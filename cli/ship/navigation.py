from cli import TerminalCore


class TerminalNav(TerminalCore):
    """
    Navigational shell, segmented sub-interpreter for movement commands.
    """
    host_init = "Navigation"
    promptColor = "\033[36m"

    def __init__(self, game, vessel):
        super().__init__()
        self.game = game
        self.vessel = vessel
        self.host = "FleetNet.{}:{}".format(self.game.stem, self.vessel.stem)
        self.path = "~/command/navigation"
