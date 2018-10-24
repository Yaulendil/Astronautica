from cmd import Cmd


class GameTerminal(Cmd):
    def __init__(self, game, player):
        """Attach to $game and take control of $player"""
        super().__init__()


class LoginTerminal(Cmd):
    pass
