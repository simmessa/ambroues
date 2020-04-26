import asyncio
import json
from colorama import init, Fore
from datetime import datetime
from xknx import XKNX
from xknx.devices import Light

# debug
force = True
# constants
WATCH_LOOP_SECONDS = 10

# globals
xknx = XKNX(config='xknx.yaml')

async def ambroues_init():
    # Init KNX
    await xknx.start()

    # Init colorama
    init()

    # Read Ambroues settings
    with open('ambroues.json') as json_settings:
        data = json.load(json_settings)
        print(Fore.YELLOW + "\nAmbroues started with %d zones:\n" % len(data['zones']))

        for zone in data['zones']:
            print("zone [%s] starts at %s, runs for %s minutes, on %s" % (zone['zone_name'], zone['zone_start_time'], zone['zone_duration_minutes'], zone['zone_week_days']) )
        print("----------------------------------------------")
        return data['zones']

async def watch(zones, force):
    # endless loop...
    while True:
        now = datetime.now()
        # for testing only
        if force:
            now = datetime.fromisoformat('2020-04-21T09:26:00')
            force = False
        now = "%02d:%02d:%02d" % (now.hour, now.minute, now.second)
        print(Fore.GREEN + "Watching irrigation jobs: (%s)" % now)

        for zone in zones:
            # starting watering
            if zone['zone_start_time'] == now:
                if zone['zone_enabled'] == 'on':
                    print("%s matches! start watering for %s minutes" % (zone['zone_name'],zone['zone_duration_minutes']) ),
                    asyncio.gather(
                        start_water(zone, xknx),
                        stop_water(zone, xknx)
                    )
                else:
                    print("zone [%s] is disabled, won't start watering" % (zone['zone_name']) ),
            else:
                # print ("%s doesn't match %s" %(zone['zone_start_time'], now))
                pass
        # run every WATCH_LOOP_SECONDS seconds
        await asyncio.sleep(WATCH_LOOP_SECONDS)

async def start_water(zone, xknx):
    print("watering [%s] for %s minutes (at %s) to knx address %s" % (zone['zone_name'], zone['zone_duration_minutes'], datetime.now(), zone['zone_knx_address']) )
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

# declaring event loop and doing init
loop = asyncio.get_event_loop()
init_task = loop.create_task(ambroues_init())

try:
    zones = loop.run_until_complete(init_task)
    watch_task = loop.create_task(watch(zones, force))
    loop.run_until_complete(watch_task)
# catch SIGINT
except KeyboardInterrupt:
    print(Fore.RED + "\nCaught SIGINT, exiting.")
    loop.run_until_complete(stop_xknx(xknx))
    print("\nAmbroues successfully terminated")