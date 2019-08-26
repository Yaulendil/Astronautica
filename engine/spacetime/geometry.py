from math import radians, degrees, isnan
from typing import Dict, List, Tuple, Type, TypeVar, Union

from numba import jit
import numpy as np
from quaternion import quaternion
from vectormath import Vector3


all_space = None
N = TypeVar("N", float, int)
NumpyVector: Type = Union[np.ndarray, Tuple[N, N, N]]
Quat: Type = Union[quaternion, Tuple[N, N, N, N]]


###===---
# COORDINATE TRANSFORMATIONS
###===---


# noinspection NonAsciiCharacters
@jit
def polar_convert(ρ: N, θ: N, φ: N) -> Tuple[N, N, N]:
    """Given polar coordinates in the conventions of Physics, convert to
        conventions of Navigation.
    """
    # Physics conventions: +θ = North of East from 0° to 360°, +φ = Down from Zenith
    #   # North: θ = 90°
    #   # South: θ = 270°
    #   # Zenith: φ = 0°
    # Navigational format: +θ = West of South from -180° to 180°, +φ = Up from Horizon
    #   # North: θ = 0°
    #   # South: θ = -180° OR 180°
    #   # Zenith: φ = 90°

    θ = 180 - ((90 + θ) % 360)
    φ = 90 - φ
    if φ == 90 or φ == -90:
        θ = 0
    return ρ, θ, φ


@jit
def rad_deg(theta: N) -> N:
    """Convert Radians to Degrees."""
    return np.round(degrees(theta), 5)


@jit
def deg_rad(theta: N) -> N:
    """Convert Degrees to Radians."""
    return np.round(radians(theta), 5)


@jit
def cart2_polar2(x: N, y: N) -> Tuple[N, N]:
    """Convert two-dimensional Cartesian Coordinates to Polar."""
    rho = np.sqrt(x ** 2 + y ** 2)
    phi = np.pi / 2 - np.arctan2(y, x)
    return rho, phi


@jit
def polar2_cart2(rho: N, phi: N) -> Tuple[N, N]:
    """Convert two-dimensional Polar Coordinates to Cartesian."""
    x = rho * np.cos(phi)
    y = rho * np.sin(phi)
    return x, y


# noinspection NonAsciiCharacters
@jit
def cart3_polar3(x: N, y: N, z: N) -> Tuple[N, N, N]:
    """Convert three-dimensional Cartesian Coordinates to Polar."""
    ρ = np.sqrt(x ** 2 + y ** 2 + z ** 2)
    φ = rad_deg(np.arccos(z / ρ))
    θ = rad_deg(np.arctan2(y, x))
    return polar_convert(ρ, θ, φ)


# noinspection NonAsciiCharacters
@jit
def polar3_cart3(ρ: N, θ: N, φ: N) -> Tuple[N, N, N]:
    """Convert three-dimensional Polar Coordinates to Cartesian."""
    θ = np.pi / 2 - deg_rad(θ)
    φ = deg_rad(φ)
    z = ρ * np.cos(φ) * np.sin(θ)
    x = ρ * np.sin(φ) * np.sin(θ)
    y = ρ * np.cos(θ)
    return x, y, z


@jit
def cyl3_cart3(rho: N, theta: N, y: N) -> Tuple[N, N, N]:
    """Convert three-dimensional Cylindrical Coordinates to Cartesian."""
    # y = cyl[2]
    z, x = polar2_cart2(rho, deg_rad(theta))
    return x, y, z


###===---
# QUATERNION FUNCTIONS
# Huge thanks to aeroeng15 for help with this.
# Quaternions are the best and also worst.
###===---


def get_rotor(theta: float, axis: Vector3) -> quaternion:
    """Return a Unit Quaternion which will rotate a Heading by Theta about Axis.
    """
    q = quaternion(
        np.cos(theta / 2), *[v * np.sin(theta / 2) for v in axis]
    ).normalized()
    return q


def break_rotor(q: quaternion) -> Tuple[N, N]:
    """Given a Unit Quaternion, break it into an angle and a Vector3."""
    theta, v = 2 * np.arccos(q.w), []
    axis = Vector3(*v)
    return theta, axis


def rotate_vector(vector: Vector3, rotor: quaternion) -> Vector3:
    """
    p' = q*p*(q^-1)
    https://en.wikipedia.org/wiki/Quaternions_and_spatial_rotation
    """
    p = quaternion(0, *vector)
    qvec = rotor * p * rotor.inverse()
    vector_out = Vector3(*[round(x, 3) for x in qvec.vec])
    return vector_out


def facing(quat):
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
        self.next_id: Dict[int, int] = {
            0: 0
        }  # Keep track of values assigned per domain here

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
        priv: bool = False,
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

        global all_space

        if priv:
            # This Coordinates does not represent a real physical object; Keep
            #   it separated from the general population in its own Space object
            self.private = True
            self.space = Space()
            self.domain = 0
        else:
            self.private = False
            if not all_space:
                # Space has yet to be created; This will be the first object
                all_space = Space()
                self.space = all_space
                self.domain = 0
            else:
                # Space exists; Register coordinates and publish returned ID
                self.space = all_space
                self.domain = domain
        self._id[self.domain] = self.space.register_coordinates(self, pos, vel)

    @property
    def position(self) -> Vector3:
        """Go into the relevant Space structure and retrieve the position that
            is assigned to this FoR, and wrap it in a Vector3.
        """
        return Vector3(self.space.array_position[self.domain][self.id])

    @position.setter
    def position(self, v: np.ndarray):
        """Transparently change the value of the position assigned to this FoR.

        NOTE: If a scalar is given, all values of the array will be that value.
        """
        self.space.array_position[self.domain][self.id] = v

    @property
    def velocity(self) -> Vector3:
        # See position
        return Vector3(self.space.array_velocity[self.domain][self.id])

    @velocity.setter
    def velocity(self, v: np.ndarray):
        # See position.setter
        self.space.array_velocity[self.domain][self.id] = v

    @property
    def position_pol(self) -> Tuple[N, N, N]:
        # Convert cartesian position from a vector to a tuple of Rho, Theta, Phi
        return cart3_polar3(*self.position)

    @property
    def velocity_pol(self) -> Tuple[N, N, N]:
        # See position_pol
        return cart3_polar3(*self.velocity)

    @property
    def position_cyl(self) -> Tuple[N, N, N]:
        """Return the position of this FoR in Cylindrical Coordinates."""
        # First, get the initial Rho, Theta, and Phi as normal
        i_rho, theta, i_phi = self.position_pol
        # Theta is going to be the same, but final Rho and Z are going to be the
        #   lengths of component vectors making up a 2D vector whose angle of
        #   inclination is equal to Phi and whose length is equal to initial Rho
        f_rho, f_z = polar2_cart2(i_rho, i_phi)
        # Return the new Cylindrical Coordinates
        return f_rho, theta, f_z

    @property
    def velocity_cyl(self) -> Tuple[N, N, N]:
        # See position_cyl
        i_rho, theta, i_phi = self.velocity_pol
        f_rho, f_z = polar2_cart2(i_rho, i_phi)
        return f_rho, theta, f_z

    @property
    def id(self):
        return self._id[self.domain]

    @id.setter
    def id(self, v):
        self._id[self.domain] = v

    def as_seen_from(self, pov: "Coordinates") -> "Coordinates":
        """Return a new Coordinates, from the perspective a given frame of
            reference.
        """
        pos_rel = self.position - pov.position
        vel_rel = self.velocity - pov.velocity
        dir_rel = self.heading / pov.heading
        rot_rel = self.rotate / pov.heading

        relative = Coordinates(pos_rel, vel_rel, dir_rel, rot_rel, priv=True)
        return relative

    def add_velocity(self, velocity):
        self.space.add_coordinates(self.domain, self.id, vel=velocity)

    @jit
    def movement(self, seconds: N) -> Tuple[Vector3, Vector3]:
        return self.position, self.velocity * seconds

    @jit
    def pos_after(self, seconds: N) -> Vector3:
        p, v = self.movement(seconds)
        return p + v

    def increment(self, seconds: N):
        self.increment_rotation(seconds)
        self.increment_position(seconds)

    def increment_rotation(self, seconds):
        theta, vec = break_rotor(self.rotate)
        theta *= seconds
        rotate = get_rotor(theta, vec)
        self.heading = rotate * self.heading

    def increment_position(self, seconds, motion=None):
        self.space.add_coordinates(
            self.domain, self.id, motion or self.movement(seconds)[1]
        )

    def serialize(self) -> Dict[str, Union[List[N], int]]:
        flat = {
            "pos": list(self.position),
            "vel": list(self.velocity),
            "hea": [self.heading.w, *self.heading.vec],
            "rot": [self.rotate.w, *self.rotate.vec],
            "domain": self.domain,
        }
        return flat


###===---
# COORDINATE OPERATIONS
###===---


def get_bearing(a, b):
    """Return SPHERICAL position of B, from the perspective of A."""
    # TODO: Rewrite or remove in accordance with new Quaternion math
    ap = a.c_pol  # Polar of A
    ac = a.c_car  # Cartesian of A
    bp = b.c_pol  # Polar of B
    bc = b.c_car  # Cartesian of B

    ab_r = np.sqrt(
        (ac[0] - bc[0]) ** 2 + (ac[1] - bc[1]) ** 2 + (ac[2] - bc[2]) ** 2
    )  # Rho of output

    ab_t, ab_p = ap[1] - bp[1], ap[2] - bp[2]  # Theta and Phi of output
    ab_p = 0 if isnan(ab_p) else ab_p

    ab = [ab_r, ab_t, ab_p]
    return ab


def bearing_wrt_heading(bearing, heading):
    """Given an absolute bearing and a heading, rotate the bearing relative to
        the heading.
    """
    # bearing: rho, theta, phi --- distance, elevation, turn
    # heading: pitch, yaw, roll --- elevation, turn, tilt
    # TODO: Rewrite or remove in accordance with new Quaternion math
    new = np.array((0, 0, 0))  # init: rho, theta, phi --- distance, elevation, turn
    new[0] = bearing[0]
    new[1] = bearing[1] - heading[0]  # bearing elevation minus heading elevation
    new[2] = bearing[2] - heading[1]  # bearing turn minus heading turn
    print(bearing, heading)
    print(new)
    return new


def get_cylindrical(a, b):
    """Return CYLINDRICAL position of B, from the perspective of A."""
    # TODO: Rewrite or remove in accordance with new Quaternion math
    bearing = get_bearing(a, b)  # Get the direction from A to B
    heading = a.data[1]  # Heading of A
    bearing_wr = bearing_wrt_heading(bearing, heading)  # Adjust for heading
    return cyl3_cart3(*bearing_wr)  # Convert to cartesian
