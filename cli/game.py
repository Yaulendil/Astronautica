from cli import TerminalCore


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
        self.path = "/"
