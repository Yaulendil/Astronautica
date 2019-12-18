from asyncio import AbstractEventLoop, CancelledError
from functools import wraps
from pathlib import Path
from re import compile
from typing import Optional

from ezipc.remote import RemoteError
from ezipc.util import echo

from .commands import CommandNotAvailable, CommandRoot
from .tui import Interface
from config import cfg


pattern_address = compile(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(:\d{1,5})?")


def setup_client(cli: Interface, cmd: CommandRoot, loop: AbstractEventLoop):
    from ezipc.client import Client

    client: Optional[Client] = None
    cli.console_header = (
        lambda: " :: ".join(
            (
                f"Server: {client.remote.id}",
                f"Commands: {len(cmd.commands)}",
                "Secure"
                if client and client.remote and client.remote.is_secure
                else "NOT SECURE",
            )
        )
        if client is not None and client.remote is not None
        else "[ NOT CONNECTED ]"
    )

    def needs_remote(func):
        @wraps(func)
        def wrapped(*a, **kw):
            if client is None:
                raise CommandNotAvailable("Command requires Connection.")
            else:
                return func(*a, **kw)

        return wrapped

    def needs_no_remote(func):
        @wraps(func)
        def wrapped(*a, **kw):
            if client is None:
                return func(*a, **kw)
            else:
                raise CommandNotAvailable("Command cannot be used while Connected.")

        return wrapped

    async def fetch():
        if client and client.alive:
            try:
                telem = await client.remote.request("TLM.FETCH", timeout=10)
            except TimeoutError:
                pass
            else:
                echo("Telemetry Updated.")
                cli.scans.telemetry = telem

    @cmd
    @needs_remote
    async def login(username: str = None):
        await client.remote.request(
            "USR.LOGIN",
            [
                username or await cli.get_input("Enter Username"),
                await cli.get_input("Enter Password", hide=True),
            ],
            timeout=10,
        )
        echo("Login Accepted.")

    @cmd
    @needs_remote
    async def register(username: str = None, *, key: str = None):
        username: str = username or await cli.get_input("Enter Username")
        password: str = await cli.get_input("Enter Password", hide=True)

        if password == await cli.get_input("Confirm Password", hide=True):
            # try:
            await client.remote.request(
                    "USR.REGISTER",
                    [
                        username,
                        password,
                        key or await cli.get_input("Enter Access Code"),
                    ],
                timeout=10,
                )
            return "Registration successful."
        else:
            return "Password Confirmation does not match."

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

        @client.hook_notif("TLM.UPDATE")
        async def update(data: list):
            echo("Receiving new Telemetry.")
            cli.scans.telemetry = data

        @client.hook_notif("ETC.PRINT")
        async def _print(data: list):
            cli.print(*(f"{client.remote}: {line}" for line in data))

        @client.hook_notif("USR.SYNC")
        async def set_id(data: dict):
            cli.prompt.username = data.get("username") or cli.prompt.username
            cli.prompt.hostname = data.get("hostname") or cli.prompt.hostname
            cli.prompt.path = Path(data.get("path") or cli.prompt.path)
            cmd.cap_set(disable=data.get("disable"), enable=data.get("enable"))

        try:
            await client.connect(loop)
            try:
                await fetch()
            except RemoteError:
                pass

            cli.redraw()

            if client.listening:
                cli.TASKS.append(client.listening)
                await client.listening

        except CancelledError:
            cli.print("Connection closed.")

        except Exception as e:
            cli.print(f"Connection failed: {type(e).__name__}: {e}")

        finally:
            # CLEANUP
            cli.scans.telemetry = None
            if client and client.alive:
                await client.terminate()
            client = None
            cli.prompt.username = cfg["interface/initial/user"]
            cli.prompt.hostname = cfg["interface/initial/host"]
            cli.prompt.path = Path(cfg["interface/initial/wdir"])

    @cmd
    @needs_remote
    async def disconnect():
        nonlocal client

        t = client.terminate()
        client = None
        await t

    @cmd
    @needs_remote
    async def _fetch():
        return await fetch()

    async def cleanup():
        if client:
            await disconnect()

    return cleanup
