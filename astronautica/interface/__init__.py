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
    P.output_line = cli.print

    @cmd
    def test(*text: str, list_: list = None, dict_: dict = None):
        """Test Command: Immediately print back all arguments provided."""
        yield from text
        if list_:
            yield repr(list_)
        if dict_:
            yield repr(dict_)

    return cli, cmd
