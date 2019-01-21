from time import sleep

from cli import TerminalCore, _interruptible
from engine import geometry, physics
from constructs import voidcraft, nature


turn_length = 300


class Game:
    def __init__(self):
        self.space = geometry.Space()
        geometry.all_space = self.space
        self.objects = physics.index

        self.running = False
        self.turn_length = turn_length

    def run(self):
        self.running = True
        while self.running:
            self._wait()
            physics.progress(self.turn_length)

    def _wait(self):
        # TODO: Replace with a method that waits only until the next (hour/turn_length)
        waited = 0
        while waited < self.turn_length:
            sleep(1)
            waited += 1


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
        self.host = "{}:0".format(self.name)
        self.path = "/"
        self.game = Game()

    @_interruptible
    def do_run(self, *_):
        self.game.run()

    def do_spawn_ship(self, line):
        params = line.split()
        if line:
            voidcraft.Sloop(*params)
