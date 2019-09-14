"""Interface Package: Command line Client and all integrations with Engine."""

from asyncio import AbstractEventLoop, sleep, CancelledError
from re import compile
from time import sleep as sleep2
from typing import Tuple

from ezipc.util import P

from .client import Client
from .commands import CommandRoot
from config import cfg
from engine import Object, run_world, Spacetime


pattern_address = compile(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(:\d{1,5})?")


def get_client(loop) -> Tuple[Client, CommandRoot]:
    cmd = CommandRoot()
    interface_client = Client(loop, command_handler=cmd)
    cmd.set_client(interface_client)

    @cmd
    def asdf(*words):
        sleep2(3)
        yield from words

    @asdf.sub
    async def qwert(*words):
        for word in words:
            await sleep(1)
            yield f"QWERT {word}"

    @asdf.sub(no_dispatch=True)
    async def qwertz(*words):
        for word in words:
            await sleep(1)
            yield f"QWERT {word}"

    return interface_client, cmd


def setup(cli: Client, cmd: CommandRoot, loop: AbstractEventLoop, host: bool):
    P.output_line = cli.echo

    if host:
        from ezipc.server import Server

        st = Spacetime()
        space = st.space

        @cmd("open")
        async def host():
            server = Server(
                cfg.get("connection/address", "127.0.0.1"),
                cfg.get("connection/port", required=True),
            )

            run = loop.create_task(server.run(loop))  # Start the Server.
            world = loop.create_task(run_world(st))  # Start the World.

            @cmd
            def close():
                server.server.close()

            del cmd.commands["open"]

            try:
                await run

            except CancelledError:
                cli.echo("Server closed.")

            finally:
                world.cancel()
                for remote in server.remotes:
                    await remote.terminate()

                cmd.add(host)
                del cmd.commands["close"]

        @cmd
        def spawn(x="0", y="0", z="0"):
            try:
                new = Object((int(x), int(y), int(z)), space=space)
            except ValueError:
                return "Cannot make arguments into ints."
            else:
                return new

        @cmd
        def ls():
            yield from iter(st.index)

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
