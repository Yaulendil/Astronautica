"""Position Module: Dedicated to simple locations in three-dimensional Space."""

from astropy import units as u
import numpy as np
from vectormath import Vector3

from .base import Position


class Pointer(Position):
    def __init__(self, domain, index: int, *, unit: u.Unit = u.meter):
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

    def __init__(
        self,
        pos: Vector3 = Vector3(0, 0, 0),
        vel: Vector3 = Vector3(0, 0, 0),
        *,
        unit: u.Unit = u.meter,
    ):
        # Physical location.
        self._pos: Vector3 = pos
        # Change in location per second.
        self._vel: Vector3 = vel

        self.domain = None
        self.unit = unit

    @property
    def position(self) -> Vector3:
        return self._pos

    @position.setter
    def position(self, value: np.ndarray):
        self._pos: Vector3 = Vector3(value)

    @property
    def velocity(self) -> Vector3:
        return self._vel

    @velocity.setter
    def velocity(self, value: np.ndarray):
        self._vel: Vector3 = Vector3(value)
