"""Module dedicated solely to the execution of Command Functions and the
    handling of their Returns.
"""

from asyncio import AbstractEventLoop, Task
from typing import AsyncIterator, Coroutine, Iterator, List, Sequence

from .commands import CommandNotFound, CommandRoot
from .etc import EchoType


def handle_return(echo: EchoType, result):
    if isinstance(result, (Iterator, Sequence)) and not isinstance(
        result, str
    ):
        for each in result:
            if each is not None:
                echo(str(each))

    else:
        echo(str(result))


async def handle_async(tokens: Sequence[str], echo: EchoType, result):
    try:
        while isinstance(result, Coroutine):
            result = await result

        if isinstance(result, AsyncIterator):
            async for each in result:
                if each is not None:
                    echo(each)

        elif result is not None:
            handle_return(echo, result)

    except Exception as exc:
        echo(
            f"Error: {' '.join(tokens)}: {type(exc).__name__}: {exc}"
            if str(exc)
            else f"Error: {' '.join(tokens)}: {type(exc).__name__}"
        )


def execute_function(
    line: str,
    echo: EchoType,
    handler: CommandRoot,
    loop: AbstractEventLoop,
    tasks: List[Task],
) -> None:
    command, tokens = handler.get_command(line)
    try:
        if command is None:
            raise CommandNotFound(f"Command '{tokens[0].upper()}' not found.")

        handler.client.cmd_hide()
        result = command(tokens)

        if result:
            if isinstance(result, (AsyncIterator, Coroutine)):
                task = loop.create_task(handle_async(tokens, echo, result))

                if command.no_dispatch:
                    task.add_done_callback(handler.client.cmd_show)
                else:
                    handler.client.cmd_show()

                tasks.append(task)
                echo("Asynchronous Task dispatched.")
            else:
                handle_return(echo, result)
                handler.client.cmd_show()

    except Exception as exc:
        echo(
            f"Error: {' '.join(tokens)}: {type(exc).__name__}: {exc}"
            if str(exc)
            else f"Error: {' '.join(tokens)}: {type(exc).__name__}"
        )
        handler.client.cmd_show()
