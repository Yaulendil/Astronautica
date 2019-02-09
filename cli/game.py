from cli import TerminalCore, _interruptible
from constructs import voidcraft
from session import Game


class TerminalHost(TerminalCore):
    """
    The Host shell, within which the game engine itself will run.
    """
    host_init = "Panopticon"
    promptColor = "\033[91m"

    def __init__(self, name):
        """Create a new game session"""
        super().__init__()
        self.name = name
        self.session = Game(name)
        self.host = "FleetNet.{}".format(self.session.path.stem)
        self.path = "/"
        self.killed = False

    @_interruptible
    def do_run(self, *_):
        """Begin monitoring this sector. To exit, ^C"""
        self.session.run()

    def do_spawn_ship(self, line):
        """Track a new vessel nearby."""
        params = line.split()
        if line:
            voidcraft.Sloop(*params)

    @_interruptible
    def do_kill(self, *_):
        """Sever the connection to this station and return to the above shell."""
        if input("This will end the currently loaded session. Confirm? [y/N] ").lower() == "y":
            self.killed = True
            self.session.close()
            return super().do_exit()
        else:
            print("Cancelled.")

    def do_save(self, name):
        """Fully serialize all objects and save to disk for storage"""
        # TODO: Write serialization to `astronautica/saves/<host_username>/$name.json`
        pass

    def do_load(self, name):
        """Deserialize all objects read from a stored file on disk"""
        # TODO: Read serialization at `astronautica/saves/<host_username>/$name.json`
        pass
