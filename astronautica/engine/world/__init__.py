from pathlib import Path
from typing import Optional, Union
from uuid import UUID, uuid4

import numpy as np
from yaml import safe_dump, safe_load

from ..space.base import Domain
from ..visualizer import render
from .generation import generate_galaxy
from .gravity import MultiSystem, System


DELIM = "|"
LINE = (DELIM.join((*(["{: = 23}"] * 3), "{}")) + "\n").format


class Galaxy(object):
    @classmethod
    def from_file(cls, path: Union[Path, str]) -> "Galaxy":
        path = Path(path)

        if path.is_dir():
            p_dir = path
            p_data = path / "meta.yml"
            p_stars = path / "stars"
        else:
            raise NotADirectoryError(path)

        with p_data.open("r") as f:
            data = safe_load(f)

        def stream():
            with p_stars.open("r") as file:
                for line in file:
                    if line.count(DELIM) == 3:
                        x, y, z, h = line.strip("\n").replace(" ", "").split(DELIM)
                        yield (float(x), float(y), float(z), UUID(hex=h).int)

        stars = np.array(list(stream()))

        return cls(stars, p_dir, data["uuid"])

    @classmethod
    def generate(cls, *a, **kw) -> "Galaxy":
        hex_ = uuid4().hex

        galaxy = generate_galaxy(*a, **kw)
        # print(*(x.shape for x in galaxy))
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

    def save(self, path: Union[Path, str]):
        p_dir = Path(path)
        p_data = p_dir / "meta.yml"
        p_stars = p_dir / "stars"

        if p_dir.exists():
            if not p_dir.is_dir():
                raise NotADirectoryError(path)
        else:
            p_dir.mkdir()

        with p_data.with_suffix(".TMP").open("w") as fd:
            safe_dump({"uuid": self.gid}, fd)
        p_data.with_suffix(".TMP").rename(p_data)

        with p_stars.with_suffix(".TMP").open("w") as fd:
            fd.writelines(LINE(*star[:3], UUID(int=star[3]).hex) for star in self.stars)
        p_stars.with_suffix(".TMP").rename(p_stars)

    def systems_at_coordinate(self, pos: np.ndarray) -> Optional[Domain]:
        t = tuple(x for x in self.stars if x[:3] == pos)
        return t[0] if t else None

    def systems_by_uuid(self, uuid: UUID) -> Optional[Domain]:
        t = tuple(x for x in self.stars if x[3] == uuid.int)
        return t[0] if t else None

    def system_random(self) -> Domain:
        return np.random.choice(self.stars)
