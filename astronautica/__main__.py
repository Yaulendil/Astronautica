"""Astronautica: A MUD in Space."""

from asyncio import AbstractEventLoop, gather, get_event_loop, wait_for
from getopt import getopt
from sys import argv, exit

from config import cfg


HOST: bool = False

try:
    opts, args = getopt(argv[1:], "hH", ["config=", "data=", "help", "host"])

    for k, v in opts:
        if k == "--config":
            cfg.load(v)
        elif k == "--data":
            cfg["data/directory"] = v
        elif k == "-h" or k == "--help":
            print(__doc__)
            exit(0)
        elif k == "-H" or k == "--host":
            HOST = True

except Exception as e:
    exit(e)


from prompt_toolkit.eventloop import use_asyncio_event_loop

from interface import get_client, setup_client, setup_host


loop: AbstractEventLoop = get_event_loop()
use_asyncio_event_loop(loop)


cli, commands = get_client(loop)
if HOST:
    cleanup = setup_host(cli, commands, loop)
else:
    cleanup = setup_client(cli, commands, loop)


try:
    with cli as app:
        loop.run_until_complete(app.run_async().to_asyncio_future())

except (EOFError, KeyboardInterrupt):
    pass

finally:
    try:
        if cleanup:
            loop.run_until_complete(cleanup())

        loop.run_until_complete(
            wait_for(
                gather(
                    loop.shutdown_asyncgens(),
                    *filter((lambda task: not task.done()), cli.TASKS),
                    loop=loop,
                    return_exceptions=True
                ),
                5,
                loop=loop,
            )
        )
        loop.close()
    except KeyboardInterrupt:
        print()
