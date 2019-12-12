from itertools import chain

from pathlib import Path
from sys import argv
from typing import Any, Iterable, Sequence, Tuple, Union

import yaml


DELIM = "/"


def getpath(filename: str = "config.yml") -> Path:
    p = Path(argv[0])

    if p.name == filename:
        return p
    elif p.is_file():
        return p.parent / filename
    elif p.is_dir():
        return p / filename
    else:
        raise FileNotFoundError(p)


def split(route: Sequence[str]) -> Sequence[str]:
    if isinstance(route, str):
        route = [route]

    return list(chain(*(part.split(DELIM) for part in route)))


class ConfigError(Exception):
    """Required value not found in Configuration File."""

    def __init__(self, route: Sequence[str]):
        super().__init__(f"Missing Configuration option: {'.'.join(route)}")


class Config(object):
    __slots__ = (
        "data",
        "path",
    )

    def __init__(self, path: Path = getpath()):
        self.data = {}
        self.path: Path = path

        self.load()

    def load(self, path: Union[Path, str] = None):
        if path is not None:
            self.path = Path(path)

        with self.path.open("r") as file:
            self.data = yaml.safe_load(file)

    def get(
        self,
        route: Union[Iterable[str], str],
        default: Any = None,
        *,
        enforce: type = None,
        required: bool = False,
    ) -> Any:
        route = split(route)

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
                    f"Config option {'.'.join(route)!r} is of incorrect type:"
                    f" Wanted '{enforce}', got '{type(here)}'"
                )

    def set(self, route: Union[Iterable[str], str], value: Any) -> None:
        *route, final = split(route)
        self.get(route, enforce=dict)[final] = value

    def __getitem__(self, key: Union[str, Tuple[str, Any]]) -> Any:
        if isinstance(key, str):
            return self.get(key)
        elif isinstance(key, Sequence):
            return self.get(*key)

    def __setitem__(self, key: Union[Iterable[str], str], value: Any) -> None:
        return self.set(key, value)


cfg = Config()
