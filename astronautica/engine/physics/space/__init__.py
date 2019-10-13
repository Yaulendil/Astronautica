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
from functools import partial, wraps
from typing import Dict, Optional, Tuple

import numpy as np

from .geometry import NumpyVector, Quat
from .position import Position, Virtual
from .rotation import Rotation
from _abc import Clock, Domain, FrameOfReference, Node


__all__ = ["Clock", "Coordinates", "FrameOfReference", "LocalSpace", "Node", "Space"]


def _nothing(*_, **__):
    pass


class Space(object):
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
        self.domain_sizes: Dict[int, int] = {}
        self.domains: Dict[int, LocalSpace] = {}

    def register_coordinates(self, coords, newpos, newvel) -> int:
        """DEPRECATED"""
        # Register coordinates and return ID number with which to retrieve them
        next_domain: int = len(self.domain_sizes)
        shape = self.array_position.shape

        if coords.domain > next_domain < -1:
            # Domain number is too high, cannot make
            raise IndexError("Cannot make new domain <0 or higher than next index")

        elif coords.domain in (next_domain, -1):
            # New domain needs to be made
            new_id = 0
            self.domain_sizes[next_domain] = 1
            addition = np.array([[[0, 0, 0]] * shape[1]])
            if next_domain >= shape[0]:
                # Increase the size of the arrays along the Domain axis
                self.array_position = np.append(self.array_position, addition, 0)
                self.array_velocity = np.append(self.array_velocity, addition, 0)
        else:
            # Not a new domain, but a new index in the domain
            new_id: int = self.domain_sizes[coords.domain]
            self.domain_sizes[coords.domain] += 1

            if new_id >= shape[1]:
                # Increase the size of the arrays along the Index axis
                addition = np.array([[[0, 0, 0]]] * shape[0])
                self.array_position = np.append(self.array_position, addition, 1)
                self.array_velocity = np.append(self.array_velocity, addition, 1)

        self.set_coordinates(coords.domain, new_id, newpos, newvel)
        return new_id

    def add_domain(self, domain: "LocalSpace") -> int:
        """Add a new Domain. A Domain is essentially a set of Arrays within the
            Space Arrays which represent a locality in Space. Objects must be in
            the same Domain in order to interact.
        """
        next_domain: int = len(self.domains)
        shape = self.array_position.shape

        # Place a Zero in the ID Dict to represent the new, empty, Domain.
        self.domain_sizes[next_domain] = 0

        if next_domain >= shape[0]:
            # The Index of the new Domain is higher than the number of Arrays
            #   available. Increase the size of the Array along the Domain axis.
            #   To this end, initialize new Arrays of X Arrays of three Zeros,
            #   where X is the number of Object Slots required in the new Domain
            #   to maintain Shape.
            self.array_position = np.append(
                self.array_position, np.array([[[0, 0, 0]] * shape[1]]), 0
            )
            self.array_velocity = np.append(
                self.array_velocity, np.array([[[0, 0, 0]] * shape[1]]), 0
            )

        domain.set_space(self, next_domain)
        return next_domain

    def add_frame_to_domain(self, domain: "LocalSpace", frame: FrameOfReference) -> int:
        shape = self.array_position.shape

        # Not a new domain, but a new index in the domain
        next_id: int = domain.get_next_index()
        self.domain_sizes[frame.domain] += 1

        if next_id >= shape[1]:
            # Increase the size of the Array along the Object axis.
            self.array_position = np.append(
                self.array_position, np.array([[[0, 0, 0]]] * shape[0]), 1
            )
            self.array_velocity = np.append(
                self.array_velocity, np.array([[[0, 0, 0]]] * shape[0]), 1
            )

        return next_id

    def get_coordinates(self, domain: int, index: int) -> Tuple[np.ndarray, np.ndarray]:
        """DEPRECATED"""
        return self.array_position[domain][index], self.array_velocity[domain][index]

    def set_coordinates(
        self, domain: int, index: int, pos: np.ndarray = None, vel: np.ndarray = None
    ):
        """DEPRECATED"""
        if pos is not None:
            self.array_position[domain][index] = pos
        if vel is not None:
            self.array_velocity[domain][index] = vel

    def progress(self, time: float):
        self.array_position += self.array_velocity * time


class LocalSpace(object):
    def __init__(self, master: Domain):
        self.master = master
        self.index: int = -1

        self.add_frame = _nothing
        self.arrays: Optional[Tuple[np.ndarray, np.ndarray]] = None

    def needs_space(self, meth):
        """Decorate a Method so that it raises an Exception if the Instance has
            not been assigned to a Space Instance.
        """

        @wraps(meth)
        def wrapper(*a, **kw):
            if self.arrays is None:
                raise IndexError("LocalSpace Object not assigned a Space")
            else:
                return meth(*a, **kw)

        return wrapper

    def set_space(self, space: Space, index: int) -> None:
        self.index = index

        self.add_frame = partial(space.add_frame_to_domain, self)
        self.arrays: Tuple[np.ndarray, np.ndarray] = (
            space.array_position[self.index],
            space.array_velocity[self.index],
        )

    def get_next_index(self) -> int:
        ...


class Coordinates(object):
    """Coordinates Class: A composite Type allowing any FoR Subclass to be
        paired with a Rotation.
    """

    def __init__(self, pos: FrameOfReference, rot: Rotation, domain: LocalSpace):
        self._position: FrameOfReference = pos
        self._rotation: Rotation = rot
        self.domain = domain

    @classmethod
    def new(
        cls,
        pos: NumpyVector,
        vel: NumpyVector,
        aim: Quat,
        rot: Quat,
        domain: LocalSpace,
    ) -> "Coordinates":
        if domain is None:
            _pos = Virtual(pos, vel)
        else:
            _pos = Position(pos, vel, domain=domain)
        _rot = Rotation(aim, rot)

        return cls(_pos, _rot, domain)

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
