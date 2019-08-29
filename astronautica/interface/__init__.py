"""Interface Package: Command line Client and all integrations with Engine."""

from typing import Tuple

from .client import Client
from .commands import CommandRoot


def get_client() -> Tuple[Client, CommandRoot]:
    cmd_root = CommandRoot()
    interface_client = Client(command_handler=cmd_root.run)

    @cmd_root("asdf")
    def asdf(*words):
        yield from words

    @asdf.sub("qwert")
    def qwert(*words):
        for word in words:
            yield f"QWERT {word}"

    return interface_client, cmd_root
