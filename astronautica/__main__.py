"""Astronautica: A MUD in Space."""

import asyncio
from getopt import getopt
from sys import argv, exit

from prompt_toolkit.eventloop import use_asyncio_event_loop

from interface import get_client, setup


loop = asyncio.get_event_loop()
use_asyncio_event_loop(loop)

opts, args = getopt(argv[1:], "hH", ["help", "host"])


HOST = False


for k, v in opts:
    if k == "-h" or k == "--help":
        print(__doc__)
        exit(0)
    elif k == "-H" or k == "--host":
        HOST = True


if __name__ == "__main__":
    client, commands = get_client(loop)
    setup(client, commands, loop, HOST)

    try:
        with client as app:
            loop.run_until_complete(app.run_async().to_asyncio_future())
    finally:
        loop.run_until_complete(
            asyncio.wait_for(
                asyncio.gather(
                    *filter((lambda task: not task.done()), client.TASKS),
                    loop=loop,
                    return_exceptions=True
                ),
                5,
                loop=loop,
            )
        )
        loop.close()
