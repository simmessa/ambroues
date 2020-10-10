import asyncio
import json
import sys,os
from colorama import init, Fore
from datetime import datetime

from xknx import XKNX
from xknx.devices import Light

import urllib.request
import urllib.parse

import paho.mqtt.client as mqtt

# to enable debug just set env var AMBROUES_DEBUG to anything
if 'AMBROUES_DEBUG' in os.environ:
    DEBUG = True #Useful for testing that KNX is sending stuff
else:
    DEBUG = False
# constants
WATCH_LOOP_SECONDS = 10

async def ambroues_init():

    # Read Ambroues settings
    try:
        with open('ambroues.json') as json_settings:
            # load json into a dict
            settings = json.load(json_settings)
            print(json.dumps(settings, indent=2 ))

            # Init KNX
            if settings['knx_engine'] == "Yes":
                try:
                    await xknx.start()
                except:
                    ex = sys.exc_info()[0]
                    print("error: %s" % ex)
                    print(Fore.RED + "Cannot start KNX engine! Exiting.")
                    exit()

            # Init MQTT
            if settings['mqtt_engine'] == "Yes":
                try:
                    client = mqtt.Client("ambroues")  # create new instance
                    client.connect(settings['mqtt']['broker_address'])  # connect to broker
                    client.publish(settings['mqtt']['topic']+"/"+"test", "ON")  # publish
                    settings['mqtt_client'] = client
                except:
                    ex = sys.exc_info()[0]
                    print("error: %s" % ex)
                    print(Fore.RED + "Cannot start MQTT engine! Exiting.")
                    exit()

            # Telegram init is optional
            if settings['telegram_notifications'] == "Yes":
                print(Fore.CYAN + "\nTelegram notifications are on, initializing Telegram")

                try:
                    await telegram_send(settings, "Ambroues started with telegram connection")
                except:
                    print(Fore.RED + "Cannot init Telegram, have you defined the right settings in ambroues.json ?")

            print(Fore.YELLOW + "\nAmbroues started with %d zones:\n" % len(settings['zones']))
            for zone in settings['zones']:
                zone['on'] = False
                print("zone [%s] starts at %s, runs for %s minutes, on %s" % (zone['zone_name'], zone['zone_start_time'], zone['zone_duration_minutes'], zone['zone_week_days']) )
            print("----------------------------------------------")
            return settings

    except IOError as err:
        print("Error: {0}".format(err))
        print(Fore.RED + "ambroues.json file is required but none found! Exiting.")
        exit()

async def watch(settings, DEBUG): # main irrigation endless loop...
    while True:
        now = datetime.now()
        # for testing only
        # if DEBUG:
        #     now = datetime.fromisoformat('2020-04-21T09:26')
        settings['now_string'] = "%02d:%02d" % (now.hour, now.minute)
        settings['today'] = now.strftime('%a')
        settings['seconds'] = now.strftime('%S')
        print(Fore.GREEN + "Watching irrigation jobs: (%s:%s - %s)" % (settings['now_string'], settings['seconds'], settings['today']) )

        for zone in settings['zones']: # check if needs watering

            # KNX zones:
            if 'zone_knx_address' in zone and settings['knx_engine'] == 'Yes':
                irrigation_zone = Light(xknx,
                                        name=zone['zone_name'],
                                        group_address_switch=zone['zone_knx_address'])
                if DEBUG:
                    print('is on? %s' % zone['on'])

                if zone['on'] == False: # check if zone is on already
                    if (zone['zone_start_time'] == settings['now_string']) or zone['zone_enabled'] == 'force':
                        text = "%s matches!" % zone['zone_name']
                               # "watering for %s minutes" % (zone['zone_name'],zone['zone_duration_minutes'])
                        print(text),
                        asyncio.gather(
                            start_water(settings, zone, xknx),
                            stop_water(settings, zone, xknx)
                        )

                        #     else:
                        #         text = "zone [%s] is disabled for today (%s), won't start watering" % (zone['zone_name'], today)
                        #         print(text)
                        #         await telegram_send(settings, text),
                        # else:
                        #     text = "zone [%s] is disabled, won't start watering" % (zone['zone_name'])
                        #     print(text)
                        #     await telegram_send(settings, text),
                    else:
                        # nothing to do, time doesn't match zones schedule
                        pass

            if 'zone_mqtt_address' in zone and settings['mqtt_engine'] == 'Yes':
                print("spamming mqtt")
                settings['mqtt_client'].publish(settings['mqtt']['topic']+"/"+zone['zone_mqtt_address'], "ON")  # publish

        # run every WATCH_LOOP_SECONDS seconds
        await asyncio.sleep(WATCH_LOOP_SECONDS)

async def telegram_send(settings, text):
    if settings['telegram_notifications'] == "Yes":
        url = "https://api.telegram.org/bot" + settings['telegram']['api_token'] + "/sendMessage?chat_id=" + settings['telegram']['chat_id'] + "&text=" + urllib.parse.quote(text)
        f = urllib.request.urlopen(url)
        if DEBUG:
            print(f.read().decode('utf-8'))

async def start_water(settings, zone, xknx):

    if zone['zone_enabled'] == 'force' or ((zone['zone_enabled'] == 'on') and (settings['today'].lower() in zone['zone_week_days'])):
        print("enabled or today")
        irrigation_zone = Light(xknx,
                                name=zone['zone_name'],
                                group_address_switch=zone['zone_knx_address'])
        if zone['on'] == False:
            text = "watering [%s] for %s minutes (at %s) to knx address {%s}" % (zone['zone_name'], zone['zone_duration_minutes'], datetime.now(), zone['zone_knx_address'])
            print(text)
            await irrigation_zone.set_on()
            zone['on'] = irrigation_zone.state
            await telegram_send(settings, text)
    else:
        text = "zone [%s] is disabled or not planned for today (%s), won't start watering" % (zone['zone_name'], settings['today'])
        print(text)
        await telegram_send(settings, text)

async def stop_water(settings, zone, xknx):

    await asyncio.sleep(int(zone['zone_duration_minutes']) * 60)
    irrigation_zone = Light(xknx,
                            name=zone['zone_name'],
                            group_address_switch=zone['zone_knx_address'])
    if zone['on'] == True:
        await irrigation_zone.set_off()
        zone['on'] = irrigation_zone.state
        text = "Zone [%s] completed watering (at %s)" % (zone['zone_name'], datetime.now())
        print(text)
        await telegram_send(settings, text)

async def stop_zone(zone, xknx):
    irrigation_zone = Light(xknx,
                            name=zone['zone_name'],
                            group_address_switch=zone['zone_knx_address'])
    await irrigation_zone.set_off()
    print("Zone [%s] turned off because we're exiting (at %s)" % (zone['zone_name'], datetime.now()) )

async def stop_xknx(xknx):
    await xknx.stop()
    print("\nKNX engine stopped.")
    await telegram_send(settings, "Ambroues successfully terminated")

def sigint(settings):
    print(Fore.RED + "\nCaught SIGINT, exiting.")

    if settings['knx_clean_bus'].lower() == "yes" and settings['knx_engine'] == 'Yes':
        print("knx_clean_bus option is on, switching off all knx zones:\n")
        for zone in settings['zones']:
            asyncio.gather(
                stop_zone(zone, xknx)
            )
        loop.run_until_complete(stop_xknx(xknx))

    print("\nAmbroues successfully terminated")
    # exit() # is implicit

# Init colorama
init()

# KNX global bus init
try:
    with open('xknx.yaml') as f:
        print(Fore.YELLOW + "\nxknx.yaml found, configuring KNX bus")
        xknx = XKNX(config='xknx.yaml')
except IOError:
    print(Fore.RED + "\nxknx.yaml doesn't exist, Ambroues will continue with auto-discovery, but please keep in mind explicit knx configuration is recommended")
    xknx = XKNX()

# declaring event loop and doing init
loop = asyncio.get_event_loop()
init_task = loop.create_task(ambroues_init())

try:
    settings = loop.run_until_complete(init_task)
    watch_task = loop.create_task(watch(settings, DEBUG))
    loop.run_until_complete(watch_task)
# catch SIGINT
except KeyboardInterrupt:
    sigint(settings)