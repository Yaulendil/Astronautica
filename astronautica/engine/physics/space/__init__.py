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
from itertools import count
from typing import Dict, List, Optional, Tuple

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
        self.domain_indices: Dict[int, List[int]] = {}
        self.domains: Dict[int, LocalSpace] = {}

    @property
    def next_domain_index(self) -> int:
        return next(i for i in count() if i not in self.domains)

    def add_domain(self, domain: "LocalSpace") -> int:
        """Add a new Domain. A Domain is essentially a set of Arrays within the
            Space Arrays which represent a locality in Space. Objects must be in
            the same Domain in order to interact.
        """
        next_domain: int = len(self.domains)

        # Place a Zero in the ID Dict to represent the new, empty, Domain.
        self.domain_indices[next_domain] = domain.used

        shape = self.array_position.shape
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

    def add_frame_to_domain(
        self, domain: "LocalSpace", frame: "Coordinates", index: int = None
    ) -> int:
        if index is None:
            index = domain.next_object_index
        elif index in domain.used:
            raise IndexError(f"Index {index} is already allocated.")

        domain.used.append(index)

        shape = self.array_position.shape
        if index >= shape[1]:
            # Increase the size of the Array along the Object axis.
            self.array_position = np.append(
                self.array_position, np.array([[[0, 0, 0]]] * shape[0]), 1
            )
            self.array_velocity = np.append(
                self.array_velocity, np.array([[[0, 0, 0]]] * shape[0]), 1
            )

        frame.domain = domain
        return index

    def progress(self, time: float):
        self.array_position += self.array_velocity * time


class LocalSpace(object):
    def __init__(self, master: Domain):
        self.master = master
        self.index: int = -1

        self.add_frame = _nothing
        self.arrays: Optional[Tuple[np.ndarray, np.ndarray]] = None

        self.used: List[int] = []

    @property
    def next_object_index(self) -> int:
        return next(i for i in count() if i not in self.used)

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
