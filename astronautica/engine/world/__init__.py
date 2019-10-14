from pathlib import Path
from typing import Optional, Union
from uuid import UUID, uuid4

import numpy as np
from yaml import safe_load

from ..space.base import Domain
from ..visualizer import render
from .generation import generate_galaxy
from .gravity import MultiSystem, System


class Galaxy(object):
    @classmethod
    def from_file(cls, path: Union[Path, str]) -> "Galaxy":
        path = Path(path)

        if path.is_file():
            p_dir = path.parent
            p_data = path
            p_stars = p_dir / "stars"
        elif path.is_dir():
            p_dir = path
            p_data = path / "meta.yml"
            p_stars = path / "stars"
        else:
            raise FileNotFoundError(path)

        with p_data.open("r") as f:
            data = safe_load(f)

        def stream():
            with p_stars.open("r") as file:
                for line in file:
                    if line.count("/") == 3:
                        x, y, z, h = line.strip("\n").split("/")
                        yield (float(x), float(y), float(z), UUID(hex=h).int)

        stars = np.array(stream())

        return cls(stars, p_dir, data["uuid"])

    @classmethod
    def generate(cls) -> "Galaxy":
        hex_ = uuid4().hex

        galaxy = generate_galaxy((1.4, 1, 0.2), arms=3)
        print(*(x.shape for x in galaxy))
        stars = np.concatenate(galaxy)

        system_ids = [[uuid4().int] for _ in stars]
        stars = np.concatenate((stars, system_ids), 1)

        return cls(stars, Path("data", hex_), hex_)

    def __init__(self, stars: np.ndarray, gdir: Path, gid: str):
        self.stars = stars
        self.gdir = gdir
        self.gid = gid

    def render(self, *a, **kw):
        render(self.stars[..., :3], *a, **kw)

    def systems_at_coordinate(self, pos: np.ndarray) -> Optional[Domain]:
        t = tuple(x for x in self.stars if x[:3] == pos)
        return t[0] if t else None

    def systems_by_uuid(self, uuid: UUID) -> Optional[Domain]:
        t = tuple(x for x in self.stars if x[3] == uuid.int)
        return t[0] if t else None

    def system_random(self) -> Domain:
        return np.random.choice(self.stars)
