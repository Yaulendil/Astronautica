"""Module dedicated solely to the execution of Command Functions and the
    handling of their Returns.
"""

from asyncio import AbstractEventLoop, Task
from typing import AsyncIterator, Callable, Coroutine, Iterator, List, Sequence

from prompt_toolkit.formatted_text import FormattedText


def handle_return(echo, result):
    if isinstance(result, (Iterator, Sequence)) and not isinstance(
        result, FormattedText
    ):
        for each in result:
            if each is not None:
                echo(each)

    else:
        echo(result)


async def handle_async(echo, result):
    try:
        while isinstance(result, Coroutine):
            result = await result

    except Exception as exc:
        echo(
            f"Error: {type(exc).__name__}: {exc}"
            if str(exc)
            else f"Error: {type(exc).__name__}"
        )

    else:
        if isinstance(result, AsyncIterator):
            async for each in result:
                if each is not None:
                    echo(each)

        else:
            handle_return(echo, result)


def execute_function(
    command: Sequence[str],
    echo: Callable,
    handler: Callable,
    loop: AbstractEventLoop,
    tasks: List[Task],
) -> None:
    try:
        result = handler(command)

    except Exception as exc:
        echo(
            f"Error: {type(exc).__name__}: {exc}"
            if str(exc)
            else f"Error: {type(exc).__name__}"
        )

    else:
        if result:
            if isinstance(result, (AsyncIterator, Coroutine)):
                tasks.append(loop.create_task(handle_async(echo, result)))
            else:
                handle_return(echo, result)
