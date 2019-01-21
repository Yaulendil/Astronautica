from getpass import getpass

from passlib.handlers.pbkdf2 import pbkdf2_sha256 as pw

import astroio
from cli import TerminalCore, _delay
from cli.ship.navigation import TerminalNav
from cli.ship.weapons import TerminalWpn


class TerminalShip(TerminalCore):
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
        self.path = "~/command"

        self.model = None
        self.load()
        self.updated = self.model["updated"]

        self.nav = TerminalNav(game, vessel)
        self.wpn = TerminalWpn(game, vessel)

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
        elif latest == self.model:
            print("Failed to commit changes: No changes to commit")
        else:
            astroio.save(self.vessel, self.model)
            print("Changes uploaded.")

    def authenticate(self):
        if not self.model.get("hash"):
            print("No passphrase is set.")
            return self._changepass()
        elif pw.verify(
            getpass("Passphrase for starship '{}': ".format(self.name)),
            self.model["hash"],
        ):
            return True
        else:
            print("Authentication failure.")

    def _changepass(self):
        h1 = pw.hash(getpass("Enter new passphrase: "))
        if not pw.verify(getpass("Confirm passphrase: "), h1):
            print("Passphrases do not match.")
            return False
        self.model["hash"] = h1
        print("Passphrase set. Change must be manually uploaded via 'commit'.")
        return True

    def do_update(self, *_):
        """Retrieve the latest telemetry scans of the constructs and its local space."""
        if input("Unsaved changes will be lost. Confirm? [y/N] ").lower() == "y":
            print("Updating telemetry...")
            self.load()
            _delay()
            print("Latest telemetry scans retrieved.")

    def do_commit(self, *_):
        """Upload orders and configuration changes to starship computer."""
        if input("Uploading all changes to starship. Confirm? [y/N] ").lower() == "y":
            self.save()

    def do_passwd(self, *_):
        """Change starship passphrase."""
        # "Insulator" method so that the return status is not passed back to CMD
        self._changepass()

    def do_navigation(self, line):
        """Issue a command to the navigation shell, or, take direct control of it"""
        if line:
            self.nav.onecmd(line)
        else:
            self.nav.cmdloop()

    def do_weapons(self, line):
        """Issue a command to the weapons shell, or, take direct control of it"""
        if line:
            self.wpn.onecmd(line)
        else:
            self.wpn.cmdloop()
