from math import degrees, radians
from typing import Tuple, Type, Union

from numba import jit
import numpy as np
from quaternion import quaternion
from vectormath import Vector3


NumpyVector: Type = Union[np.ndarray, Tuple[float, float, float]]
Quat: Type = Union[quaternion, Tuple[float, float, float, float]]


EAST = Vector3(1, 0, 0)
WEST = Vector3(-1, 0, 0)

NORTH = Vector3(0, 1, 0)
SOUTH = Vector3(0, -1, 0)

ZENITH = Vector3(0, 0, 1)
NADIR = Vector3(0, 0, -1)


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
    """Rotate a Vector around a Rotor Quaternion.

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
