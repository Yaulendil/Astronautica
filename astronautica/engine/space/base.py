from abc import ABC, abstractmethod
from typing import Tuple

from quaternion import quaternion
from vectormath import Vector3

from .geometry import from_cylindrical, from_spherical, to_cylindrical, to_spherical


class Position(ABC):
    __slots__ = ("domain", "unit")

    @property
    @abstractmethod
    def position(self) -> Vector3:
        ...

    @position.setter
    @abstractmethod
    def position(self, value: Vector3) -> None:
        ...

    @property
    @abstractmethod
    def velocity(self) -> Vector3:
        ...

    @velocity.setter
    @abstractmethod
    def velocity(self, value: Vector3) -> None:
        ...

    @property
    def position_pol(self) -> Tuple[float, float, float]:
        """Return the Position of this FoR in Spherical Coordinates."""
        return to_spherical(*self.position)

    @position_pol.setter
    def position_pol(self, value: Tuple[float, float, float]) -> None:
        """Return the Position of this FoR in Spherical Coordinates."""
        self.position = from_spherical(*value)

    @property
    def velocity_pol(self) -> Tuple[float, float, float]:
        """Return the Velocity of this FoR in Spherical Coordinates."""
        return to_spherical(*self.velocity)

    @velocity_pol.setter
    def velocity_pol(self, value: Tuple[float, float, float]) -> None:
        """Return the Velocity of this FoR in Spherical Coordinates."""
        self.velocity = from_spherical(*value)

    @property
    def position_cyl(self) -> Tuple[float, float, float]:
        """Return the Position of this FoR in Cylindrical Coordinates."""
        return to_cylindrical(*self.position)

    @position_cyl.setter
    def position_cyl(self, value: Tuple[float, float, float]) -> None:
        """Return the Position of this FoR in Cylindrical Coordinates."""
        self.position = from_cylindrical(*value)

    @property
    def velocity_cyl(self) -> Tuple[float, float, float]:
        """Return the Velocity of this FoR in Cylindrical Coordinates."""
        return to_cylindrical(*self.velocity)

    @velocity_cyl.setter
    def velocity_cyl(self, value: Tuple[float, float, float]) -> None:
        """Return the Velocity of this FoR in Cylindrical Coordinates."""
        self.velocity = from_cylindrical(*value)

    @property
    def speed(self) -> float:
        return self.velocity.length

    def serialize(self):
        flat = {
            "type": type(self).__name__,
            "data": {
                "pos": list(self.position),
                "vel": list(self.velocity),
            },
        }
        return flat


class Rotation(ABC):
    @property
    @abstractmethod
    def heading(self) -> quaternion:
        ...

    @heading.setter
    @abstractmethod
    def heading(self, value: quaternion) -> None:
        ...

    @property
    @abstractmethod
    def rotate(self) -> quaternion:
        ...

    @rotate.setter
    @abstractmethod
    def rotate(self, value: quaternion) -> None:
        ...

    def serialize(self):
        flat = {
            "type": type(self).__name__,
            "data": {
                "hdg": list(self.heading),
                "rot": list(self.rotate),
            },
        }
        return flat
