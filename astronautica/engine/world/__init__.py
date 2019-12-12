from pathlib import Path
from secrets import choice
from typing import Dict, Optional, Tuple, Union
from uuid import UUID, uuid4

import numpy as np
from numpy.linalg import norm
from yaml import safe_dump, safe_load

from ..rendering import render_galaxy
from ..serial import deserialize
from .base import Clock
from .generation import generate_galaxy, generate_system
from .gravity import MultiSystem, System
from config import cfg
from util.storage import PersistentDict


DELIM = "|"
LINE = (DELIM.join((*(["{: = 23}"] * 3), "{}")) + "\n").format


class SystemHandler(object):
    __slots__ = (
        "data",
        "path",
        "system",
        "uuid",
    )

    def __init__(self, filepath: Path, dat: Tuple[float, float, float, int]):
        self.path = filepath
        _load = self.path.exists()

        self.data = PersistentDict(self.path, fmt="json")
        self.uuid = dat[3]

        if _load:
            self.system = deserialize(self.data)
        else:
            self.system = generate_system(self.data)

    def serialize(self):
        return dict(type=type(self).__name__)

    def sync(self):
        self.data.update(self.serialize())
        self.data.sync()


class Galaxy(object):
    __slots__ = (
        "gdir",
        "gid",
        "loaded",
        "obj",
        "stars",
    )

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
                        yield float(x), float(y), float(z), UUID(hex=h).int

        stars = np.array(list(stream()))
        return cls(stars, path, UUID(hex=data["uuid"]))

    @classmethod
    def generate(cls, *a, name: str = None, **kw) -> "Galaxy":
        uuid = uuid4()

        stars = np.concatenate(generate_galaxy(*a, **kw))
        stars = np.concatenate((stars, [[uuid4().int] for _ in stars]), 1)

        return cls(stars, Path(cfg["data/directory"], "world", name or uuid.hex), uuid)

    def __init__(self, stars: np.ndarray, gdir: Path, gid: UUID):
        self.stars = stars
        self.gdir = gdir
        self.gid = gid

        self.loaded: Dict[int, SystemHandler] = {}
        self.obj = PersistentDict(
            self.gdir / cfg["data/obj", "objects.json"], fmt="json"
        )

    def ensure(self):
        if self.gdir.exists():
            if not self.gdir.is_dir():
                raise NotADirectoryError(self.gdir)
        else:
            self.gdir.mkdir()

    def get_system(self, uuid: UUID) -> SystemHandler:
        """Retrieve a Star System by its UUID. If the System does not exist,
            procedurally generate it on the fly.
        """
        uuid_h = uuid.hex
        uuid_i = uuid.int
        self.ensure()

        if uuid_i in self.loaded:
            return self.loaded[uuid_i]

        dat = self.system_by_uuid(uuid)

        if dat:
            systems = self.gdir / "systems"
            systems.mkdir(exist_ok=True)
            fp = (systems / uuid_h).with_suffix(".json")

            system = SystemHandler(fp, dat)

            self.loaded[uuid_i] = system
            return system
        else:
            raise FileNotFoundError(f"System {uuid_h!r} not found in Galaxy.")

    def unload_system(self, system: SystemHandler) -> bool:
        if system.uuid in self.loaded:
            system.sync()
            del self.loaded[system.uuid]
            return True
        else:
            return False

    def unload_all(self) -> int:
        return sum(1 for x in map(self.unload_system, self.loaded.values()) if x)

    def render(self, *a, **kw):
        render_galaxy(self.stars[..., :3], *a, **kw)

    def rename(self, target: Path):
        if not target.exists():
            if self.gdir.exists():
                self.gdir.rename(target)
            self.gdir = target
        else:
            raise FileExistsError(target)

    def save(self):
        p_data = self.gdir / cfg["data/meta", "meta.yml"]
        p_stars = self.gdir / cfg["data/stars", "STARS"]
        self.ensure()

        for system in self.loaded.values():
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

    def systems_at(
        self, pos: np.ndarray, radius: float = 0
    ) -> Tuple[Tuple[float, float, float, int], ...]:
        return tuple(x for x in self.stars if norm(x[:3] - pos) <= radius)

    def system_by_uuid(self, uuid: UUID) -> Optional[Tuple[float, float, float, int]]:
        # Find Indices of all Stars with a matching UUID.
        indices = np.where(self.stars[..., 3] == uuid.int)[0].tolist()
        if indices:
            # Return the Data at the first Index.
            return tuple(self.stars[indices[0]].tolist())
        else:
            return None

    def system_random(self) -> Tuple[float, float, float, int]:
        return choice(self.stars)
