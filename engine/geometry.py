from math import radians, degrees, isnan

# from astropy import units as u
import numpy as np
from quaternion import quaternion
from vectormath import Vector3, Vector3Array


all_space = None


###===---
# COORDINATE TRANSFORMATIONS
###===---


def npr(n):
    return np.round(n, 5)


def rad_deg(theta):
    return npr(degrees(theta))


def deg_rad(theta):
    return npr(radians(theta))


def cart2_polar2(x, y):
    rho = np.sqrt(x ** 2 + y ** 2)
    phi = np.pi / 2 - np.arctan2(y, x)
    return rho, phi


def polar2_cart2(rho, phi):
    x = rho * np.cos(phi)
    y = rho * np.sin(phi)
    return x, y


def cart3_polar3(x, y, z):
    ρ = np.sqrt(x ** 2 + y ** 2 + z ** 2)
    φ = rad_deg(np.arccos(z / ρ))
    θ = rad_deg(np.arctan2(y, x))
    return npr((ρ, θ, φ))


def polar3_cart3(ρ, θ, φ):
    θ = np.pi / 2 - deg_rad(θ)
    φ = deg_rad(φ)
    z = ρ * np.cos(φ) * np.sin(θ)
    x = ρ * np.sin(φ) * np.sin(θ)
    y = ρ * np.cos(θ)
    return npr((x, y, z))


def cyl3_cart3(*cyl):
    y = cyl[2]
    z, x = polar2_cart2(cyl[0], deg_rad(cyl[1]))
    return x, y, z


###===---
# QUATERNION FUNCTIONS
# Huge thanks to aeroeng15 for help with this
# Quaternions are the best and also worst
###===---


def get_rotor(theta: float, axis: Vector3) -> quaternion:
    """
    Return a Unit Quaternion which will rotate a Heading by Theta about Axis
    """
    q = quaternion(
        np.cos(theta / 2), *[v * np.sin(theta / 2) for v in axis]
    ).normalized()
    return q


def break_rotor(q: quaternion) -> tuple:
    """
    Given a Unit Quaternion, break it into an angle and a Vector3
    """
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


class Space:
    """
    Coordinates tracker/handler object
    """

    def __init__(self, first_pos, first_vel):
        # TODO: Make this have enough levels
        self.array_position = Vector3Array([Vector3Array([first_pos])])
        self.array_velocity = Vector3Array([Vector3Array([first_vel])])

    def register_coordinates(self, coords, newpos, newvel):
        # Register coordinates and return ID number with which to retrieve them
        new_id = len(self.array_position)
        if coords.domain == new_id:
            # New domain needs to be made
            self.array_position = np.append(self.array_position, Vector3Array(newpos))
            self.array_velocity = np.append(self.array_velocity, Vector3Array(newvel))
        elif coords.domain > new_id:
            # Domain number is too high, cannot make
            raise ValueError("Cannot make a new domain higher than the next index")
        else:
            # Do thing
            self.array_position[coords.domain] = np.append(
                self.array_position[coords.domain], Vector3Array(newpos)
            )
            self.array_velocity[coords.domain] = np.append(
                self.array_velocity[coords.domain], Vector3Array(newvel)
            )
        return new_id

    def get_coordinates(self, domain, index):
        return self.array_position[domain][index], self.array_velocity[domain][index]

    def progress(self, time: float):
        self.array_position += self.array_velocity * time


class Coordinates:
    """
    Coordinates object:
    Store information as Vector3 and Quaternions and return transformations as requested
    """

    def __init__(
        self,
        pos=(0, 0, 0),
        vel=(0, 0, 0),
        aim=None,
        rot=None,
        *,
        noregister=False,
        domain=0
    ):
        pos = Vector3(*pos)  # Physical location
        vel = Vector3(*vel)  # Change in location per second
        self.heading = aim or quaternion(0, 0, 0, 0)  # Orientation
        self.rotate = rot or quaternion(0, 0, 0, 0)  # Change in orientation per second

        global all_space

        if noregister:
            self.private = True
            self.space = Space(pos, vel)
            self.domain = 0
            self.id = 0
        else:
            if not all_space:
                all_space = Space(pos, vel)
                self.space = all_space
                self.domain = 0
                self.id = 0
            else:
                self.space = all_space
                self.domain = domain
                self.id = self.space.register_coordinates(self, pos, vel)
            self.private = False

    @property
    def position(self):
        return self.space.array_position[self.domain][self.id]

    @property
    def velocity(self):
        return self.space.array_velocity[self.domain][self.id]

    def as_seen_from(self, pov):
        """
        Return a new Coordinates, from the perspective a given frame of reference
        """
        pos_relative = self.position - pov.position
        vel_relative = self.velocity - pov.velocity
        dir_relative = self.heading / pov.heading
        rot_relative = self.rotate / pov.heading

        relative = Coordinates(
            pos_relative, vel_relative, dir_relative, rot_relative, noregister=True
        )
        return relative

    def movement(self, seconds):
        return self.position, self.velocity * seconds

    def increment(self, seconds):
        self.increment_rotation(seconds)
        self.increment_position(seconds)

    def increment_rotation(self, seconds):
        theta, vec = break_rotor(self.rotate)
        theta *= seconds
        rotate = get_rotor(theta, vec)
        self.heading = rotate * self.heading

    def increment_position(self, seconds, motion=None):
        # FIXME
        self.position += motion or self.movement(seconds)[1]


###===---
# COORDINATE OPERATIONS
###===---


def get_bearing(a, b):
    """Return SPHERICAL position of B, from the perspective of A"""
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
    """Given an absolute bearing and a heading, rotate the bearing relative to the heading"""
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
    """Return CYLINDRICAL position of B, from the perspective of A"""
    # TODO: Rewrite or remove in accordance with new Quaternion math
    bearing = get_bearing(a, b)  # Get the direction from A to B
    heading = a.data[1]  # Heading of A
    bearing_wr = bearing_wrt_heading(bearing, heading)  # Adjust for heading
    return cyl3_cart3(*bearing_wr)  # Convert to cartesian
