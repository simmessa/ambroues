import asyncio
import json
import time
from xknx import XKNX
from xknx.devices import Light


async def init():
    """Read settings"""
    with open('ambroues.json') as json_settings:
        data = json.load(json_settings)
        print("Ambroues started with settings:")
        print(json.dumps(data, indent=4))

async def watch():
    while True:
        seconds = time.time()
        print("WATERING!(%d)" % seconds)
        await asyncio.sleep(1)

def stop():
    watch_task.cancel()

loop = asyncio.get_event_loop()
#run only X times
loop.call_later(2, stop)
init_task = loop.create_task(init())
watch_task = loop.create_task(watch())

try:
    loop.run_until_complete(init_task)
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
