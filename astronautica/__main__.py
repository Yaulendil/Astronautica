"""Astronautica: A MUD in Space."""

from asyncio import AbstractEventLoop, gather, get_event_loop, wait_for
from getopt import getopt, GetoptError
from sys import argv, exit


HOST: bool = False

try:
    opts, args = getopt(argv[1:], "hH", ["help", "host"])
except GetoptError as e:
    exit(e)

else:
    for k, v in opts:
        if k == "-h" or k == "--help":
            print(__doc__)
            exit(0)
        elif k == "-H" or k == "--host":
            HOST = True


from prompt_toolkit.eventloop import use_asyncio_event_loop

from interface import get_client, setup_client, setup_host


loop: AbstractEventLoop = get_event_loop()
use_asyncio_event_loop(loop)


client, commands = get_client(loop)
if HOST:
    setup_host(client, commands, loop)
else:
    setup_client(client, commands, loop)


try:
    with client as app:
        loop.run_until_complete(app.run_async().to_asyncio_future())

except (EOFError, KeyboardInterrupt):
    pass
finally:
    loop.run_until_complete(
        wait_for(
            gather(
                loop.shutdown_asyncgens(),
                *filter((lambda task: not task.done()), client.TASKS),
                loop=loop,
                return_exceptions=True
            ),
            5,
            loop=loop,
        )
    )
    loop.close()
