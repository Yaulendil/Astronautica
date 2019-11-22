"""Interface Package: Command line Client and all integrations with Engine."""
from asyncio import AbstractEventLoop, sleep
from time import sleep as sleep2
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
    P.output_line = cli.echo

    @cmd
    def asdf(*words):
        """Test command.

        Does nothing interesting.
        """
        sleep2(3)
        yield from words

    @asdf.sub(task=True)
    async def qwert(*words):
        for word in words:
            await sleep(1)
            yield f"QWERT {word}"

    @asdf.sub
    async def qwerty(*words, zxcv: int = 5, b: bool = "z", f: str = "", g=None):
        return (f" {type(x).__name__!r:<12} : {x!r}" for x in (words, zxcv, b, f, g))

    @asdf.sub
    async def qwertz(*words):
        for word in words:
            await sleep(1)
            yield f"QWERT {word}"

    @cmd
    def test(*text):
        yield from map(repr, text)

    return cli, cmd
