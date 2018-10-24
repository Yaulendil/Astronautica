from astropy import units
import numpy

# CONSTANT DIRECTIONS
# (θ elevation, φ azimuth)
NORTH = (0 * units.degree, 0 * units.degree)
EAST = (0 * units.degree, 90 * units.degree)
WEST = (0 * units.degree, -90 * units.degree)
SOUTH = (0 * units.degree, 180 * units.degree)

ZENITH = (90 * units.degree, 0 * units.degree)
NADIR = (-90 * units.degree, 0 * units.degree)


def cart2_polar2(x, y):
    rho = numpy.sqrt(x ** 2 + y ** 2)
    phi = numpy.arctan2(y, x).to(units.degree)
    return rho, phi


def polar2_cart2(rho, phi):
    x = rho * numpy.cos(phi)
    y = rho * numpy.sin(phi)
    return x, y


class Coordinates:
    """Coordinates object:
    Store coordinates as a cartesian tuple and return transformations as requested"""

    def __init__(self, *, car=None, cyl=None, pol=None):
        if car and len(car) >= 3:  # CARTESIAN: (X, Y, Z)
            self.cartesian = (
                car[0] * units.kilometer,
                car[1] * units.kilometer,
                car[2] * units.kilometer,
            )
        elif cyl and len(cyl) >= 3:  # CYLINDRICAL: (R, φ azimuth, Y)
            pass
        elif pol and len(pol) >= 3:  # SPHERICAL: (R, θ elevation, φ azimuth)
            pass
        else:
            raise TypeError("Coordinates object requires initial values")

        self.heading = (
            0 * units.degree,
            0 * units.degree,
        )  # (θ elevation, φ azimuth); Direction object is FACING
        self.course = (
            0 * units.degree,
            0 * units.degree,
        )  # (θ elevation, φ azimuth); Direction object is MOVING
        self.velocity = 0 * (units.meter / units.second)
        # Velocity can be considered the rho of the course

    @property
    def c_car(self):
        """Return the CARTESIAN coordinates"""
        return self.cartesian

    @property
    def c_cyl(self):
        """Return the CYLINDRICAL coordinates"""
        x, y, z = self.cartesian  # Take the cartesian coordinates
        rho, phi = cart2_polar2(x, z)  # Find rho and phi of x and z
        return rho, phi, y  # Return rho, phi, and height

    @property
    def c_pol(self):
        """Return the SPHERICAL coordinates (horizontal)"""
        x, y, z = self.cartesian
        rho0, phi = cart2_polar2(x, y)
        rho, theta = cart2_polar2(z, rho0)
        return rho, theta, phi


def get_bearing(a, b):
    """Return SPHERICAL coordinates (horizontal) of relative position"""
    ap = a.c_pol  # Polar of A
    ac = a.c_car  # Cartesian of A
    bp = b.c_pol  # Polar of B
    bc = b.c_car  # Cartesian of B
    ab_r = numpy.sqrt(
        (ac[0] - bc[0]) ** 2 + (ac[1] - bc[1]) ** 2 + (ac[2] - bc[2]) ** 2
    )  # Rho of output
    ab_tp = ap[1] - bp[1], ap[2] - bp[2]  # Theta and Phi of output
    ab = ab_r, *ab_tp
    return ab


# def get_relative(a, b):
#     """Return CYLINDRICAL coordinates of relative position"""
#     pass
