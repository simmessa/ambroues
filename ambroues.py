import asyncio
import json
import time
from datetime import datetime
from xknx import XKNX
from xknx.devices import Light


async def init():
    """Init KNX"""
    xknx = XKNX(config='xknx.yaml')
    await xknx.start()

    """Read settings"""
    with open('ambroues.json') as json_settings:
        data = json.load(json_settings)
        # print("Ambroues started with settings:")
        # print(json.dumps(data, indent=4))

        for zone in data['zones']:
            print("%s starts at %s" % (zone['zone_name'],zone['zone_start_time']) )
            # irrigation_zone = Light(xknx, name=,
            #           group_address_switch='2/0/20')
        return data['zones']

    # await light.set_on()
    # await asyncio.sleep(2)
    # await light.set_off()
    # await xknx.stop()

async def watch(zones):
    while True:
        # now = datetime.now()
        now = datetime.fromisoformat('2020-04-21T17:38:00')
        now = str(now.hour)+":"+str(now.minute)
        print("Watching irrigation jobs: (%s)" % now)

        for zone in zones:
            # starting watering
            if zone['zone_start_time'] == now:
                print("%s matches! start watering for %s minutes" % (zone['zone_name'],zone['zone_duration_minutes']) )
                await water(zone)
            else:
                print ("%s doesn't match %s" %(zone['zone_start_time'], now))
            # stopping watering
        await asyncio.sleep(1)

async def water(zone):
    print("watering for %s (%s)" % (zone['zone_duration_minutes'], time.time()) )
    await asyncio.sleep(int(zone['zone_duration_minutes'])*10)


def stop():
    watch_task.cancel()

loop = asyncio.get_event_loop()
#stop after X seconds
# loop.call_later(3, stop)
init_task = loop.create_task(init())

try:
    zones = loop.run_until_complete(init_task)
    print(json.dumps(zones, indent=4))

    watch_task = loop.create_task(watch(zones))
    loop.run_until_complete(watch_task)
except asyncio.CancelledError:
    pass

# pylint: disable=invalid-name


    """Connect to KNX/IP bus, switch on light, wait 2 seconds and switch it off again."""

    # xknx = XKNX(config='xknx.yaml')
    #
    # await xknx.start()
    #
    # for device in xknx.devices:
    #     print(device)
    #
    # light = Light(xknx,
    #               name='StairsLed',
    #               group_address_switch='2/0/20')
    # await light.set_on()
    # await asyncio.sleep(2)
    # await light.set_off()
    # await xknx.stop()
