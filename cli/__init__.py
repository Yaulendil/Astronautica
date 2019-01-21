print("Connection established. Initiating QES 3.1 key exchange...")

from pathlib import Path

from cli.core import TerminalCore, _delay, _interruptible
from cli.game import TerminalHost
from cli.ship import TerminalShip


wd = "astronautica"  # Working Directory


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
        self.path = "/"
        self.game = None

    def do_ls(self, line):
        """List currently active Host Stations, or vessels in range of a Host Station.
        Syntax: ls [<host_name>]"""
        if line:
            path = Path(wd, line)
            title = "List of vessels in range of Host '{}':".format(line)
        else:
            path = Path(wd)
            title = "List of live Host Stations:"
        ls = [p.stem for p in path.glob("*")]
        if not path.is_dir() or not ls:
            print("Nothing found.")
            return
        print(title)
        for host in ls:
            if not host.endswith("_orders"):
                print("  - " + host)

    def do_host(self, line):
        """Tunnel to a Host Station through which interacting constructs can be directed.
        Syntax: host <host>"""
        if self.game:
            if line:
                print("A game is already running on this connection.")
            else:
                self.game.cmdloop()
        else:
            name = (line or input("Enter title of Host Station: ")).strip()
            if not name:
                print("Invalid name.")
            elif Path(wd).glob(name):
                print("Duplicate name.")
            else:
                self.game = TerminalHost(name)
                self.game.cmdloop()

    @_interruptible
    def do_login(self, line):
        """Connect to a vessel via QSH to check its scans or issue orders.
        Syntax: login <host>/<vessel_name>"""
        name = (line or input("Enter 'host/vessel': ")).strip()
        if not name or name.count("/") != 1:
            print("Invalid name.")
            return

        host, vessel = name.split("/")
        hostpath = Path(wd, host)
        shippath = Path(wd, host, vessel + ".json")
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
        shell = TerminalShip(hostpath, shippath)
        if shell.authenticate():
            shell.cmdloop()
