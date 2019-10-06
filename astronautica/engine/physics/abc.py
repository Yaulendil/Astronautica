from abc import ABC, abstractmethod
from typing import Tuple

from vectormath import Vector3


class Clock(ABC):
    @abstractmethod
    def __call__(self) -> float:
        ...


class FrameOfReference(ABC):
    @property
    @abstractmethod
    def position(self) -> Vector3:
        ...

    @property
    @abstractmethod
    def velocity(self) -> Vector3:
        ...

    @property
    @abstractmethod
    def position_pol(self) -> Tuple[float, float, float]:
        ...

    @property
    @abstractmethod
    def velocity_pol(self) -> Tuple[float, float, float]:
        ...

    @property
    @abstractmethod
    def position_cyl(self) -> Tuple[float, float, float]:
        ...

    @property
    @abstractmethod
    def velocity_cyl(self) -> Tuple[float, float, float]:
        ...

    @property
    @abstractmethod
    def id(self) -> int:
        ...

    @abstractmethod
    def as_seen_from(self, pov: "FrameOfReference") -> "FrameOfReference":
        ...
