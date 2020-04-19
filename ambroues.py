import asyncio
import json
import schedule
from xknx import XKNX
from xknx.devices import Light

async def main():

    """Read settings"""
    with open('ambroues.json') as json_settings:
        data = json.load(json_settings)
        print("Ambroues started with settings:")
        print(json.dumps(data, indent=4))

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


# pylint: disable=invalid-name

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.close()
