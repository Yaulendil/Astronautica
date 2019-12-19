"""Interface Package: Command line Client and all integrations with Engine."""

from asyncio import AbstractEventLoop  # , sleep
from typing import List, Tuple

from ezipc.util import P

from .client import setup_client
from .commands import CommandRoot
from .etc import T
from .server import setup_host
from .tui import Interface


def get_client(loop: AbstractEventLoop) -> Tuple[Interface, CommandRoot]:
    cmd = CommandRoot()
    cli = Interface(loop, command_handler=cmd)
    P.output_line = cli.print

    @cmd
    def test(
        *text: str,
        x: bool = False,
        y: str = "zxcv",
        z: int = 1337,
        bool_: bool = False,
        list_: List[int] = None,
        dict_: dict = None,
    ):
        """Test Command: Immediately print back all arguments provided."""
        yield from text
        yield f"{x=!r:>5}, {y=!r}, {z=!r}, {bool_=!r:>5}"
        if list_:
            yield repr(list_)
        if dict_:
            yield repr(dict_)

    @test.sub
    def science(num: int):
        return "A" * num

    return cli, cmd
