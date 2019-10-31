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

    client: Optional[Client] = None

    cli.console_header = (
        lambda: " :: ".join(
            (f"Server: {client.remote.id}", f"Commands: {len(cmd.commands)}")
        )
        if client is not None and client.remote is not None
        else "[ NOT CONNECTED ]"
    )

    def needs_remote(func):
        @wraps(func)
        def wrapped(*a, **kw):
            if client is None:
                raise RuntimeError("Command requires Connection.")
            else:
                return func(*a, **kw)

        return wrapped

    def needs_no_remote(func):
        @wraps(func)
        def wrapped(*a, **kw):
            if client is None:
                return func(*a, **kw)
            else:
                raise RuntimeError("Command cannot be used while Connected.")

        return wrapped

    @needs_remote
    async def send_command(
        meth: str, data: Union[list, dict] = None, wait: bool = True
    ) -> Union[dict, Future, list]:
        resp = await client.remote.request(f"CMD.{meth}", [] if data is None else data)
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
    async def login(username: str, password: str):
        result = await send_command("LOGIN", [username, password])
        if result and result[0]:
            cli.echo("Login Accepted.")
        else:
            cli.echo("Authentication Failure.")

    @cmd(task=True)
    @needs_no_remote
    async def connect(addr_port: str = cfg.get("connection/address", "127.0.0.1")):
        nonlocal client

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

        client = Client(addr, int(port))
        await client.connect(loop)

        @client.hook_notif("ETC.PRINT")
        async def _print(data: list):
            for line in data:
                cli.echo(f"{client.remote}: {line}")

        @client.hook_notif("USR.SYNC")
        async def set_id(data: dict):
            cli.prompt.username = data.get("username", cli.prompt.username)
            cli.prompt.hostname = data.get("hostname", cli.prompt.hostname)
            cli.prompt.path = Path(data.get("path", cli.prompt.path))

        try:
            cli.redraw()
            cli.TASKS.append(client.listening)
            await client.listening

        except CancelledError:
            cli.echo("Connection closed.")

        except Exception as e:
            cli.echo(f"Connection failed with {type(e).__name__!r}: {e}")

        finally:
            # CLEANUP
            if client and client.alive:
                await client.terminate()
            client = None
            cli.prompt.username = cfg["interface/initial/user"]
            cli.prompt.hostname = cfg["interface/initial/host"]
            cli.prompt.path = cfg["interface/initial/wdir"]

    @cmd
    @needs_remote
    async def disconnect():
        nonlocal client

        await client.terminate()
        client = None
