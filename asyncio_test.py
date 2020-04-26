import asyncio

async def periodic(test, loop):
    while True:
        print('periodic')
        await asyncio.sleep(1)
        if test == True:
            loop.call_soon(boom,"boh")
            test = False

def boom(boh):
    print("BOOM!")

def stop():
    task.cancel()

test = True
loop = asyncio.get_event_loop()
task = loop.create_task(periodic(test, loop))

try:
    loop.run_until_complete(task)
except asyncio.CancelledError:
    pass