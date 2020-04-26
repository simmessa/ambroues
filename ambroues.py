import asyncio
import json
from colorama import init, Fore
from datetime import datetime
from xknx import XKNX
from xknx.devices import Light

# debug
DEBUG = False #Useful for testing that KNX is sending stuff
# constants
WATCH_LOOP_SECONDS = 10

async def ambroues_init():
    # Init KNX
    await xknx.start()

    # Read Ambroues settings
    try:
        with open('ambroues.json') as json_settings:
            data = json.load(json_settings)
            print(Fore.YELLOW + "\nAmbroues started with %d zones:\n" % len(data['zones']))

            for zone in data['zones']:
                print("zone [%s] starts at %s, runs for %s minutes, on %s" % (zone['zone_name'], zone['zone_start_time'], zone['zone_duration_minutes'], zone['zone_week_days']) )
            print("----------------------------------------------")
            return data['zones']
    except IOError:
        print(Fore.RED + "ambroues.json file is required but none found! Exiting.")
        exit()

async def watch(zones, DEBUG):
    # endless loop...
    while True:
        now = datetime.now()
        # for testing only
        if DEBUG:
            now = datetime.fromisoformat('2020-04-21T09:26')
            DEBUG = False
        now_string = "%02d:%02d" % (now.hour, now.minute)
        today = now.strftime('%a')
        seconds = now.strftime('%S')
        print(Fore.GREEN + "Watching irrigation jobs: (%s:%s - %s)" % (now_string, seconds, today) )

        for zone in zones:
            # starting watering
            if zone['zone_start_time'] == now_string:
                if zone['zone_enabled'] == 'on':
                    if today.lower() in zone['zone_week_days']:
                        print("%s matches! start watering for %s minutes" % (zone['zone_name'],zone['zone_duration_minutes']) ),
                        asyncio.gather(
                            start_water(zone, xknx),
                            stop_water(zone, xknx)
                        )
                    else:
                        print("zone [%s] is disabled for today (%s), won't start watering" % (zone['zone_name'], today)),
                else:
                    print("zone [%s] is disabled, won't start watering" % (zone['zone_name']) ),
            else:
                # print ("%s doesn't match %s" %(zone['zone_start_time'], now))
                pass
        # run every WATCH_LOOP_SECONDS seconds
        await asyncio.sleep(WATCH_LOOP_SECONDS)

async def start_water(zone, xknx):
    print("watering [%s] for %s minutes (at %s) to knx address {%s}" % (zone['zone_name'], zone['zone_duration_minutes'], datetime.now(), zone['zone_knx_address']) )
    irrigation_zone = Light(xknx,
                            name=zone['zone_name'],
                            group_address_switch=zone['zone_knx_address'])
    await irrigation_zone.set_on()

async def stop_water(zone, xknx):
    await asyncio.sleep(int(zone['zone_duration_minutes']) * 60)
    irrigation_zone = Light(xknx,
                            name=zone['zone_name'],
                            group_address_switch=zone['zone_knx_address'])
    await irrigation_zone.set_off()
    print("Zone [%s] completed watering (at %s)" % (zone['zone_name'], datetime.now()) )

async def stop_xknx(xknx):
    await xknx.stop()
    print("\nKNX engine stopped.")

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
    zones = loop.run_until_complete(init_task)
    watch_task = loop.create_task(watch(zones, DEBUG))
    loop.run_until_complete(watch_task)
# catch SIGINT
except KeyboardInterrupt:
    print(Fore.RED + "\nCaught SIGINT, exiting.")
    loop.run_until_complete(stop_xknx(xknx))
    print("\nAmbroues successfully terminated")