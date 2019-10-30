from asyncio import AbstractEventLoop, CancelledError, Future
from functools import wraps
from pathlib import Path
from re import compile
from typing import Union, Optional

from .commands import CommandRoot
from .tui import Interface
from config import cfg


pattern_address = compile(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(:\d{1,5})?")


def setup_client(cli: Interface, cmd: CommandRoot, loop: AbstractEventLoop):
    from ezipc.client import Client

    ipc: Optional[Client] = None

    def needs_remote(func):
        @wraps(func)
        def wrapped(*a, **kw):
            if ipc is None:
                raise RuntimeError("Command requires Connection.")
            else:
                return func(*a, **kw)

        return wrapped

    def needs_no_remote(func):
        @wraps(func)
        def wrapped(*a, **kw):
            if ipc is None:
                return func(*a, **kw)
            else:
                raise RuntimeError("Command cannot be used while Connected.")

        return wrapped

    @needs_remote
    async def send_command(
        meth: str, data: Union[list, dict], default=None, wait: bool = True
    ) -> Union[dict, Future, list]:
        resp = await ipc.remote.request(f"CMD.{meth}", data)
        if wait:
            return await resp
        else:
            return resp

    @cmd(task=True)
    @needs_no_remote
    async def connect(addr_port: str = cfg.get("connection/address", "127.0.0.1")):
        nonlocal ipc

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

        ipc = Client(addr, int(port))
        await ipc.connect(loop)

        # cmd(ipc.disconnect)
        # del cmd.commands["connect"]

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
            if ipc.alive:
                await ipc.terminate()

    @cmd
    @needs_remote
    async def disconnect():
        await ipc.terminate()

    @cmd
    @needs_remote
    async def cd(path: str):
        result = await send_command("CD", [path])
        if result and True in result:
            cli.prompt.path /= path
            cli.prompt.path = cli.prompt.path.resolve()

    @cmd
    @needs_remote
    async def login(username: str):
        result = await send_command("LOGIN", [username])
        if result:
            cli.prompt.username = result[0]

    @cmd
    @needs_remote
    async def sync():
        result = await send_command("SYNC", [], {})
        cli.prompt.username = result.get("username", cli.prompt.username)
        cli.prompt.hostname = result.get("hostname", cli.prompt.hostname)
        cli.prompt.path = Path(result.get("path", cli.prompt.path))

    @cmd
    @needs_remote
    async def ping(*a):
        result = await send_command("PING", list(a))
        cli.echo(repr(result))

    @cmd
    @needs_remote
    async def time():
        result = await send_command("TIME", [])
        cli.echo(repr(result))
