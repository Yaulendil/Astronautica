"""Position Module: Dedicated to locations in three-dimensional Space."""

from abc import ABC
from typing import Tuple

from astropy import units as u
import numpy as np
from vectormath import Vector3

from .base import Clock, FrameOfReference
from .geometry import NumpyVector, to_cylindrical, to_spherical


class Position(FrameOfReference, ABC):
    """Position object: Track information as Vector3 and return transformations
        as requested.
    """

    @property
    def position_pol(self) -> Tuple[float, float, float]:
        """Return the Position of this FoR in Spherical Coordinates."""
        return to_spherical(*self.position)

    @property
    def velocity_pol(self) -> Tuple[float, float, float]:
        """Return the Velocity of this FoR in Spherical Coordinates."""
        return to_spherical(*self.velocity)

    @property
    def position_cyl(self) -> Tuple[float, float, float]:
        """Return the Position of this FoR in Cylindrical Coordinates."""
        return to_cylindrical(*self.position)

    @property
    def velocity_cyl(self) -> Tuple[float, float, float]:
        """Return the Velocity of this FoR in Cylindrical Coordinates."""
        return to_cylindrical(*self.velocity)

    @property
    def speed(self) -> float:
        return self.velocity.length

    def serialize(self):
        flat = {
            "type": type(self).__name__,
            "data": {
                "pos": list(self.position),
                "vel": list(self.velocity),
                "domain": self.domain,
            },
        }
        return flat


class Pointer(Position):
    def __init__(
        self,
        domain,
        index: int,
        *,
        unit: u.Unit = u.meter,
    ):
        self.domain = domain
        self.index: int = index
        self.unit = unit

    @property
    def position(self) -> Vector3:
        """Go into the relevant Space structure and retrieve the Position that
            is assigned to this FoR, and wrap it in a Vector3.
        """
        return Vector3(self.domain.array_position[self.index])

    @position.setter
    def position(self, v: np.ndarray):
        """Transparently change the value of the Position assigned to this FoR.

        If a Scalar is given, all values of the Array will be that value.
        """
        self.domain.array_position[self.index] = v

    @property
    def velocity(self) -> Vector3:
        """Go into the relevant Space structure and retrieve the Velocity that
            is assigned to this FoR, and wrap it in a Vector3.
        """
        return Vector3(self.domain.array_velocity[self.index])

    @velocity.setter
    def velocity(self, v: np.ndarray):
        """Transparently change the value of the Velocity assigned to this FoR.

        If a Scalar is given, all values of the Array will be that value.
        """
        self.domain.array_velocity[self.index] = v


class Virtual(Position):
    """Virtual Position object: Track information as Vector3 and return
        transformations as requested, WITHOUT registering into a Space.
    """

    # noinspection PyMissingConstructor
    def __init__(
        self,
        pos: NumpyVector = (0, 0, 0),
        vel: NumpyVector = (0, 0, 0),
        *,
        unit: u.Unit = u.meter,
    ):
        self.position = Vector3(
            pos if isinstance(pos, np.ndarray) else np.array(pos)
        )  # Physical location.
        self.velocity = Vector3(
            vel if isinstance(vel, np.ndarray) else np.array(vel)
        )  # Change in location per second.

        self.domain = None
        self.space = None
        self.unit = unit

        self.id = None

    @property
    def position(self) -> Vector3:
        return self._pos

    @position.setter
    def position(self, v: np.ndarray):
        self._pos = Vector3(v)

    @property
    def velocity(self) -> Vector3:
        return self._vel

    @velocity.setter
    def velocity(self, v: np.ndarray):
        self._vel = Vector3(v)


class Orbit(FrameOfReference):
    """A Relative Frame of Reference which is based on a Primary, whose real
        position is a function of Time.
    """

    # TODO

    __slots__ = ("offset", "primary", "radius", "time")

    def __init__(
        self,
        primary: FrameOfReference,
        radius: float,
        time: Clock,
        unit: u.Unit = u.meter,
        *,
        offset: float = 0,
    ):
        self.primary = primary
        self.radius = radius
        self.time = time

        self.offset = offset

        self.domain = self.primary.domain
        self.space = self.primary.space
        self.unit = unit

    @property
    def position(self) -> Vector3:
        pass

    @property
    def velocity(self) -> Vector3:
        pass

    @property
    def position_pol(self) -> Tuple[float, float, float]:
        pass

    @property
    def velocity_pol(self) -> Tuple[float, float, float]:
        pass

    @property
    def position_cyl(self) -> Tuple[float, float, float]:
        pass

    @property
    def velocity_cyl(self) -> Tuple[float, float, float]:
        pass

    @property
    def id(self) -> int:
        pass


class Lagrangian(FrameOfReference):
    """A Relative Frame of Reference which is based on an Orbit; The five
        Lagrangian Points are the points relative to an Orbiting Body at which
        a Body can maintain a stable secondary Orbit.
    """

    # TODO: Return Real values relative to Leader as appropriate for Point.

    def __init__(self, leader: Orbit, point: int):
        self.leader: Orbit = leader
        self.point: int = point
        self.real: Orbit = Orbit(
            self.leader.primary,
            self.leader.radius,
            self.leader.time,
            self.leader.unit,
            offset=self.leader.offset,
        )

    @property
    def position(self) -> Vector3:
        return self.real.position

    @property
    def velocity(self) -> Vector3:
        return self.real.velocity

    @property
    def position_pol(self) -> Tuple[float, float, float]:
        return self.real.position_pol

    @property
    def velocity_pol(self) -> Tuple[float, float, float]:
        return self.real.velocity_pol

    @property
    def position_cyl(self) -> Tuple[float, float, float]:
        return self.real.position_cyl

    @property
    def velocity_cyl(self) -> Tuple[float, float, float]:
        return self.real.velocity_cyl

    @property
    def id(self) -> int:
        return self.real.id
