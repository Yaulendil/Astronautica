"""Module dedicated solely to the execution of Command Functions and the
    handling of their Returns.
"""

from asyncio import AbstractEventLoop, Task
from typing import AsyncIterator, Callable, Coroutine, Iterator, List, Sequence

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


async def handle_async(command, echo: EchoType, result):
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
            f"Error: {command}: {type(exc).__name__}: {exc}"
            if str(exc)
            else f"Error: {command}: {type(exc).__name__}"
        )


def execute_function(
    command: Sequence[str],
    echo: EchoType,
    handler: Callable,
    loop: AbstractEventLoop,
    tasks: List[Task],
) -> None:
    try:
        result = handler(command)

        if result:
            if isinstance(result, (AsyncIterator, Coroutine)):
                tasks.append(loop.create_task(handle_async(command, echo, result)))
                # echo("Asynchronous Task dispatched.")
            else:
                handle_return(echo, result)

    except Exception as exc:
        echo(
            f"Error: {command}: {type(exc).__name__}: {exc}"
            if str(exc)
            else f"Error: {command}: {type(exc).__name__}"
        )
