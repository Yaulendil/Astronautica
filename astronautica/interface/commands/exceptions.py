class CommandError(Exception):
    """Base Class for problems with Commands."""


class CommandNotAvailable(CommandError):
    """Command cannot be used."""


class CommandNotFound(CommandError):
    """Command cannot be located."""


class CommandExists(CommandError):
    """Command cannot be added."""


class CommandFailure(CommandError):
    """Command cannot be executed."""


class CommandBadArguments(CommandFailure):
    """Command cannot be executed because the Arguments are wrong."""


class CommandBadInput(CommandFailure):
    """Command cannot be executed because the Input Data is wrong."""
