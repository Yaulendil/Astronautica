"""Module implementing Coordinate Systems and Geometric Operations.

Uses NumPy Arrays for storage of Coordinates, by way of third-party Vector3 and
    Quaternion subclasses.
Uses Numba for JIT Compilation.
"""

from math import radians, degrees
from typing import Dict, Tuple, Type, Union

from astropy import units as u
from numba import jit
import numpy as np
from quaternion import quaternion
from vectormath import Vector3

__all__ = [
    "to_spherical",
    "from_spherical",
    "to_cylindrical",
    "from_cylindrical",
    "Coordinates",
    "Space",
]


NumpyVector: Type = Union[np.ndarray, Tuple[float, float, float]]
Quat: Type = Union[quaternion, Tuple[float, float, float, float]]


# Spherical Coordinates:
# Physics conventions: +θ = North of East from 0° to 360°, +φ = Down from Zenith
#   # North: θ = 90°
#   # South: θ = 270°
#   # Zenith: φ = 0°
# Navigational format: +θ = West of South from -180° to 180°, +φ = Up from Horizon
#   # North: θ = 0°
#   # South: θ = -180° OR 180°
#   # Zenith: φ = 90°


###===---
# COORDINATE TRANSFORMATIONS
###===---


@jit(nopython=True)
def to_spherical(x: float, y: float, z: float) -> Tuple[float, float, float]:
    """Convert three-dimensional Cartesian Coordinates to Spherical."""
    rho = np.sqrt(np.sum(np.square(np.array((x, y, z)))))
    theta = 90 - degrees(np.arccos(z / rho)) if rho else 0
    phi = (
        0
        if theta == 90 or theta == -90
        else (270 - degrees(np.arctan2(y, x))) % 360 - 180
    )
    return rho, theta, phi


@jit(nopython=True)
def from_spherical(rho: float, theta: float, phi: float) -> Tuple[float, float, float]:
    """Convert three-dimensional Spherical Coordinates to Cartesian."""
    theta = np.pi / 2 - radians(theta)
    phi_ = radians(phi)
    y = rho * np.cos(phi_) * np.sin(theta)
    x = rho * np.sin(phi_) * np.sin(theta)
    z = rho * np.cos(theta)
    return x, y, z


@jit(nopython=True)
def to_cylindrical(x: float, y: float, z: float) -> Tuple[float, float, float]:
    """Convert three-dimensional Cartesian Coordinates to Cylindrical."""
    rho = np.sqrt(np.sum(np.square(np.array((x, y)))))
    phi = np.arctan2(y, x)
    return rho, phi, z


@jit(nopython=True)
def from_cylindrical(rho: float, phi: float, z: float) -> Tuple[float, float, float]:
    """Convert three-dimensional Cylindrical Coordinates to Cartesian."""
    phi_ = radians(phi)
    x = rho * np.cos(phi_)
    y = rho * np.sin(phi_)
    return x, y, z


###===---
# QUATERNION FUNCTIONS
# Huge thanks to aeroeng15 for help with this.
# Quaternions are the best and also worst.
###===---


@jit(nopython=True)
def get_rotor(theta: float, axis: Vector3) -> quaternion:
    """Return a Unit Quaternion which will rotate a Heading by Theta about Axis.
    """
    q = quaternion(
        np.cos(theta / 2), *(v * np.sin(theta / 2) for v in axis)
    ).normalized()
    return q


@jit(nopython=True)
def break_rotor(q: quaternion) -> Tuple[float, Vector3]:
    """Given a Unit Quaternion, break it into an angle and a Vector3."""
    theta, v = 2 * np.arccos(q.w), []
    axis = Vector3(*v)
    return theta, axis


@jit(nopython=True)
def rotate_vector(vector: Vector3, rotor: quaternion) -> Vector3:
    """
    p' = q*p*(q^-1)
    https://en.wikipedia.org/wiki/Quaternions_and_spatial_rotation
    """
    p = quaternion(0, *vector)
    qvec = rotor * p * rotor.inverse()
    vector_out = Vector3(*[round(x, 3) for x in qvec.vec])
    return vector_out


@jit(nopython=True)
def facing(quat) -> Vector3:
    """Given a Unit Quaternion, return the Unit Vector of its direction."""
    return rotate_vector(Vector3(0, 1, 0), quat)


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


class Coordinates:
    """Coordinates object: Store information as Vector3 and Quaternions and
        return transformations as requested.
    """

    def __init__(
        self,
        pos: NumpyVector = (0, 0, 0),
        vel: NumpyVector = (0, 0, 0),
        aim: Quat = (1, 0, 0, 0),
        rot: Quat = (1, 0, 0, 0),
        *,
        domain: int = 0,
        space: Space,
        unit: u.Unit = u.meter,
    ):
        pos = (
            pos if isinstance(pos, np.ndarray) else np.array(pos)
        )  # Physical location.
        vel = (
            vel if isinstance(vel, np.ndarray) else np.array(vel)
        )  # Change in location per second.

        self.heading = (
            aim if isinstance(aim, quaternion) else quaternion(*aim)
        )  # Orientation.
        self.rotate = (
            rot if isinstance(rot, quaternion) else quaternion(*rot)
        )  # Spin per second.
        self._id: Dict[int, int] = {}

        self.space = space
        self.domain = domain
        self.unit = unit

        self._id[self.domain] = self.space.register_coordinates(self, pos, vel)

    @property
    def position(self) -> Vector3:
        """Go into the relevant Space structure and retrieve the Position that
            is assigned to this FoR, and wrap it in a Vector3.
        """
        return Vector3(self.space.array_position[self.domain][self.id])

    @position.setter
    def position(self, v: np.ndarray):
        """Transparently change the value of the Position assigned to this FoR.

        If a Scalar is given, all values of the Array will be that value.
        """
        self.space.array_position[self.domain][self.id] = v

    @property
    def velocity(self) -> Vector3:
        """Go into the relevant Space structure and retrieve the Velocity that
            is assigned to this FoR, and wrap it in a Vector3.
        """
        return Vector3(self.space.array_velocity[self.domain][self.id])

    @velocity.setter
    def velocity(self, v: np.ndarray):
        """Transparently change the value of the Velocity assigned to this FoR.

        If a Scalar is given, all values of the Array will be that value.
        """
        self.space.array_velocity[self.domain][self.id] = v

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

    @property
    def id(self) -> int:
        return self._id[self.domain]

    @id.setter
    def id(self, v: int):
        self._id[self.domain] = v

    def as_seen_from(self, pov: "Coordinates") -> "Coordinates":
        """Return a new Coordinates, from the perspective a given frame of
            reference.
        """
        return Coordinates(
            self.position - pov.position,
            self.velocity - pov.velocity,
            self.heading / pov.heading,
            self.rotate / pov.heading,
            domain=self.domain,
            space=self.space,
        )

    def increment(self, seconds: float):
        self.increment_rotation(seconds)
        self.increment_position(seconds)

    def increment_rotation(self, seconds: float):
        theta, vec = break_rotor(self.rotate)
        theta *= seconds
        rotate = get_rotor(theta, vec)
        self.heading = rotate * self.heading

    def increment_position(self, seconds: float):
        self.position += self.velocity * seconds

    def serialize(self):
        flat = {
            "type": type(self).__name__,
            "data": {
                "pos": list(self.position),
                "vel": list(self.velocity),
                "hea": [self.heading.w, *self.heading.vec],
                "rot": [self.rotate.w, *self.rotate.vec],
                "domain": self.domain,
            },
        }
        return flat
