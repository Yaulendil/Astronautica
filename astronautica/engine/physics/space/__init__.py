"""Module implementing Coordinate Systems and Geometric Operations.

Uses NumPy Arrays for storage of Coordinates, by way of third-party Vector3 and
    Quaternion subclasses.
Uses Numba for JIT Compilation.


Spherical Coordinates:
    Physics conventions: +θ = North of East from 0° to 360°, +φ = Down from Zenith
      North: θ = 90°
      South: θ = 270°
      Zenith: φ = 0°
    Navigational format: +θ = West of South from -180° to 180°, +φ = Up from Horizon
      North: θ = 0°
      South: θ = -180° OR 180°
      Zenith: φ = 90°
"""

from typing import Dict, Tuple

import numpy as np

from .geometry import NumpyVector, Quat
from .position import Position, Virtual
from .rotation import Rotation
from _abc import Clock, Domain, FrameOfReference, Node


__all__ = ["Clock", "Coordinates", "Domain", "FrameOfReference", "Node", "Space"]


class Space:
    """Coordinates tracker/handler object."""

    def __init__(self):
        """Initialize positions and velocities to be ndarrays, three dimensions
            deep.

        Top level is "domains", or localities, spaces that are shared between
            objects.
        Second level is objects, this is the axis the index ID of each object
            refers to.
        Bottom level is the three values for X, Y, and Z.
        """
        self.array_position = np.ndarray((1, 1, 3))
        self.array_velocity = np.ndarray((1, 1, 3))
        self.next_id: Dict[int, int] = {0: 0}

    def register_coordinates(self, coords, newpos, newvel) -> int:
        # Register coordinates and return ID number with which to retrieve them
        next_domain: int = len(self.next_id)
        shape = self.array_position.shape

        if coords.domain > next_domain < -1:
            # Domain number is too high, cannot make
            raise IndexError("Cannot make new domain <0 or higher than next index")

        elif coords.domain in (next_domain, -1):
            # New domain needs to be made
            new_id = 0
            self.next_id[next_domain] = 1
            addition = np.array([[[0, 0, 0]] * shape[1]])
            if next_domain >= shape[0]:
                # Increase the size of the arrays along the Domain axis
                self.array_position = np.append(self.array_position, addition, 0)
                self.array_velocity = np.append(self.array_velocity, addition, 0)
        else:
            # Not a new domain, but a new index in the domain
            new_id: int = self.next_id[coords.domain]
            self.next_id[coords.domain] += 1

            if new_id >= shape[1]:
                # Increase the size of the arrays along the Index axis
                addition = np.array([[[0, 0, 0]]] * shape[0])
                self.array_position = np.append(self.array_position, addition, 1)
                self.array_velocity = np.append(self.array_velocity, addition, 1)

        self.set_coordinates(coords.domain, new_id, newpos, newvel)
        return new_id

    def get_coordinates(self, domain: int, index: int) -> Tuple[np.ndarray, np.ndarray]:
        return self.array_position[domain][index], self.array_velocity[domain][index]

    def set_coordinates(
        self, domain: int, index: int, pos: np.ndarray = None, vel: np.ndarray = None
    ):
        if pos is not None:
            self.array_position[domain][index] = pos
        if vel is not None:
            self.array_velocity[domain][index] = vel

    def add_coordinates(
        self, domain: int, index: int, pos: np.ndarray = None, vel: np.ndarray = None
    ):
        if pos is not None:
            self.array_position[domain][index] += pos
        if vel is not None:
            self.array_velocity[domain][index] += vel

    def progress(self, time: float):
        self.array_position += self.array_velocity * time


class Coordinates(object):
    """Coordinates Class: A composite Type allowing any FoR Subclass to be
        paired with a Rotation.
    """

    def __init__(self, pos: FrameOfReference, rot: Rotation, space: Space):
        self._position: FrameOfReference = pos
        self._rotation: Rotation = rot
        self.space = space

    @classmethod
    def new(
        cls,
        pos: NumpyVector,
        vel: NumpyVector,
        aim: Quat,
        rot: Quat,
        domain: int,
        space: Space,
    ) -> "Coordinates":
        if space is None:
            _pos = Virtual(pos, vel)
        else:
            _pos = Position(pos, vel, domain=domain, space=space)
        _rot = Rotation(aim, rot)

        return cls(_pos, _rot, space)

    @property
    def domain(self) -> int:
        return self._position.domain

    @domain.setter
    def domain(self, value: int):
        self._position.domain = value

    def increment_rotation(self, sec: float):
        self._rotation.increment(sec)

    def as_seen_from(self, pov: "Coordinates") -> "Coordinates":
        """Return a new Coordinates, from the perspective of a given frame of
            reference.
        """
        return type(self)(
            Virtual(
                self._position.position - pov._position.position,
                self._position.velocity - pov._position.velocity,
            ),
            Rotation(
                self._rotation.heading / pov._rotation.heading,
                self._rotation.rotate / pov._rotation.heading,
            ),
            None,
        )
