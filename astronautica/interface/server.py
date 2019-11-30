from asyncio import AbstractEventLoop, CancelledError
from functools import wraps
from pathlib import Path
from typing import Dict, Optional
from uuid import UUID

from ezipc.remote import Remote
from ezipc.util import P
from users import get_user, KEYS, new_keys, Session

from .commands import CommandNotAvailable, CommandRoot
from .tui import Interface
from config import cfg
from engine import CB_POST_TICK, Galaxy, Spacetime


DATA_DIR = Path(cfg["data/directory"])


def setup_host(cli: Interface, cmd: CommandRoot, loop: AbstractEventLoop):
    from ezipc.server import Server

    server: Optional[Server] = None
    sessions: Dict[Remote, Session] = {}

    st = Spacetime()
    # space = st.space
    P.verbosity = 3

    cli.console_header = lambda: " :: ".join(
        (
            f"Clients: {len(server.remotes)}" if server else "Server Offline",
            "Galaxy: {}".format(
                f"{len(st.world.loaded)}/{st.world.stars.shape[0]}"
                if st.world and st.world.stars.shape
                else None
            ),
        )
    )

    def hostup():
        if st.world and st.world.gdir:
            cli.prompt.hostname = st.world.gdir.stem
            cli.prompt.path = Path("/")
        else:
            cli.prompt.hostname = "NONE"
            cli.prompt.path = Path("~")

    hostup()
    cli.prompt.username = "host"

    def needs_session(func):
        @wraps(func)
        def wrapped(data, remote):
            if remote not in sessions:
                raise CommandNotAvailable("Requires Session.")
            else:
                return func(data, remote, sessions[remote])

        return wrapped

    def needs_server(func):
        @wraps(func)
        def wrapped(*a, **kw):
            if server is None:
                raise CommandNotAvailable("Command requires Active Host.")
            else:
                return func(*a, **kw)

        return wrapped

    def needs_no_server(func):
        @wraps(func)
        def wrapped(*a, **kw):
            if server is None:
                return func(*a, **kw)
            else:
                raise CommandNotAvailable("Command cannot be used while Hosting.")

        return wrapped

    ###===---
    # COMMAND HOOKS: All "local" Commands for the Server Console go here.
    ###===---

    @cmd
    def galaxy():
        raise NotImplementedError

    @galaxy.sub
    async def new():
        """Generate a new Galaxy."""
        yield "Generating..."
        st.world = Galaxy.generate((1.4, 1, 0.2), arms=3)
        hostup()
        yield f"New Galaxy of {st.world.stars.shape[0]} stars generated."

    @galaxy.sub
    async def load(path: str):
        """Load a Galaxy from a file."""
        yield "Loading..."
        try:
            st.world = Galaxy.from_file(DATA_DIR / "world" / path)
        except NotADirectoryError:
            yield "Galaxy Directory not found."
        else:
            hostup()
            yield f"Loaded {st.world.stars.shape[0]} stars."

    @galaxy.sub
    async def rename(path: str = None):
        """Change the storage location of the current Galaxy."""
        path = DATA_DIR / path
        if path.parent != DATA_DIR:
            return "Galaxy Directory must be a simple name."
        st.world.rename(path)
        hostup()
        return f"Galaxy Renamed. New location: {path}"

    @galaxy.sub
    async def save():
        """Write the Galaxy to storage."""
        yield "Saving..."
        st.world.save()
        yield f"Galaxy Saved in: {st.world.gdir}"

    @galaxy.sub
    async def rand():
        """Fetch a randomly-selected System."""
        yield repr(st.world.get_system(UUID(int=st.world.system_random()[3])))

    @cmd(task=True)
    @needs_no_server
    async def _open(ip4: str = None, port: int = None):
        """Open the Server and begin simulating the passage of Time."""
        nonlocal server
        server = Server(
            ip4 or cfg.get("connection/address", "127.0.0.1"),
            port or cfg.get("connection/port", required=True),
        )
        server.setup()

        run = await server.run(loop)  # Start the Server.
        world = loop.create_task(st.run())  # Start the World.

        @server.hook_connect
        async def prep_session(remote: Remote):
            session = Session(remote)
            sessions[remote] = session
            await session.sync()
            # await remote.notif(
            #     "ETC.PRINT", ["Connected to FleetNet.", "Use LOGIN to Authenticate."]
            # )

        @server.hook_disconnect
        async def cleanup_session(remote: Remote):
            if remote in sessions:
                del sessions[remote]

        ###===---
        # REQUEST HOOKS: All "incoming" Commands from Remote Clients go here.
        ###===---

        @server.hook_request("CMD.CD")
        async def cd(data):
            cli.print(repr(data))
            return [True]

        @server.hook_request("CMD.LOGIN")
        @needs_session
        async def login(data, _remote: Remote, session: Session):
            if session.login(*data):
                await session.sync(path="~")
                return True
            else:
                return False

        @server.hook_request("CMD.REGISTER")
        @needs_session
        async def register(data, _remote: Remote, session: Session):
            if session.register(*data):
                await session.sync(path="~")
                return True
            else:
                return False

        ###===---

        bcast = lambda: server.bcast_notif("ETC.PRINT", ["New Telemetry available."])
        CB_POST_TICK.append(bcast)

        try:
            await run

        except CancelledError:
            cli.print("Server closed.")

        except Exception as e:
            cli.print(f"Server raised {type(e).__name__!r}: {e}")

        finally:
            # CLEANUP
            if bcast in CB_POST_TICK:
                CB_POST_TICK.remove(bcast)

            if world.cancel():
                await world

            if server:
                await server.terminate()
                server = None

    @cmd
    async def keys():
        """Show or manipulate Access Keys."""
        raise NotImplementedError

    @keys.sub
    async def free(*access_key):
        """Dissociate one or more Access Keys from their Usernames."""
        with KEYS:
            for k in access_key:
                if k in KEYS:
                    owner = (KEYS[k] or {}).get("username")
                    KEYS[k] = None
                    try:
                        if owner:
                            user = get_user(owner)
                            yield f"Freeing key {k!r} from {owner!r}."
                        else:
                            raise ValueError

                    except FileNotFoundError:
                        yield f"Key {k!r} owner {owner!r} not found."
                    except ValueError:
                        yield f"Key {k!r} is not claimed."

                    else:
                        if user:
                            user["key"] = None
                            user.sync()
                else:
                    yield f"Key {k!r} is not claimed."

    @keys.sub
    async def generate(number: int = 1):
        """Generate a number of new Access Keys."""
        return new_keys(number)

    @keys.sub
    async def show():
        """Display active Access Keys."""
        return (
            f"{key} :: {value['username']}" if value is not None else key
            for key, value in KEYS.items()
        )

    @show.sub
    async def free():
        """Display only available Access Keys."""
        return (key for key, value in KEYS.items() if value is None)

    @show.sub
    async def used():
        """Display only Access Keys that are in use."""
        return (
            f"{key} :: {value['username']}"
            for key, value in KEYS.items()
            if value is not None
        )

    @cmd
    @needs_server
    async def close():
        """Stop the Server, and stop iterating Time."""
        nonlocal server

        await server.terminate()
        server = None

    async def cleanup():
        if server:
            await close()

    return cleanup
