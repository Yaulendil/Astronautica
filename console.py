print("Connection established. Initiating QES 3.1 key exchange...")

from cmd import Cmd
import crypt
import getpass
import pathlib
import time

import astroio


wd = "astronautica"
_PromptString = "{c}{u}@{h}\033[0m:\033[94m{p}\033[0m$ "


def _interruptible(func):
    def attempt(*a, **kw):
        try:
            func(*a, **kw)
        except KeyboardInterrupt:
            print("(Interrupted)")
    return attempt


class TerminalCore(Cmd):
    prompt_init = "Offline"
    intro = None
    farewell = None
    promptColor = "\033[93m"

    def __init__(self):
        super().__init__()
        self.host = self.prompt_init
        self.path = "~/"

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


class TerminalGame(TerminalCore):
    prompt_init = "Starship"
    promptColor = "\033[36m"

    def __init__(self, game, vessel):
        """Attach to $game and take control of $vessel"""
        super().__init__()
        self.game = game
        self.vessel_name = vessel
        self.host = self.vessel_name

    @property
    def vessel(self):
        path = pathlib.PurePath(self.game, self.vessel_name)
        concrete = pathlib.Path(*path.parts)
        if concrete.is_file():
            return astroio.load(concrete)

    def do_load(self, line):
        pass


class TerminalHost(TerminalCore):
    prompt_init = "Panopticon"
    promptColor = "\033[91m"


class TerminalLogin(TerminalCore):
    prompt_init = "FleetNet"
    intro = "Secure connection to FleetNet complete. For help: 'help' or '?'"
    farewell = "QLink powering down..."
    promptColor = "\033[33m"

    def do_ls(self, line):
        if line:
            path = pathlib.Path(wd, line)
            title = "List of vessels in game '{}':".format(line)
        else:
            path = pathlib.Path(wd)
            title = "List of live Hosts:"
        ls = [p.stem for p in path.glob("*")]
        if not path.is_dir() or not ls:
            print("Nothing found")
            return
        print(title)
        for game in ls:
            if not game.endswith("_orders"):
                print("  - " + game)

    def do_host(self, line):
        name = (line or input("Enter title of game: ")).strip()
        if not name:
            print("Invalid name.")
            return

    def do_login(self, line):
        """Connect to a vessel via QSH to poll its state or issue orders.
        Syntax: login <location>/<vessel_name>"""
        name = (line or input("Enter game/vessel: ")).strip()
        if not name:
            print("Invalid name.")
            return
        print("Connecting to {} as {}.".format(self.user, name))
        pwhash = getpass.getpass()
        TerminalGame(None, None).cmdloop()

