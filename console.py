print("Connection established. Initiating QES 3.1 key exchange...")

from cmd import Cmd
import crypt
import getpass
import pathlib
import random
import time

import astroio


wd = "astronautica"
_PromptString = "{c}{u}@{h}\033[0m:\033[94m{p}\033[0m$ "


def _delay(a=5, b=20):
    """Wait a short time to simulate an advanced function that causes a hang"""

    time.sleep(random.randint(a, b) / 10)


def _interruptible(func):
    """Designates a method during which a KeyboardInterrupt will not exit the shell."""

    def attempt(*a, **kw):
        try:
            func(*a, **kw)
        except KeyboardInterrupt:
            print("(Interrupted)")

    attempt.__doc__ = func.__doc__
    return attempt


class TerminalCore(Cmd):
    """
    The core shell, implementing functionality shared by all three primaries.
    Also wraps the cmdloop method as an interruptible, allowing smoother exiting via ^C.
    """

    prompt_init = "Offline"
    intro = None
    farewell = None
    promptColor = "\033[93m"

    def __init__(self):
        super().__init__()
        self.host = self.prompt_init
        self.path = "~"

    @property
    def user(self):
        return getpass.getuser()

    @property
    def prompt(self):
        return _PromptString.format(
            c=self.promptColor, u=self.user.lower(), h=self.host, p=self.path
        )

    @_interruptible
    def cmdloop(self, *a, **kw):
        return super().cmdloop(*a, **kw)

    def do_exit(self, *_):
        """Exit this context and return to the above shell."""
        if self.farewell:
            print(self.farewell)
        return True

    def default(self, line):
        if line == "EOF":
            print("exit")
            return self.do_exit(line)
        else:
            return super().default(line)


class TerminalHost(TerminalCore):
    """
    The Host shell, within which the game engine itself will run.
    """

    prompt_init = "Panopticon"
    promptColor = "\033[91m"

    def __init__(self, game):
        """Attach to $game and take control of $vessel"""
        super().__init__()
        self.game = game
        self.host = "{}:0".format(self.game.name)


class TerminalGame(TerminalCore):
    """
    The Game shell, from which starships are given orders and their scans are read.
    The main interface through which most users will be issuing commands. Password-protected.
    """

    prompt_init = "Starship"
    promptColor = "\033[36m"

    def __init__(self, game, vessel):
        """Attach to $game and take control of $vessel"""
        super().__init__()
        self.game = game
        self.vessel = vessel
        self.host = "FleetNet.{}:{}".format(self.game.stem, self.vessel.stem)
        self.path = "/command"

        self.model = None
        self.load()
        self.updated = self.model["updated"]

    @property
    def name(self):
        return self.vessel.stem

    def rescan(self):
        # path = pathlib.PurePath(self.game, self.vessel.name)
        # concrete = pathlib.Path(*path.parts)
        concrete = self.vessel.resolve()
        if concrete.is_file():
            return astroio.load(concrete)

    def load(self):
        self.model = self.rescan()
        self.updated = self.model["updated"]

    def save(self):
        latest = self.rescan()
        if latest["updated"] != self.model["updated"]:
            print("Failed to commit changes: Telemetry out of date")
            return
        elif hash(latest) == hash(self.model):
            print("Failed to commit changes: No changes to commit")
            return
        else:
            astroio.save(self.vessel, self.model)

    def authenticate(self):
        if not self.model["hash"]:
            print("No password is set.")
            self.do_passwd()
            return True
        else:
            pwhash = crypt.crypt(
                getpass.getpass(), self.model.get("salt", "asdfqwertyuiop")
            )
            if pwhash == self.model["hash"]:
                return True
            else:
                print("Authentication failure.")

    def do_update(self, *_):
        """Retrieve the latest telemetry scans of the voidcraft and its local space."""
        if input("Unsaved changes will be lost. Confirm? [y/N] ").lower() == "y":
            print("Updating telemetry...")
            self.load()
            _delay()
            print("Latest telemetry scans retrieved.")

    def do_passwd(self, *_):
        h1 = crypt.crypt(
            getpass.getpass("Enter new password: "),
            self.model.get("salt", "asdfqwertyuiop"),
        )
        h2 = crypt.crypt(
            getpass.getpass("Confirm password: "),
            self.model.get("salt", "asdfqwertyuiop"),
        )
        if h1 != h2:
            print("Passwords do not match.")
            return
        self.model["hash"] = h1
        print("Password set.")


class TerminalLogin(TerminalCore):
    """
    The login shell. A game lobby of sorts, from which the user launches the other shells.
    """

    prompt_init = "FleetNet"
    intro = "Secure connection to FleetNet complete. For help: 'help' or '?'"
    farewell = "QLink powering down..."
    promptColor = "\033[33m"

    def __init__(self):
        super().__init__()
        self.path = "/login"

    def do_ls(self, line):
        """List currently active Host Stations, or vessels in range of a Host Station.
        Syntax: ls [<host_name>]"""
        if line:
            path = pathlib.Path(wd, line)
            title = "List of vessels in range of Host '{}':".format(line)
        else:
            path = pathlib.Path(wd)
            title = "List of live Host Stations:"
        ls = [p.stem for p in path.glob("*")]
        if not path.is_dir() or not ls:
            print("Nothing found.")
            return
        print(title)
        for game in ls:
            if not game.endswith("_orders"):
                print("  - " + game)

    def do_host(self, line):
        """Tunnel to a Host Station through which interacting voidcraft can be directed.
        Syntax: host <host>"""
        name = (line or input("Enter title of Host Station: ")).strip()
        if not name:
            print("Invalid name.")
            return

    @_interruptible
    def do_login(self, line):
        """Connect to a vessel via QSH to check its scans or issue orders.
        Syntax: login <host>/<vessel_name>"""
        name = (line or input("Enter 'host/vessel': ")).strip()
        if not name or name.count("/") != 1:
            print("Invalid name.")
            return

        host, vessel = name.split("/")
        hostpath = pathlib.Path(wd, host)
        shippath = pathlib.Path(wd, host, vessel + ".json")
        if not hostpath.is_dir():
            print("Host Station not found.")
            return
        elif not shippath.is_file():
            print("Vessel not found.")
            return

        print(
            "Connecting to qsh://FleetNet.{}:{} as '{}'...".format(
                host, vessel, self.user
            )
        )
        shell = TerminalGame(hostpath, shippath)
        if shell.authenticate():
            shell.cmdloop()
