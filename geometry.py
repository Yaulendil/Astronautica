from math import radians, degrees, isnan

# from astropy import units as u
import numpy as np
from quaternion import quaternion
from vectormath import Vector3


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


def get_rotor(theta: int, axis: Vector3):
    """
    Return a Unit Quaternion which will rotate a Heading by Theta about Axis
    """
    q = quaternion(
        np.cos(theta / 2), *[v * np.sin(theta / 2) for v in axis]
    ).normalized()
    return q


def rotate_vector(vector: Vector3, rotor: quaternion):
    """
    p' = q*p*(q^-1)
    https://en.wikipedia.org/wiki/Quaternions_and_spatial_rotation
    """
    p = quaternion(0, *vector)
    qvec = rotor * p * rotor.inverse()
    vector_out = Vector3(*[round(x, 3) for x in qvec.vec])
    return vector_out


class Rotor(quaternion):
    """
    Extremely ugly hack, dont look directly at it
    I wrote it to cut down a bit on calculations but eeewwwwww
    I dont even know if it will work long term
    Initial signs point to no
    """

    def __init__(self, theta: float, axis: Vector3):
        self.theta = theta
        self.axis = axis
        super().__init__(*self.plain)

    def __setattr__(self, name, value):
        current = getattr(self, name, False)
        super().__setattr__(name, value)
        if current is not False:
            # Only do this if the value is being changed, rather than set initially
            self.update()

    @property
    def plain(self):
        return [np.cos(self.theta / 2)] + [
            v * np.sin(self.theta / 2) for v in self.axis
        ]

    def update(self):
        super().__init__(*self.plain)


class Coordinates:
    """Coordinates object:
    Store information as Vector3 and Quaternions and return transformations as requested
    """

    def __init__(self, pos=(0, 0, 0), vel=(0, 0, 0), heading=None, rot=None):
        self.position = Vector3(*pos)  # Physical location
        self.velocity = Vector3(*vel)  # Change in location per second
        self.heading = heading or quaternion(0, 0, 0, 0)  # Orientation
        self.rotate = rot or quaternion(0, 0, 0, 0)  # Change in orientation per second

    def as_seen_from(self, pov):
        """
        Return a new Coordinates, from the perspective a given frame of reference
        """
        pos_relative = self.position - pov.position
        vel_relative = self.velocity - pov.velocity
        dir_relative = self.heading / pov.heading
        rot_relative = self.rotate / pov.heading

        relative = Coordinates(pos_relative, vel_relative)
        relative.heading = dir_relative
        relative.rotation = rot_relative
        return relative

    def movement(self, seconds: int):
        return self.position, self.velocity * seconds

    def increment(self, seconds: int):
        self.increment_rotation(seconds)
        self.increment_position(seconds)

    def increment_rotation(self, seconds: int):
        # TODO: Do this more correctly; this feels like a hack
        for i in range(seconds):
            self.heading = self.rotate * self.heading

    def increment_position(self, seconds: int, motion=None):
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
