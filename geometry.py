from math import radians, degrees

# from astropy import units as u
import numpy as np

# CONSTANT DIRECTIONS
# (θ elevation, φ azimuth)
NORTH = (0, 0)
EAST = (0, 90)
WEST = (0, -90)
SOUTH = (0, 180)

ZENITH = (90, 0)
NADIR = (-90, 0)

###===---
# MATH FUNCTIONS
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
# ROTATIONAL FUNCTIONS
###===---

# https://en.wikipedia.org/wiki/Rotation_matrix#Basic_rotations


def r_x(theta):
    return np.array(
        [
            [1, 0, 0],
            [0, np.cos(theta), -np.sin(theta)],
            [0, np.sin(theta), np.cos(theta)],
        ]
    )


def r_y(theta):
    return np.array(
        [
            [np.cos(theta), 0, np.sin(theta)],
            [0, 1, 0],
            [-np.sin(theta), 0, np.cos(theta)],
        ]
    )


def r_z(theta):
    return np.array(
        [
            [np.cos(theta), -np.sin(theta), 0],
            [np.sin(theta), np.cos(theta), 0],
            [0, 0, 1],
        ]
    )


def get_matrix(heading):
    """Return a rotational matrix based on a pitch/yaw/roll iterable"""
    return r_x(heading[0]) * r_y(heading[1]) * r_z(heading[2])


def rotate(matrix, rot):
    """Return a copy of the input 'matrix', rotated by the tuple 'rot'"""
    pitch, yaw, roll = rot
    rr = r_x(pitch) * r_y(yaw) * r_z(roll)
    return matrix * rr


class Coordinates:
    """Coordinates object:
    Store coordinates as a cartesian tuple and return transformations as requested
    Real data:
        Cartesian (x[km],y[km],z[km])
        Heading   (p[deg],y[deg],r[deg])
        Course    (v[m/s],θ[deg],φ[deg])
        Rotation   (p[deg/min],y[deg/min],r[deg/min])"""

    def __init__(
        self, *, car=None, cyl=None, pol=None, heading=None, course=None, rotation=None
    ):
        if car and len(car) >= 3:  # CARTESIAN: (X, Y, Z)
            cartesian = [float(n) for n in car]
        elif cyl and len(cyl) >= 3:  # CYLINDRICAL: (R, φ azimuth, Y)
            cartesian = list(cyl3_cart3(*cyl))  # (x, y, z)
        elif pol and len(pol) >= 3:  # SPHERICAL: (R, θ elevation, φ azimuth)
            cartesian = list(polar3_cart3(*pol))
        else:
            raise TypeError("Coordinates object requires initial values")

        self.heading = heading or (
            0,
            0,
            0,
        )  # (pitch, yaw, roll); FACING orientation of object
        self.velocity = 0  # * (u.meter / u.second)
        # Velocity can be considered the rho of the course
        self.course = course or (
            0,
            0,
        )  # (θ elevation, φ azimuth); Direction object is MOVING

        self.data = np.array(
            [
                cartesian,  # 0. Position
                heading or [0.0, 0.0, 0.0],  # 1. Facing
                course or [0.0, 0.0, 0.0],  # 2. Moving
                rotation or [0.0, 0.0, 0.0],  # 3. Turning
            ]
        )
        self.cartesian = self.data[0:1]

    @property
    def array(self):
        return self.data

    @property
    def c_car(self):
        """Return the CARTESIAN coordinates"""
        return np.array([npr(v) for v in self.cartesian])

    @property
    def c_cyl(self):
        """Return the CYLINDRICAL coordinates"""
        x, y, z = self.cartesian  # Take the cartesian coordinates
        rho, phi = cart2_polar2(x, z)  # Find rho and phi of x and z
        return np.array((npr(rho), rad_deg(phi), npr(y)))  # Return rho, phi, and height

    @property
    def c_pol(self):
        """Return the SPHERICAL coordinates (horizontal)"""
        x, y, z = self.cartesian
        return cart3_polar3(x, y, z)
        # rho0, phi = cart2_polar2(x, y)
        # rho, theta = cart2_polar2(z, rho0)
        # return rho, theta, phi

    def move(self):
        d = self.data[0]
        for i in range(len(d)):
            d[i] = d[i] + self.data[2][i]


class Projectile:
    def __init__(self, start, target):
        """

        :type start: Coordinates
        :type target: Coordinates
        """
        self.start = start
        self.target = target


###===---
# COORDINATE OPERATIONS
###===---


def get_bearing(a, b):
    """Return SPHERICAL position of B, from the perspective of A"""
    ap = a.c_pol  # Polar of A
    ac = a.c_car  # Cartesian of A
    bp = b.c_pol  # Polar of B
    bc = b.c_car  # Cartesian of B
    ab_r = np.sqrt(
        (ac[0] - bc[0]) ** 2 + (ac[1] - bc[1]) ** 2 + (ac[2] - bc[2]) ** 2
    )  # Rho of output
    ab_tp = ap[1] - bp[1], ap[2] - bp[2]  # Theta and Phi of output
    ab = ab_r, *ab_tp
    return ab


def bearing_wrt_heading(bearing, heading):
    """Given an absolute bearing and a heading, rotate the bearing relative to the heading"""
    # bearing: rho, theta, phi --- distance, elevation, turn
    # heading: pitch, yaw, roll --- elevation, turn, tilt
    new = np.array((0, 0, 0))  # init: rho, theta, phi --- distance, elevation, turn
    new[0] = bearing[0]
    new[1] = bearing[1] - heading[0]
    new[2] = bearing[2] - heading[1]
    return new


def get_cylindrical(a, b):
    """Return CYLINDRICAL position of B, from the perspective of A"""
    bearing = bearing_wrt_heading(get_bearing(a, b), a.heading)
    return cyl3_cart3(*bearing)


# def get_relative(a, b):
#     """Return CYLINDRICAL coordinates of relative position"""
#     pass
