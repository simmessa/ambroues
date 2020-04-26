import asyncio
import json
import time
from datetime import datetime
from xknx import XKNX
from xknx.devices import Light

# debug
force = True
# constants
WATCH_LOOP_SECONDS = 10

# globals
xknx = XKNX(config='xknx.yaml')

async def init():
    """Init KNX"""
    await xknx.start()

    """Read settings"""
    with open('ambroues.json') as json_settings:
        data = json.load(json_settings)
        # print("Ambroues started with settings:")
        # print(json.dumps(data, indent=4))

        for zone in data['zones']:
            print("%s starts at %s" % (zone['zone_name'],zone['zone_start_time']) )
        return data['zones']

async def watch(zones, force):
    while True:
        now = datetime.now()
        if force:
            now = datetime.fromisoformat('2020-04-21T09:26:00')
            force = False
        now = "%02d:%02d:%02d" % (now.hour, now.minute, now.second)
        print("Watching irrigation jobs: (%s)" % now)

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

async def test_xknx(xknx):
    light = Light(xknx,
                  name='StairsLed',
                  group_address_switch='2/0/1')
    await light.set_on()
    await asyncio.sleep(2)
    await light.set_off()
    await xknx.stop()

async def stop_xknx(xknx):
    await xknx.stop()
    print("\nKNX engine stopped.")

# def stop():
#     watch_task.cancel()

loop = asyncio.get_event_loop()
init_task = loop.create_task(init())

try:
    zones = loop.run_until_complete(init_task)
    # print(json.dumps(zones, indent=4))
    watch_task = loop.create_task(watch(zones, force))
    loop.run_until_complete(watch_task)

except KeyboardInterrupt:
    print("\nCaught SIGINT, exiting.")
    loop.run_until_complete(stop_xknx(xknx))
    print("\nAmbroues successfully terminated")