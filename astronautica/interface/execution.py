"""Module dedicated solely to the execution of Command Functions and the
    handling of their Returns.
"""

from typing import AsyncIterator, Callable, Coroutine, Iterator, Sequence

from prompt_toolkit.formatted_text import FormattedText


async def execute_function(
    handler: Callable, echo: Callable, command: Sequence[str]
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
            while isinstance(result, Coroutine):
                result = await result

            if isinstance(result, AsyncIterator):
                async for each in result:
                    if each is not None:
                        echo(each)

            elif isinstance(result, (Iterator, Sequence)) and not isinstance(
                result, FormattedText
            ):
                for each in result:
                    if each is not None:
                        echo(each)

            else:
                echo(result)
