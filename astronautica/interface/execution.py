"""Module dedicated solely to the execution of Command Functions and the
    handling of their Returns.
"""

from asyncio import AbstractEventLoop, Task
from typing import AsyncIterator, Coroutine, Iterator, List, Sequence

from .commands import CommandNotFound, CommandRoot
from .etc import EchoType, T


def handle_return(echo: EchoType, result):
    """We have received either an Iterator or the result of a Command Function.
        If it is an Iterator or a Sequence, loop through it and Echo each
        element to the Output. Otherwise, simply Echo a String of it.
    """
    if isinstance(result, (Iterator, Sequence)) and not isinstance(result, str):
        for each in result:
            if each is not None:
                echo(str(each))

    else:
        echo(str(result))


async def handle_async(line, echo: EchoType, result):
    """We have received...something. So long as it is a Coroutine, replace it
        with the result of awaiting it. If it is an Asynchronous Iterator,
        loop through it and Echo each element. If it is anything else, simply
        forward it to the Synchronous Return Handler.
    """
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
            f"Error: {T.bold(line)}: {type(exc).__name__!r}\n\r    {exc}"
            if str(exc)
            else f"Error: {T.bold(line)}: {type(exc).__name__!r}"
        )


def execute_function(
    line: str,
    echo: EchoType,
    handler: CommandRoot,
    loop: AbstractEventLoop,
    tasks: List[Task],
    set_job,
) -> None:
    """Find the Command Object and Tokens represented by the input line, and
        handle the process of either retrieving its output, or dispatching a
        Task to do so.
    """
    tokens = handler.split(line)
    command, args = handler.get_command(tokens)
    try:
        if command is None:
            raise CommandNotFound(f"Command {tokens[0].upper()!r} not found.")

        handler.client.cmd_hide()

        if command.is_async:
            # This Command Function is Asynchronous. Dispatch a Task to run
            #   and manage it.
            task = loop.create_task(handle_async(line, echo, command(args)))
            tasks.append(task)

            if not command.dispatch_task:
                set_job(task)

            # if command.dispatch_task:
            #     # This Command is meant to run in the background. Return
            #     #   control to the User now.
            #     handler.client.cmd_show()
            # else:
            #     # This Command, while Asynchronous, is meant to block
            #     #   further User Input. Register a Callback to return
            #     #   control after it is done.
            #     task.add_done_callback(handler.client.cmd_show)

            # echo("Asynchronous Task dispatched.")
        else:
            # This Command Function is Synchronous. We have no choice but to
            #   accept the blocking.
            handle_return(echo, command(args))
            # handler.client.cmd_show()

    except Exception as exc:
        echo(
            f"Error: {T.bold(line)}: {type(exc).__name__!r}\n\r    {exc}"
            if str(exc)
            else f"Error: {T.bold(line)}: {type(exc).__name__!r}"
        )
        # handler.client.cmd_show()
