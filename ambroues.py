import asyncio
import json
import sys,os
from colorama import init, Fore
from datetime import datetime

from xknx import XKNX
from xknx.devices import Light
# from xknx import io

import urllib.request
import urllib.parse

import paho.mqtt.client as mqtt

from yaml import load, dump

from flask import Flask, jsonify

# to enable debug just set env var AMBROUES_DEBUG to anything
if 'AMBROUES_DEBUG' in os.environ:
    DEBUG = True #Useful for testing that KNX is sending stuff
else:
    DEBUG = False
# constants
WATCH_LOOP_SECONDS = 10

# [
#     {
#         "type": "error",
#         "date": "07/21/2021 - 17:42:49",
#         "msg" : "somelog"
#     }
# ]


def log(string, code=""):
    print(code + string)
    log_type = "info"
    if code == Fore.RED:
        log_type = "error"
    log_date = datetime.now().strftime("%m/%d/%Y - %H:%M:%S")
    log_msg = string.strip("\n")
    # log = json.loads(log)
    log = {"type":log_type, "date":log_date, "msg":log_msg}
    return log

#WTF
async def api_call(route):
    print(route)

def init_api(app, settings):
    @app.route("/")
    def index():
        loop.run_until_complete(api_call("/"))
        out_file = open("./dist/index.html", "r")
        out = out_file.read()
        return out
    @app.route("/logs")
    def logs():
        loop.run_until_complete(api_call("/logs"))
        return jsonify(settings['logs'])


def init_mqtt(settings):
    if settings['mqtt']['enabled'] == True:
        try:
            client = mqtt.Client("ambroues")  # create new instance
            client.connect(settings['mqtt']['broker_address'], settings['mqtt']['broker_port']) # connect to broker
            client.publish('ambroues'+"/"+"start", "started at %s" % datetime.now())  # publish
            settings['mqtt_client'] = client #eheh manipulate the object in memory...
            settings['logs'] += log("Successfully connected to MQTT broker on %s \n" % settings['mqtt']['broker_address'], Fore.GREEN)
        except:
            ex = sys.exc_info()[0]
            settings['logs'] += log("error: %s" % ex, Fore.RED)
            settings['logs'] += log("Cannot start MQTT engine! Exiting.", Fore.RED)
            exit()

app = Flask(__name__)

async def ambroues_init(app):
    # Read Ambroues settings
    try:
        # Load settings
        with open('ambroues-settings.yaml') as yaml_settings:
            # load conifg yaml into a dict
            try:
                from yaml import CLoader as Loader, CDumper as Dumper
            except ImportError:
                from yaml import Loader, Dumper
            settings = load(yaml_settings, Loader=Loader)
            # init logs
            settings['logs'] = []
            settings['logs'].append(log("Welcome to Ambroues!\n"))

            settings['logs'].append(log(dump(settings, Dumper=Dumper, indent=2)))

            # init xknx if required            
            if settings['knx']['enabled'] == True:
                settings['logs'].append(log("\nKNX support enabled, configuring KNX bus", Fore.YELLOW))

                try:
                    knx = settings['knx']
                    if os.path.isfile(knx['filename']):                    
                        settings['logs'].append(log("\nKNX configuration found, applying...\n", Fore.GREEN))
                        settings['logs'].append(log(dump(knx, Dumper=Dumper)))
                        xknx_config = knx['filename']
                        try:
                            xknx = XKNX(config=xknx_config)
                            await xknx.start()
                            settings['logs'].append(log("Successfully connected to KNX Bus", Fore.GREEN))
                        except:
                            ex = sys.exc_info()[0]
                            settings['logs'].append(log("error: %s" % ex, Fore.RED))
                            settings['logs'].append(log("Cannot start KNX engine! Exiting.", Fore.RED))
                            exit()
                    else:
                        try:
                            settings['logs'].append(log("xknx filename doesn't exist in ambroues-settings.yaml, Ambroues will continue with auto-discovery.\nKeep in mind this can result in error and explicit knx configuration is always recommended", Fore.YELLOW))
                            xknx = XKNX()
                            await xknx.start()
                            settings['logs'].append(log("Successfully connected to KNX Bus", Fore.GREEN))
                        except:
                            ex = sys.exc_info()[0]
                            settings['logs'].append(log("error: %s" % ex, Fore.RED))
                            settings['logs'].append(log("Cannot start KNX engine! Exiting."))
                            exit()
                except:
                    settings['logs'].append(log("Couldn't init KNX\n", Fore.RED))

            else:
                settings['logs'].append(log("KNX support disabled, KNX init skipped", Fore.YELLOW+"\n"))

            # Init MQTT if required
            if settings['mqtt']['enabled'] == True:
                init_mqtt(settings)

            # Telegram init if required (just a startup notification)
            if settings['telegram']['notifications'] == True:
                settings['logs'].append(log("\nTelegram notifications are on, initializing Telegram", Fore.CYAN))

                try:
                    await telegram_send(settings, "Ambroues started with telegram connection at %s" % datetime.now())
                except:
                    settings['logs'].append(log("Cannot init Telegram, have you defined the right settings in ambroues.json ?", Fore.RED))

            # Init API if required
            if settings['api']['enabled'] == True:
                init_api(app, settings)
            else:
                app = None

        with open('ambroues-tasks.json') as json_tasks:
            # load json into a dict
            tasks = json.load(json_tasks)
            settings['logs'].append(log(json.dumps(tasks, indent=2 )))

            settings['logs'].append(log("\nAmbroues started with %d zones:\n" % len(tasks['zones']), Fore.YELLOW))
            for zone in tasks['zones']:
                zone['on'] = False
                settings['logs'].append(log("zone [%s] starts at %s, runs for %s minutes, on %s" % (zone['zone_name'], zone['zone_start_time'], zone['zone_duration_minutes'], zone['zone_week_days']) ))
            settings['logs'].append(log("----------------------------------------------"))
            context = (settings, tasks)
            return context

    except IOError as err:
        settings['logs'].append(log("Error: {0}".format(err), Fore.RED))
        settings['logs'].append(log("ambroues-tasks.json file is required but none found! Exiting."))
        exit()

async def watch(settings, tasks, DEBUG): # main irrigation endless loop...
    while True:
        now = datetime.now()
        # for testing only
        # if DEBUG:
        #     now = datetime.fromisoformat('2020-04-21T09:26')
        tasks['now_string'] = "%02d:%02d" % (now.hour, now.minute)
        tasks['today'] = now.strftime('%a')
        tasks['seconds'] = now.strftime('%S')
        settings['logs'] += log("Watching irrigation jobs: (%s:%s - %s)" % (tasks['now_string'], tasks['seconds'], tasks['today']), Fore.GREEN)

        for zone in tasks['zones']: # check if needs watering

            if DEBUG:
                settings['logs'] += log('%s is on? %s' % (zone['zone_name'], zone['on']))

            if zone['on'] == False: # check if zone is on already
                if (zone['zone_start_time'] == tasks['now_string']) or zone['zone_enabled'] == 'force':
                    text = "%s matches!" % zone['zone_name']
                           # "watering for %s minutes" % (zone['zone_name'],zone['zone_duration_minutes'])
                    settings['logs'] += log(text),

                    asyncio.gather(
                        start_water(settings, tasks, zone),
                        stop_water(settings, tasks, zone)
                    )

                    #     else:
                    #         text = "zone [%s] is disabled for today (%s), won't start watering" % (zone['zone_name'], today)
                    #         print(text)
                    #         await telegram_send(tasks, text),
                    # else:
                    #     text = "zone [%s] is disabled, won't start watering" % (zone['zone_name'])
                    #     print(text)
                    #     await telegram_send(tasks, text),
                else:
                    # nothing to do, time doesn't match zones schedule
                    pass

        # run every WATCH_LOOP_SECONDS seconds
        await asyncio.sleep(WATCH_LOOP_SECONDS)

async def telegram_send(settings, text):

    if settings['telegram']['notifications'] == True:
        url = "https://api.telegram.org/bot" + settings['telegram']['api_token'] + "/sendMessage?chat_id=" + settings['telegram']['chat_id'] + "&text=" + urllib.parse.quote(text)
        f = urllib.request.urlopen(url)
        if DEBUG:
            settings['logs'] += log(f.read().decode('utf-8'))

async def start_water(settings, tasks, zone):

    if zone['zone_enabled'] == 'force' or ((zone['zone_enabled'] == 'on') and (tasks['today'].lower() in zone['zone_week_days'])):
        settings['logs'] += log("%s enabled for today" % zone['zone_name'])

        # hack to avoid infinite watering: force > on
        if zone['zone_enabled'] == 'force':
            zone['zone_enabled'] = 'on'

        # is a KNX zone:
        if 'zone_knx_address' in zone and settings['knx']['enabled'] == True:
            irrigation_zone = Light(xknx,
                                    name=zone['zone_name'],
                                    group_address_switch=zone['zone_knx_address'])

            text = "watering [%s] for %s minutes (at %s) to knx address {%s}" % (zone['zone_name'], zone['zone_duration_minutes'], datetime.now(), zone['zone_knx_address'])
            settings['logs'] += log(text)
            await irrigation_zone.set_on()
            zone['on'] = irrigation_zone.state
            await telegram_send(settings, text)

        # is an MQTT zone:
        if 'zone_mqtt_address' in zone and settings['mqtt']['enabled'] == True:
            init_mqtt(settings)
            text = "watering [%s] for %s minutes (at %s) to mqtt address {%s}" % (zone['zone_name'], zone['zone_duration_minutes'], datetime.now(), zone['zone_mqtt_address'])
            settings['logs'] += log(text)
            mqtt_topic = zone['zone_mqtt_address'].split(':')[0]
            mqtt_address = zone['zone_mqtt_address'].split(':')[1]
            settings['mqtt_client'].publish(mqtt_topic, mqtt_address) # publish msg TOPIC: ADDRESS
            zone['on'] = True # we just did that
            await telegram_send(settings, text)

    else:
        text = "zone [%s] is disabled or not planned for today (%s), won't start watering" % (zone['zone_name'], settings['today'])
        settings['logs'] += log(text)
        await telegram_send(settings, text)

async def stop_water(settings, tasks, zone):

    # fire and know when to stop this
    await asyncio.sleep(int(zone['zone_duration_minutes']) * 60)

    # is a KNX zone:
    if 'zone_knx_address' in zone and settings['knx']['enabled'] == True:

        irrigation_zone = Light(xknx,
                                name=zone['zone_name'],
                                group_address_switch=zone['zone_knx_address'])
        if zone['on'] == True:
            await irrigation_zone.set_off()
            zone['on'] = irrigation_zone.state
            text = "Zone [%s] completed watering (at %s)" % (zone['zone_name'], datetime.now())
            settings['logs'] += log(text)
            await telegram_send(settings, text)


    # is an MQTT zone:
    if 'zone_mqtt_address' in zone and settings['mqtt']['enabled'] == True:

        if zone['on'] == True:
            init_mqtt(settings)
            mqtt_topic = zone['zone_mqtt_address'].split(':')[0]
            mqtt_address = zone['zone_mqtt_address'].split(':')[1]
            settings['mqtt_client'].publish(mqtt_topic, 0) # publish msg TOPIC: 0
            text = "Zone [%s] completed watering (at %s)" % (zone['zone_name'], datetime.now())
            settings['logs'] += log(text)
            zone['on'] = False # we just did that
            await telegram_send(settings, text)

async def stop_knx_zone(zone, xknx):
    irrigation_zone = Light(xknx,
                            name=zone['zone_name'],
                            group_address_switch=zone['zone_knx_address'])
    await irrigation_zone.set_off()
    settings['logs'] += log("Zone [%s] turned off because we're exiting (at %s)" % (zone['zone_name'], datetime.now()) )

def stop_mqtt_zone(zone, mqtt_client):
    init_mqtt(settings)
    mqtt_topic = zone['zone_mqtt_address'].split(':')[0]
    mqtt_address = zone['zone_mqtt_address'].split(':')[1]
    mqtt_client.publish(mqtt_topic, 0) # publish msg TOPIC: 0
    settings['logs'] += log("Zone [%s] turned off because we're exiting (at %s)" % (zone['zone_name'], datetime.now()) )

async def stop_xknx(xknx):
    await xknx.stop()
    settings['logs'] += log("\nKNX engine stopped.")
    await telegram_send(settings, "Ambroues successfully stopped xknx")

def sigint(settings, tasks):
    settings['logs'] += log("\nCaught SIGINT, exiting.", Fore.RED)

    if settings['knx']['clean_bus'] and settings['knx']['enabled']:
        settings['logs'] += log("knx_clean_bus option is on, switching off all knx zones:\n")
        # stop knx zones
        for zone in tasks['zones']:
            if zone['zone_knx_address'] != "":
                asyncio.gather(
                    stop_knx_zone(zone, xknx)
                )
        # stop xknx
        loop.run_until_complete(stop_xknx(xknx))

    settings['logs'] += log("resetting all mqtt zones...")
    for zone in tasks['zones']:
        try:
            if zone['zone_mqtt_address'] != "":
                stop_mqtt_zone(zone, settings['mqtt_client'])
        except:
            pass
    message = "Ambroues successfully terminated via SIGINT"
    settings['logs'] += log("\n" + message)
    loop.run_until_complete(telegram_send(settings, message))

    # exit() # is implicit

# Init colorama
init()

# declaring event loop and doing init
loop = asyncio.get_event_loop()
init_task = loop.create_task(ambroues_init(app))

try:
    settings, tasks = loop.run_until_complete(init_task)
    watch_task = loop.create_task(watch(settings, tasks, DEBUG))
    app.run(host="0.0.0.0", port=8000, debug=False, use_reloader=False)
    loop.run_until_complete(watch_task)

# catch SIGINT
except KeyboardInterrupt:
    sigint(settings, tasks)