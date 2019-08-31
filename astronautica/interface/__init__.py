"""Interface Package: Command line Client and all integrations with Engine."""

from asyncio import AbstractEventLoop, create_task, sleep, CancelledError
from re import compile
from time import sleep as sleep2
from typing import Tuple

from ezipc.util import P, set_colors

from .client import Client
from .commands import CommandRoot
from config import cfg


set_colors(False)

pattern_address = compile(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(:\d{1,5})?")


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

        @cmd("open")
        async def host():
            server = Server(
                cfg.get("connection/address", "127.0.0.1"),
                cfg.get("connection/port", required=True),
            )

            run = create_task(server.run(loop))

            @cmd
            def close():
                server.server.close()

            del cmd.commands["open"]

            try:
                await run
            except CancelledError:
                cli.echo("Server closed.")
            finally:
                for remote in server.remotes:
                    await remote.terminate()

                cmd.add(host)
                del cmd.commands["close"]


    else:
        from ezipc.client import Client as ClientIPC

        @cmd
        async def connect(addr_port: str = cfg.get("connection/address", "127.0.0.1")):
            if cfg.get("connection/deny_custom_server", False):
                addr_port = (
                    f'{cfg.get("connection/address", "127.0.0.1")}'
                    f':{cfg.get("connection/port", required=True)}'
                )

            if not pattern_address.fullmatch(addr_port):
                raise ValueError(f"Invalid IPv4 Address: {addr_port}")
            elif ":" in addr_port:
                addr, port = addr_port.split(":")
            else:
                addr = addr_port
                port = cfg.get("connection/port", required=True)

            ipc = ClientIPC(addr, int(port))
            await ipc.connect(loop)

            cmd(ipc.disconnect)
            del cmd.commands["connect"]

            try:
                await ipc.listening
            except CancelledError:
                cli.echo("Connection closed.")
            finally:
                await ipc.disconnect()

                cmd.add(connect)
                del cmd.commands["disconnect"]
