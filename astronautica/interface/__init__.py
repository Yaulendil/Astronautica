"""Interface Package: Command line Client and all integrations with Engine."""

from asyncio import sleep
from time import sleep as sleep2
from typing import Tuple

from .client import Client
from .commands import CommandRoot


def get_client(loop) -> Tuple[Client, CommandRoot]:
    cmd_root = CommandRoot()
    interface_client = Client(loop, command_handler=cmd_root.run)

    @cmd_root("asdf")
    def asdf(*words):
        sleep2(3)
        yield from words

    @asdf.sub("qwert")
    async def qwert(*words):
        for word in words:
            await sleep(1)
            yield f"QWERT {word}"

    return interface_client, cmd_root
