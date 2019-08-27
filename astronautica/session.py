from datetime import datetime as dt, timedelta as td
from getpass import getuser
from time import sleep

from astronautica import config
from astronautica.engine.spacetime import Spacetime
from astronautica.util import astroio, paths


class Game:
    """Interface between software/memory and disk. Saves and loads game, creates
        and destroys objects, manages communication files with instances of the
        client terminal. Possibly the most important part of the host.
    """
    def __init__(self, name):
        self.name = name
        self.path = paths.get_path(config.working_dir, name)

        if not self.path.exists():
            # Not a preexisting game? Make the directory to run the game in.
            self.path.mkdir()
        elif not self.path.is_dir():
            # Wait...We cant play here. This is File country.
            raise NotADirectoryError("{} is not a directory.".format(self.path))

        # Make sure the current user is the owner of this game.
        if self.path.owner() != getuser():
            raise PermissionError("Failed to connect to game: User is not host")

        self.st = Spacetime()
        self.objects = self.st.index

        self.running = False
        self.turn_length = config.turn_length

    def run(self):
        self.running = True
        start = dt.utcnow()
        while self.running:
            # TODO: Create empty input files for client use
            # `config.working_dir/<game_name>/*.txt`
            self.publish()
            # TODO: Mark input files as writable
            start = self._wait(start)
            # Time from wait end to wait end should be as precise as possible.
            #     This prevents the expensive process of simulating a turn from
            #     cutting into the NEXT wait, by timing the start of every wait
            #     relative to the end of the previous one.
            if self.running: # Just to double check
                # TODO: Mark input files as unwritable
                # TODO: Read input files and send orders to ships
                # TODO: Execute ship orders
                self.st.progress(self.turn_length)

    def _wait(self, start: dt):
        """Wait until $turn_length seconds after $start. This allows the turn
            period to remain constant even though to calculate a turn takes a
            non-zero amount of time.
        """
        # TODO: Replace with a method that waits only until the next (hour/turn_length)
        until = start + td(seconds=self.turn_length)
        # waited = 0
        now = dt.utcnow()
        while now < until and self.running:
            sleep(1)
            now = dt.utcnow()
            # waited += 1
        return now

    def publish(self):
        """Save a limited dataset onto disk, for access by clients"""
        # Write serializations to `config.working_dir/<game_name>/obj.name.json`
        for obj in self.st.index:
            if obj.__dict__.get("name"):
                astroio.save(self.path / str(obj), obj.serialize())

    def close(self):
        """Delete self and go home."""
        rmdir_f(self.path)

    def add_object(self, obj):
        """Given a set of data, make it into a thing."""
        print(obj)


def load(name: str) -> Game:
    """Read previously-saved serializations from `astronautica/saves/$user/$name.json`
        and create a Game object out of them.
    """
    newgame = Game(name)
    user = getuser()

    src = (paths.root / "saves" / user / name).with_suffix(".json")
    world = astroio.load(src)

    for o in world:
        newgame.add_object(o)
    return newgame


def rmdir_f(path):
    """Recursively delete an entire directory and everything in it.
    WARNING: Very dangerous. Duh.
    """
    if not path.is_dir() or not path.is_absolute():
        return
    for sub in path.iterdir():
        if sub.is_dir() and not sub.is_symlink():
            rmdir_f(sub)
        else:
            sub.unlink()
    path.rmdir()
