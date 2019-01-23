from time import sleep

from pathlib import Path

import astroio
from cli import TerminalCore, _interruptible
import config
from engine import geometry, physics
from constructs import voidcraft


class Game:
    def __init__(self, name):
        self.space = geometry.Space()
        geometry.all_space = self.space
        self.objects = physics.index

        self.name = name
        self.filepath = Path(config.working_dir, name)
        self.filepath.resolve().mkdir()
        self.running = False
        self.turn_length = config.turn_length

    def run(self):
        self.running = True
        while self.running:
            self.save()
            self._wait()
            physics.progress(self.turn_length)

    def _wait(self):
        # TODO: Replace with a method that waits only until the next (hour/turn_length)
        waited = 0
        while waited < self.turn_length:
            sleep(1)
            waited += 1

    def save(self):
        for obj in physics.index:
            if obj.__dict__.get("name"):
                astroio.save(self.filepath.joinpath(obj.name), obj.serialize())


class TerminalHost(TerminalCore):
    """
    The Host shell, within which the game engine itself will run.
    """

    prompt_init = "Panopticon"
    promptColor = "\033[91m"

    def __init__(self, name):
        """Create a new game session"""
        super().__init__()
        self.name = name
        self.game = Game(name)
        self.host = "FleetNet.{}:0".format(self.game.filepath.stem)
        self.path = "/"

    @_interruptible
    def do_run(self, *_):
        self.game.run()

    def do_spawn_ship(self, line):
        params = line.split()
        if line:
            voidcraft.Sloop(*params)
