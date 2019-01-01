from math import radians, degrees, isnan

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


def rotate_matrix(matrix, rot):
    """Return a copy of the input 'matrix', rotated by the tuple 'rot'"""
    pitch, yaw, roll = rot
    print(rot)
    # rr = r_x(pitch) * r_y(yaw) * r_z(roll)
    rr = heading_to_matrix(rot)
    print(rr)
    return matrix * rr


def heading_to_matrix(heading):
    """Return a rotational matrix based on a pitch/yaw/roll iterable"""
    return r_x(heading[0]) * r_y(heading[1]) * r_z(heading[2])


def matrix_to_heading(r):
    """Convert a rotation matrix into pitch/yaw/roll"""
    α = np.arctan2(r[1][0], r[0][0])
    β = np.arctan2(-r[2][1], np.sqrt(r[2][1] ** 2 + r[2][2] ** 2))
    γ = np.arctan2(r[2][1], r[2][2])
    return α, β, γ


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

        self.data = np.array(
            [
                cartesian,  # 0. Position
                heading or [0.0, 0.0, 0.0],  # 1. Facing
                course or [0.0, 0.0, 0.0],  # 2. Moving
                rotation or [0.0, 0.0, 0.0],  # 3. Turning
            ]
        )
        self.cartesian = self.data[0]

    @property
    def heading_matrix(self):
        return heading_to_matrix(self.data[1])

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

    def move(self, delta=None):
        delta = delta or self.data[2]  # With no parameter, use own velocity
        d = self.data[0]
        for i in range(len(d)):
            d[i] = d[i] + delta[i]

    def rotate(self, rot):
        m = self.heading_matrix
        mm = rotate_matrix(m, rot)
        print(mm)
        new = matrix_to_heading(mm)
        return new


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

    ab_t, ab_p = ap[1] - bp[1], ap[2] - bp[2]  # Theta and Phi of output
    ab_p = 0 if isnan(ab_p) else ab_p

    ab = [ab_r, ab_t, ab_p]
    return ab


def bearing_wrt_heading(bearing, heading):
    """Given an absolute bearing and a heading, rotate the bearing relative to the heading"""
    # bearing: rho, theta, phi --- distance, elevation, turn
    # heading: pitch, yaw, roll --- elevation, turn, tilt
    new = np.array((0, 0, 0))  # init: rho, theta, phi --- distance, elevation, turn
    new[0] = bearing[0]
    new[1] = bearing[1] - heading[0]  # bearing elevation minus heading elevation
    new[2] = bearing[2] - heading[1]  # bearing turn minus heading turn
    print(bearing, heading)
    print(new)
    return new


def get_cylindrical(a, b):
    """Return CYLINDRICAL position of B, from the perspective of A"""
    bearing = get_bearing(a, b)  # Get the direction from A to B
    heading = a.data[1]  # Heading of A
    bearing_wr = bearing_wrt_heading(bearing, heading)  # Adjust for heading
    return cyl3_cart3(*bearing_wr)  # Convert to cartesian


# def get_relative(a, b):
#     """Return CYLINDRICAL coordinates of relative position"""
#     pass


A = Coordinates(car=[0,0,0])
B = Coordinates(car=[5,5,0])
