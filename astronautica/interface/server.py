from asyncio import AbstractEventLoop, CancelledError
from functools import wraps
from pathlib import Path
from typing import Optional
from uuid import UUID

from ezipc.remote import Remote
from ezipc.util import P

from .commands import CommandRoot
from .tui import Interface
from config import cfg
from engine import Galaxy, Spacetime


DATA_DIR = Path(cfg["data/directory"])


def setup_host(cli: Interface, cmd: CommandRoot, loop: AbstractEventLoop):
    from ezipc.server import Server

    server: Optional[Server] = None

    st = Spacetime()
    # space = st.space
    P.verbosity = 3

    def needs_server(func):
        @wraps(func)
        def wrapped(*a, **kw):
            if server is None:
                raise RuntimeError("Command requires Active Host.")
            else:
                return func(*a, **kw)

        return wrapped

    def needs_no_server(func):
        @wraps(func)
        def wrapped(*a, **kw):
            if server is None:
                return func(*a, **kw)
            else:
                raise RuntimeError("Command cannot be used while Hosting.")

        return wrapped

    ###===---
    # COMMAND HOOKS: All "local" Commands for the Server Console go here.
    ###===---

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

    @cmd("open", task=True)
    @needs_no_server
    async def host():
        nonlocal server
        server = Server(
            cfg.get("connection/address", "127.0.0.1"),
            cfg.get("connection/port", required=True),
        )
        server.setup()

        run = loop.create_task(server.run(loop))  # Start the Server.
        world = loop.create_task(st.run(echo=cli.echo))  # Start the World.

        @server.hook_connect
        async def sync(remote: Remote):
            await remote.notif("SYNC", dict(username="nobody", hostname="ingress", path="/login"))

        ###===---
        # REQUEST HOOKS: All "incoming" Commands from Remote Clients go here.
        ###===---

        @server.hook_request("CMD.CD")
        async def cd(data):
            cli.echo(repr(data))
            return [True]

        @server.hook_request("CMD.LOGIN")
        async def login(data):
            cli.echo(repr(data))
            return [name.lower().replace(" ", "") for name in data]

        ###===---

        try:
            await run

        except CancelledError:
            cli.echo("Server closed.")

        except Exception as e:
            cli.echo(f"Server raised {type(e).__name__!r}: {e}")

        finally:
            # CLEANUP
            if world.cancel():
                await world

            if server:
                await server.terminate()
                server = None

    @cmd
    @needs_server
    async def close():
        nonlocal server

        server.server.close()
        server = None
