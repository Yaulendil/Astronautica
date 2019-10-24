from pathlib import Path
from secrets import choice
from typing import List, Tuple, Union
from uuid import UUID, uuid4

import numpy as np
from numpy.linalg import norm
from yaml import safe_dump, safe_load

from ..visualizer import render
from .generation import generate_galaxy, generate_system
from .gravity import MultiSystem, System
from config import cfg
from util.storage import PersistentDict


DELIM = "|"
LINE = (DELIM.join((*(["{: = 23}"] * 3), "{}")) + "\n").format


class Galaxy(object):
    @classmethod
    def from_file(cls, path: Union[Path, str]) -> "Galaxy":
        path = Path(path)

        if path.is_dir():
            p_data = path / cfg["data/meta", "meta.yml"]
            p_stars = path / cfg["data/stars", "STARS"]
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
        return cls(stars, path, UUID(hex=data["uuid"]))

    @classmethod
    def generate(cls, *a, name: str = None, **kw) -> "Galaxy":
        uuid = uuid4()

        galaxy = generate_galaxy(*a, **kw)
        # print(*(x.shape for x in galaxy))
        stars = np.concatenate(galaxy)

        system_ids = [[uuid4().int] for _ in stars]
        stars = np.concatenate((stars, system_ids), 1)

        return cls(stars, Path(cfg["data/directory"], name or uuid.hex), uuid)

    def __init__(self, stars: np.ndarray, gdir: Path, gid: UUID):
        self.stars = stars
        self.gdir = gdir
        self.gid = gid

        self.loaded: List[PersistentDict] = []
        self.obj = PersistentDict(
            self.gdir / cfg["data/obj", "objects.json"], fmt="json"
        )

    def ensure(self):
        if self.gdir.exists():
            if not self.gdir.is_dir():
                raise NotADirectoryError(self.gdir)
        else:
            self.gdir.mkdir()

    def load_system(self, uuid: UUID) -> PersistentDict:
        uuid_h = uuid.hex
        uuid_i = uuid.int
        self.ensure()

        if uuid_i in self.stars[..., 3]:
            systems = self.gdir / "systems"
            systems.mkdir(exist_ok=True)
            fp = (systems / uuid_h).with_suffix(".json")

            if fp.exists():
                pd = PersistentDict(fp, fmt="json")
            else:
                pd = PersistentDict(fp, fmt="json")
                pd.update(generate_system())

            self.loaded.append(pd)
            return pd
        else:
            raise FileNotFoundError(f"System {uuid_h!r} not found in Galaxy.")

    def unload_system(self, system: PersistentDict) -> bool:
        if system in self.loaded:
            system.close()
            self.loaded.remove(system)
            return True
        else:
            return False

    def unload_all(self) -> int:
        return sum(x and 1 or 0 for x in map(self.unload_system, self.loaded))

    def render(self, *a, **kw):
        render(self.stars[..., :3], *a, **kw)

    def save(self, path: Union[Path, str] = None) -> Path:
        if path is not None:
            self.gdir = Path(path)

        p_data = self.gdir / cfg["data/meta", "meta.yml"]
        p_stars = self.gdir / cfg["data/stars", "STARS"]
        self.ensure()

        for system in self.loaded:
            system.sync()

        tmp = p_data.with_suffix(".TMP")
        with tmp.open("w") as fd:
            safe_dump({"uuid": self.gid.hex}, fd)
        tmp.rename(p_data)

        tmp = p_stars.with_suffix(".TMP")
        with tmp.open("w") as fd:
            fd.writelines(LINE(*star[:3], UUID(int=star[3]).hex) for star in self.stars)
        tmp.rename(p_stars)

        return self.gdir

    def systems_at_coordinate(
        self, pos: np.ndarray, radius: float = 0
    ) -> Tuple[Tuple[float, float, float, int], ...]:
        return tuple(x for x in self.stars if norm(x[:3] - pos) <= radius)

    def system_by_uuid(self, uuid: UUID) -> Tuple[float, float, float, int]:
        t = tuple(x for x in self.stars if x[3] == uuid.int)
        return t[0] if t else None

    def system_random(self) -> Tuple[float, float, float, int]:
        return choice(self.stars)
