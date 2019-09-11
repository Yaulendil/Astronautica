from pathlib import Path
from typing import Optional, Union
from uuid import UUID, uuid4

import numpy as np
from yaml import safe_load

from ..abc import Domain
from .gravity import MultiSystem, System


def _generate_galaxy() -> np.ndarray:
    ...


class Galaxy(object):
    @classmethod
    def from_file(cls, path: Union[Path, str]) -> "Galaxy":
        path = Path(path)

        if path.is_file():
            p_dir = path.parent
            p_data = path
            p_stars = path / "stars"
        elif path.is_dir():
            p_dir = path
            p_data = path / "meta.yml"
            p_stars = path / "stars"
        else:
            raise FileNotFoundError(path)

        def stream():
            with p_stars.open("r") as file:
                for line in file:
                    if line.count("/") == 3:
                        x, y, z, h = line.strip("\n").split("/")
                        yield (float(x), float(y), float(z), UUID(hex=h).int)

        stars = np.array(stream())

        with p_data.open("r") as f:
            data = safe_load(f)

        return cls(stars, p_dir, data["uuid"])

    @classmethod
    def generate(cls) -> "Galaxy":
        hex_ = uuid4().get_hex()
        return cls(_generate_galaxy(), Path("data", hex_), hex_)

    def __init__(self, stars: np.ndarray, gdir: Path, gid: str):
        self.stars = stars
        self.gdir = gdir
        self.gid = gid

    def system_at_coordinate(self, pos: np.ndarray) -> Optional[Domain]:
        ...

    def system_by_uuid(self, uuid: str) -> Optional[Domain]:
        ...
