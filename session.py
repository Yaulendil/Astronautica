from getpass import getuser
from time import sleep

import config
from engine import geometry, physics
from util import astroio
from util.paths import get_path


class Game:
    """
    Interface between software/memory and disk. Saves and loads game, creates
        and destroys objects, manages communication files with instances of
        the client terminal. Possibly the most important part of the host.
    """
    def __init__(self, name):
        self.name = name
        self.path = get_path(config.working_dir, name)
        if not self.path.exists():
            # Not a preexisting game? Make the directory to run the game in.
            self.path.mkdir()
        elif not self.path.is_dir():
            # Wait...We cant play here. This is File country.
            raise NotADirectoryError("{} is not a directory.".format(self.path))
        # Make sure the current user is the owner of this game.
        if self.path.owner() != getuser():
            raise PermissionError("Failed to connect to game: User is not host")

        self.space = geometry.Space()
        geometry.all_space = self.space
        self.objects = physics.index

        self.running = False
        self.turn_length = config.turn_length

    def run(self):
        self.running = True
        while self.running:
            # TODO: Create empty input files for client use
            # `config.working_dir/<game_name>/*.txt`
            self.publish()
            # TODO: Mark input files as writable
            self._wait()
            # TODO: Mark input files as unwritable
            # TODO: Read input files and send orders to ships
            # TODO: Execute ship orders
            physics.progress(self.turn_length)

    def _wait(self):
        # TODO: Replace with a method that waits only until the next (hour/turn_length)
        waited = 0
        while waited < self.turn_length:
            sleep(1)
            waited += 1

    def publish(self):
        """Save a limited dataset onto disk, for access by clients"""
        # Write serializations to `config.working_dir/<game_name>/obj.name.json`
        for obj in physics.index:
            if obj.__dict__.get("name"):
                astroio.save(self.path / obj.name, obj.serialize())

    def close(self):
        pass


def load(user: str, name: str):
    """
    Read previously-saved serializations from `astronautica/saves/$user/$name.json`
        and create a Game object out of them
    """
    pass
