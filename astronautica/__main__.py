import asyncio

from prompt_toolkit.eventloop import use_asyncio_event_loop

from interface import get_client


loop = asyncio.get_event_loop()
use_asyncio_event_loop(loop)


if __name__ == "__main__":
    client, commands = get_client(loop)

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
