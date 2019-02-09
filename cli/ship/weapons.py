from cli import TerminalCore


class TerminalWpn(TerminalCore):
    """
    Weaponry shell, segmented sub-interpreter for attack commands.
    """
    host_init = "Weapons"
    promptColor = "\033[36m"

    def __init__(self, game, vessel):
        super().__init__()
        self.game = game
        self.vessel = vessel
        self.host = "FleetNet.{}:{}".format(self.game.stem, self.vessel.stem)
        self.path = "~/command/weapons"
