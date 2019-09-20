"""Astronautica: A MUD in Space."""

import asyncio
from getopt import getopt
from sys import argv, exit

from prompt_toolkit.eventloop import use_asyncio_event_loop

from interface import get_client, setup_client, setup_host


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
