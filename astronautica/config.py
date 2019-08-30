working_dir = "/astronautica"
turn_length = 300  # Seconds

cmd_prompt = "{c}{u}@{h}\033[0m:\033[94m{p}\033[0m$ "
cmd_aliases = {"quit": "exit", "logout": "exit", "nav": "navigation", "wep": "weapons"}

class Scan:
    result_none = "Telemetry includes no {}."
    indent = 3
    display_attr = ["radius", "mass", "coords"]
    decimals = 3


from pathlib import Path
from sys import argv
from typing import Any, Sequence

import yaml


DELIM = "/"


def getpath(filename: str = "config.yml"):
    p = Path(argv[0])

    if p.name == filename:
        return p
    elif p.is_file():
        return p.parent / filename
    elif p.is_dir():
        return p / filename
    else:
        raise FileNotFoundError(p)


class ConfigError(Exception):
    """Required value not found in Configuration File."""

    def __init__(self, route: Sequence[str]):
        super().__init__(f"Missing Configuration option: {'.'.join(route)}")


class Config(object):
    def __init__(self, path: Path = getpath()):
        self.path: Path = path
        with self.path.open("r") as file:
            self.data = yaml.safe_load(file)

    def get(
        self,
        route: str,
        default: Any = None,
        *,
        enforce: type = None,
        required: bool = False,
    ):
        if DELIM in route:
            route = route.split(DELIM)
        else:
            route = [route]

        here = self.data
        try:
            for jump in filter(None, route):
                here = here[jump]
        except BaseException as e:
            if required:
                raise ConfigError(route) from e
            else:
                return default
        else:
            if enforce is None or isinstance(here, enforce):
                return here
            else:
                raise TypeError(
                    f"Config option '{'.'.join(route)}' is of incorrect type:"
                    f" Wanted '{enforce}', got '{type(here)}'"
                )


cfg = Config()
