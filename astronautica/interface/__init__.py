"""Interface Package: Command line Client and all integrations with Engine."""
from asyncio import AbstractEventLoop  # , sleep
from typing import Tuple

from ezipc.util import P

from .client import setup_client
from .commands import CommandRoot
from .etc import T
from .server import setup_host
from .tui import Interface


def get_client(loop: AbstractEventLoop) -> Tuple[Interface, CommandRoot]:
    cmd = CommandRoot()
    cli = Interface(loop, command_handler=cmd)
    cmd.set_client(cli)
    P.output_line = cli.print

    # @cmd
    # async def asdf(*words, no_echo: bool = False, wait: float = 3):
    #     """Test command.
    #
    #     Does nothing interesting.
    #     """
    #     await sleep(wait)
    #     if not no_echo:
    #         return words
    #
    # @asdf.sub(task=True)
    # async def qwert(*words):
    #     for word in words:
    #         await sleep(1)
    #         yield f"QWERT {word}"
    #
    # @asdf.sub
    # async def qwerty(*words, zxcv: int = 5, b: bool = "z", f: str = "", g=None):
    #     return (f" {type(x).__name__!r:<12} : {x!r}" for x in (words, zxcv, b, f, g))
    #
    # @cmd
    # async def qwertz(text: str, mult: int = 1):
    #     return text * mult
    #
    # @cmd
    # def test(*text):
    #     return map(repr, text)

    return cli, cmd
