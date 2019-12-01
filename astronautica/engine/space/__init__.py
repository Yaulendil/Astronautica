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

from itertools import count
from typing import Dict, Iterator, List, Optional, Sequence
from weakref import proxy

from astropy import constants as const
from numba import jit
import numpy as np
from quaternion import as_float_array, from_float_array, quaternion
from vectormath import Vector3

from . import base, position, rotation


__all__ = ["base", "Coordinates", "LocalSpace", "position", "rotation", "Space"]


INITIAL_DOMAINS = 5
INITIAL_OBJECTS = 10


class Space(object):
    """Coordinates tracker/handler object."""

    def __init__(self, struct: dict = None):
        """Initialize positions and velocities to be ndarrays, three dimensions
            deep.

        Top level is "domains", or localities, spaces that are shared between
            objects.
        Second level is objects, this is the axis the index ID of each object
            refers to.
        Bottom level is the three values for X, Y, and Z.
        """
        self.array_position = np.zeros((INITIAL_DOMAINS, INITIAL_OBJECTS, 3))
        self.array_velocity = np.zeros((INITIAL_DOMAINS, INITIAL_OBJECTS, 3))
        self.array_heading = np.zeros((INITIAL_DOMAINS, INITIAL_OBJECTS, 4))
        self.array_rotate = np.zeros((INITIAL_DOMAINS, INITIAL_OBJECTS, 4))

        self.domains: Dict[int, List[int]] = {}

        if struct is not None:
            struct["positions"] = self.array_position
            struct["velocities"] = self.array_velocity

            struct["headings"] = self.array_heading
            struct["rotations"] = self.array_rotate

            struct["domains"] = self.domains

    @property
    def next_domain_index(self) -> int:
        return next(i for i in count() if i not in self.domains)

    @property
    def quat_heading(self) -> np.ndarray:
        return from_float_array(self.array_heading)

    @property
    def quat_rotate(self) -> np.ndarray:
        return from_float_array(self.array_rotate)

    def add_domain(self, domain: "LocalSpace") -> int:
        """Add a new Domain. A Domain is essentially a set of Arrays within the
            Space Arrays which represent a locality in Space. Objects must be in
            the same Domain in order to interact.
        """
        next_domain: int = self.next_domain_index

        # Place a Zero in the ID Dict to represent the new, empty, Domain.
        self.domains[next_domain] = domain.used

        shape = self.array_position.shape
        while next_domain >= shape[0]:
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
            self.array_heading = np.append(
                self.array_heading, np.array([[[0, 0, 0, 0]] * shape[1]]), 0
            )
            self.array_rotate = np.append(
                self.array_rotate, np.array([[[0, 0, 0, 0]] * shape[1]]), 0
            )

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
        while index >= shape[1]:
            # Increase the size of the Array along the Object axis.
            self.array_position = np.append(
                self.array_position, np.array([[[0, 0, 0]]] * shape[0]), 1
            )
            self.array_velocity = np.append(
                self.array_velocity, np.array([[[0, 0, 0]]] * shape[0]), 1
            )
            self.array_heading = np.append(
                self.array_heading, np.array([[[0, 0, 0, 0]]] * shape[0]), 1
            )
            self.array_rotate = np.append(
                self.array_rotate, np.array([[[0, 0, 0, 0]]] * shape[0]), 1
            )

        frame.domain = domain
        return index

    def all_domains(self) -> Iterator["LocalSpace"]:
        for d in LocalSpace.ALL:
            try:
                if d.space is self:
                    yield d
            except:
                continue

    @staticmethod
    def all_frames() -> Iterator["Coordinates"]:
        for f in Coordinates.ALL:
            try:
                if f.domain is not None:
                    yield f
            except:
                continue

    @jit(forceobj=True, nopython=False)
    def progress(self, time: float):
        self.array_position += self.array_velocity * time
        self.array_heading = as_float_array(
            from_float_array(self.array_rotate * np.array((time, 1, 1, 1)))
            * self.quat_heading
        )


class LocalSpace(object):
    ALL: List["LocalSpace"] = []

    def __init__(self, master, space: Space):
        self.master = master
        self.space: Space = space
        self.used: List[int] = []

        self.index: int = self.space.add_domain(self)

        self.ALL.append(proxy(self, self.free_wr))

    @property
    def array_position(self) -> Sequence[Vector3]:
        return self.space.array_position[self.index]

    @array_position.setter
    def array_position(self, value: Sequence[Vector3]) -> None:
        self.space.array_position[self.index] = value

    @property
    def array_velocity(self) -> Sequence[Vector3]:
        return self.space.array_velocity[self.index]

    @array_velocity.setter
    def array_velocity(self, value: Sequence[Vector3]) -> None:
        self.space.array_velocity[self.index] = value

    @property
    def array_heading(self) -> Sequence[np.ndarray]:
        return self.space.array_heading[self.index]

    @array_heading.setter
    def array_heading(self, value: Sequence[np.ndarray]) -> None:
        self.space.array_heading[self.index] = value

    @property
    def array_rotate(self) -> Sequence[np.ndarray]:
        return self.space.array_rotate[self.index]

    @array_rotate.setter
    def array_rotate(self, value: Sequence[np.ndarray]) -> None:
        self.space.array_rotate[self.index] = value

    @property
    def quat_heading(self) -> Sequence[quaternion]:
        return from_float_array(self.array_heading)

    @property
    def quat_rotate(self) -> Sequence[quaternion]:
        return from_float_array(self.array_rotate)

    @property
    def next_object_index(self) -> int:
        return next(i for i in count() if i not in self.used)

    def add_frame(self, frame: "Coordinates", index: int = None) -> int:
        return self.space.add_frame_to_domain(self, frame, index)

    def free(self):
        if self.index in self.space.domain_indices:
            del self.space.domain_indices[self.index]

        self.space = None
        self.used.clear()

    def free_wr(self, prox):
        if prox in self.ALL:
            self.ALL.remove(prox)

        self.free()

    def all_frames(self) -> Iterator["Coordinates"]:
        for f in Coordinates.ALL:
            try:
                if f.domain is self:
                    yield f
            except:
                continue

    @jit(nopython=True)
    def gravitate(self, mass: float):
        self.array_velocity -= np.array(
            np.linalg.norm(vec) * ((const.G * mass) / np.square(vec.length))
            for vec in self.array_position
        )


class Coordinates(object):
    """Coordinates Class: A composite Type allowing any Position Subclass to be
        paired with a Rotation.
    """

    ALL: List["Coordinates"] = []

    def __init__(self, domain: Optional[LocalSpace], add_values: bool = True):
        self.domain: Optional[LocalSpace] = domain

        if domain is not None:
            self.index: int = self.domain.add_frame(self)

            if add_values:
                self._position: base.Position = position.Pointer(
                    self.domain, self.index
                )
                self._rotation: base.Rotation = rotation.Pointer(
                    self.domain, self.index
                )
            else:
                self._position = self._rotation = None

        else:
            self.index: int = -1

        self.ALL.append(proxy(self, self.free_wr))

    @property
    def position(self) -> Vector3:
        return self._position and self._position.position

    @property
    def velocity(self) -> Vector3:
        return self._position and self._position.velocity

    @property
    def heading(self) -> quaternion:
        return self._rotation and self._rotation.heading

    @property
    def rotate(self) -> quaternion:
        return self._rotation and self._rotation.rotate

    def set_posrot(self, pos: base.Position, rot: base.Rotation):
        self._position: base.Position = pos
        self._rotation: base.Rotation = rot

        def dset(newdomain: LocalSpace):
            self.domain = newdomain

        self._position.domain = self._rotation.domain = property(
            (lambda: self.domain), dset
        )

    def free(self):
        if self.index in self.domain.used:
            self.domain.used.remove(self.index)

        self.domain = None
        self.index = -1

    def free_wr(self, prox):
        if prox in self.ALL:
            self.ALL.remove(prox)

        self.free()

    def detach(self):
        self._position = self._position.clone()
        self._rotation = self._rotation.clone()
        self.free()

    def clone(self) -> "Coordinates":
        new = Coordinates(None, False)
        new.set_posrot(self._position.clone(), self._rotation.clone())
        return new

    def as_seen_from(self, pov: "Coordinates") -> "Coordinates":
        """Return a new Coordinates, from the perspective of a given frame of
            reference.
        """
        new = Coordinates(None, False)
        new.set_posrot(
            position.Virtual(
                self._position.position - pov._position.position,
                self._position.velocity - pov._position.velocity,
            ),
            rotation.Virtual(
                self._rotation.heading / pov._rotation.heading,
                self._rotation.rotate / pov._rotation.heading,
            ),
        )
        return new
