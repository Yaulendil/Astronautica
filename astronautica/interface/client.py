from asyncio import AbstractEventLoop, CancelledError, Future
from pathlib import Path
from re import compile
from typing import Union

from .commands import CommandRoot
from .tui import Interface
from config import cfg


pattern_address = compile(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(:\d{1,5})?")


def setup_client(cli: Interface, cmd: CommandRoot, loop: AbstractEventLoop):
    from ezipc.client import Client

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

        ipc = Client(addr, int(port))
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
