"""Interface Package: Command line Client and all integrations with Engine."""
from asyncio import AbstractEventLoop, Future, sleep, CancelledError
from pathlib import Path
from re import compile
from time import sleep as sleep2
from typing import Tuple, Union
from uuid import UUID

from ezipc.util import P

from .client import Interface
from .commands import CommandRoot
from .etc import T
from config import cfg
from engine import Galaxy, Spacetime


DATA_DIR = Path(cfg["data/directory"])
pattern_address = compile(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(:\d{1,5})?")


def get_client(loop) -> Tuple[Interface, CommandRoot]:
    cmd = CommandRoot()
    interface_client = Interface(loop, command_handler=cmd)
    cmd.set_client(interface_client)

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
    async def qwertz(*words):
        for word in words:
            await sleep(1)
            yield f"QWERT {word}"

    @cmd
    def test(*text):
        yield from map(repr, text)

    return interface_client, cmd


def setup_host(cli: Interface, cmd: CommandRoot, loop: AbstractEventLoop):
    from ezipc.server import Server

    P.output_line = cli.echo

    st = Spacetime()
    # space = st.space

    @cmd("open", task=True)
    async def host():
        server = Server(
            cfg.get("connection/address", "127.0.0.1"),
            cfg.get("connection/port", required=True),
        )
        server.setup()

        run = loop.create_task(server.run(loop))  # Start the Server.
        world = loop.create_task(st.run(echo=cli.echo))  # Start the World.

        @cmd
        def close():
            server.server.close()

        del cmd.commands["open"]

        @server.hook_request("CD")
        async def cd(data):
            cli.echo(repr(data))
            return [True]

        @server.hook_request("LOGIN")
        async def login(data):
            cli.echo(repr(data))
            return [name.lower().replace(" ", "") for name in data]

        @server.hook_request("SYNC")
        async def sync(_data):
            return dict(username="nobody", hostname="ingress", path="/login")

        try:
            await run

        except CancelledError:
            cli.echo("Server closed.")

        except Exception as e:
            cli.echo(f"Server raised {type(e).__name__!r}: {e}")

        finally:
            world.cancel()
            await server.terminate()

            cmd.add(host)
            del cmd.commands["close"]
            if st.world:
                st.world.save()

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
        yield "Galaxy Saved in: {}".format(st.world.gdir)

    @g.sub
    async def rand():
        yield repr(st.world.get_system(UUID(int=st.world.system_random()[3])))


def setup_client(cli: Interface, cmd: CommandRoot, loop: AbstractEventLoop):
    from ezipc.client import Client as ClientIPC

    P.output_line = cli.echo

    @cmd(task=True)
    async def connect(addr_port: str = cfg.get("connection/address", "127.0.0.1")):
        port = cfg.get("connection/port", required=True)

        if cfg.get("connection/deny_custom_server", False):
            addr_port = f'{cfg.get("connection/address", "127.0.0.1")}' f":{port}"

        if not pattern_address.fullmatch(addr_port):
            raise ValueError(f"Invalid IPv4 Address: {addr_port}")
        elif ":" in addr_port:
            addr, port = addr_port.split(":")
        else:
            addr = addr_port

        ipc = ClientIPC(addr, int(port))
        await ipc.connect(loop)

        cmd(ipc.disconnect)
        del cmd.commands["connect"]

        async def send_command(
            meth: str, data: Union[list, dict], default=None, wait: bool = True
        ) -> Union[dict, Future, list]:
            resp = await ipc.remote.request(meth, data)
            if wait:
                return await resp
            else:
                return resp

        @cmd
        async def cd(path: str):
            result = await send_command("CD", [path])
            if result and True in result:
                cli.prompt.path /= path
                cli.prompt.path = cli.prompt.path.resolve()

        @cmd
        async def login(username: str):
            result = await send_command("LOGIN", [username])
            if result:
                cli.prompt.username = result[0]

        @cmd
        async def sync():
            result = await send_command("SYNC", [], {})
            cli.prompt.username = result.get("username", cli.prompt.username)
            cli.prompt.hostname = result.get("hostname", cli.prompt.hostname)
            cli.prompt.path = Path(result.get("path", cli.prompt.path))

        @cmd
        async def ping(*a):
            result = await send_command("PING", list(a))
            cli.echo(repr(result))

        @cmd
        async def time():
            result = await send_command("TIME", [])
            cli.echo(repr(result))

        try:
            await sync()
            cli.redraw()
            cli.TASKS.append(ipc.listening)
            await ipc.listening

        except CancelledError:
            cli.echo("Connection closed.")

        except Exception as e:
            cli.echo(f"Connection failed with {type(e).__name__!r}: {e}")

        finally:
            await ipc.terminate()

            cmd.add(connect)
            del cmd.commands["disconnect"]
