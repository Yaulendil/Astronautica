"""Interface Package: Command line Client and all integrations with Engine."""

from asyncio import AbstractEventLoop, create_task, sleep
from time import sleep as sleep2
from typing import Tuple

from ezipc.util import P

from .client import Client
from .commands import CommandRoot


def get_client(loop) -> Tuple[Client, CommandRoot]:
    cmd = CommandRoot()
    interface_client = Client(loop, command_handler=cmd.run)

    @cmd
    def asdf(*words):
        sleep2(3)
        yield from words

    @asdf.sub
    async def qwert(*words):
        for word in words:
            await sleep(1)
            yield f"QWERT {word}"

    return interface_client, cmd


def setup(cli: Client, cmd: CommandRoot, loop: AbstractEventLoop, host: bool):
    P.output_line = cli.echo

    if host:
        from ezipc.server import Server

        ...
    else:
        from ezipc.client import Client as ClientIPC

        @cmd
        async def connect(addr_port: str):
            addr, port = addr_port.split(":")
            ipc = ClientIPC(addr, int(port))

            ...
