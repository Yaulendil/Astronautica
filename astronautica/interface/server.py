from asyncio import AbstractEventLoop, CancelledError
from pathlib import Path
from uuid import UUID

from .commands import CommandRoot
from .tui import Interface
from config import cfg
from engine import Galaxy, Spacetime


DATA_DIR = Path(cfg["data/directory"])


def setup_host(cli: Interface, cmd: CommandRoot, loop: AbstractEventLoop):
    from ezipc.server import Server

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
