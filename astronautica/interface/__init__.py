"""Interface Package: Command line Client and all integrations with Engine."""

from asyncio import AbstractEventLoop, sleep, CancelledError
from pathlib import Path
from re import compile
from time import sleep as sleep2
from typing import Tuple, Union
from uuid import UUID

from ezipc.util import P

from .client import Client
from .commands import CommandRoot
from .etc import T
from config import cfg
from engine import Coordinates, Galaxy, Object, Spacetime


DATA_DIR = Path(cfg["data/directory"])
pattern_address = compile(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(:\d{1,5})?")


def get_client(loop) -> Tuple[Client, CommandRoot]:
    cmd = CommandRoot()
    interface_client = Client(loop, command_handler=cmd)
    cmd.set_client(interface_client)

    @cmd
    def asdf(*words):
        sleep2(3)
        yield from words

    @asdf.sub(task=True)
    async def qwert(*words):
        for word in words:
            await sleep(1)
            yield f"QWERT {word}"

    @asdf.sub
    async def qwertz(*words):
        for word in words:
            await sleep(1)
            yield f"QWERT {word}"

    @cmd
    def test(*text):
        yield from map(repr, text)

    return interface_client, cmd


def setup_host(cli: Client, cmd: CommandRoot, loop: AbstractEventLoop):
    from ezipc.server import Server

    P.output_line = cli.echo

    st = Spacetime()
    space = st.space

    @cmd("open", task=True)
    async def host():
        server = Server(
            cfg.get("connection/address", "127.0.0.1"),
            cfg.get("connection/port", required=True),
        )

        run = loop.create_task(server.run(loop))  # Start the Server.
        world = loop.create_task(st.run())  # Start the World.

        @cmd
        def close():
            server.server.close()

        del cmd.commands["open"]

        try:
            await run

        except CancelledError:
            cli.echo("Server closed.")

        except Exception as e:
            cli.echo(f"Server raised {type(e).__name__!r}: {e}")

        finally:
            world.cancel()
            for remote in server.remotes:
                await remote.terminate()

            cmd.add(host)
            del cmd.commands["close"]
            if st.world:
                st.world.save()

    # @cmd
    # def spawn(x="0", y="0", z="0") -> Union[Object, str]:
    #     try:
    #         new = Object(frame=Coordinates((float(x), float(y), float(z)), space=space))
    #     except ValueError:
    #         return "Cannot make arguments into numbers."
    #     else:
    #         return new

    # @cmd
    # def ls():
    #     yield from iter(st.index)

    @cmd
    def g():
        raise NotImplementedError

    @g.sub
    async def new():
        yield "Generating..."
        st.world = Galaxy.generate((1.4, 1, 0.2), arms=3)
        yield "New Galaxy Generated."

    @g.sub
    async def load(path: str):
        yield "Loading..."
        try:
            st.world = Galaxy.from_file(DATA_DIR / path)
        except NotADirectoryError:
            yield "Galaxy Directory not found."
        else:
            yield f"Loaded {st.world.stars.shape} stars."

    @g.sub
    async def rename(path: str = None):
        path = DATA_DIR / path
        if path.parent != DATA_DIR:
            return "Galaxy Directory must be a simple name."
        st.world.rename(path)
        return f"Galaxy Renamed. New location: {path}"

    @g.sub
    async def save():
        yield "Saving..."
        st.world.save()
        yield "Galaxy Saved in: {}".format(
        st.world.gdir)

    @g.sub
    async def rand():
        yield repr(st.world.get_system(UUID(int=st.world.system_random()[3])))


def setup_client(cli: Client, cmd: CommandRoot, loop: AbstractEventLoop):
    from ezipc.client import Client as ClientIPC

    P.output_line = cli.echo

    @cmd(task=True)
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

        except Exception as e:
            cli.echo(f"Connection failed with {type(e).__name__!r}: {e}")

        finally:
            await ipc.disconnect()

            cmd.add(connect)
            del cmd.commands["disconnect"]
