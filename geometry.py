from astropy import units
import numpy


def cart_polar(x, y):
    rho = numpy.sqrt(x ** 2 + y ** 2)
    phi = numpy.arctan2(y, x).to(units.degree)
    return rho, phi


def polar_cart(rho, phi):
    x = rho * numpy.cos(phi)
    y = rho * numpy.sin(phi)
    return x, y


class Coordinates:
    """Coordinates object:
    Store coordinates as a cartesian tuple and return transformations as requested"""

    def __init__(self, x=0, y=0, z=0):
        self.cartesian = (x * units.kilometer, y * units.kilometer, z * units.kilometer)

        self.heading = (
            0 * units.degree,
            0 * units.degree,
        )  # (azimuth, altitude); Direction object is FACING
        self.course = (
            0 * units.degree,
            0 * units.degree,
        )  # (azimuth, altitude); Direction object is MOVING
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
        rho, phi = cart_polar(x, z)  # Find rho and phi of x and z
        return rho, phi, y  # Return rho, phi, and height

    @property
    def c_pol(self):
        """Return the SPHERICAL coordinates (horizontal)"""
        x, y, z = self.cartesian
        rho0, phi = cart_polar(x, y)
        rho, theta = cart_polar(z, rho0)
        return rho, phi, theta


def get_bearing(a, b):
    """Return SPHERICAL coordinates (horizontal) of relative position"""
    pass


def get_relative(a, b):
    """Return CYLINDRICAL coordinates of relative position"""
    pass
