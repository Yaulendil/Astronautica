from abc import ABC, abstractmethod
from pathlib import Path

from ..serial import deserialize
from .generation import generate_system

from util.storage import PersistentDict


class Clock(ABC):
    @abstractmethod
    def __call__(self) -> float:
        ...


class Body(object):
    ...


class SystemHandler(object):
    def __init__(self, filepath: Path):
        self.path = filepath
        _load = self.path.exists()

        self.data = PersistentDict(self.path, fmt="json")

        if _load:
            self.system = deserialize(self.data)
        else:
            self.system = generate_system(self.data)

    def serialize(self):
        return dict(type=type(self).__name__)

    def sync(self):
        self.data.update(self.serialize())
        self.data.sync()
