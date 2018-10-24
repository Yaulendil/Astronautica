from astropy import units, constants
import numpy

from . import interior


class Coordinates:
    def __init__(self, x=0, y=0, z=0):
        self.cartesian = (x * units.kilometer, y * units.kilometer, z * units.kilometer)

    @property
    def c_pol(self):
        """Return the SPHERICAL coordinates"""
        return

    @property
    def c_cyl(self):
        """Return the CYLINDRICAL coordinates"""
        return

    @property
    def c_car(self):
        """Return the CARTESIAN coordinates"""
        return self.cartesian


def get_bearing(a, b):
    """Return SPHERICAL coordinates of relative position"""
    pass


def get_relative(a, b):
    """Return CYLINDRICAL coordinates of relative position"""
    pass


class ObjectInSpace:
    def __init__(self, x=0, y=0, z=0, size=100):
        self.radius = size * units.meter  # Assume a spherical cow in a vacuum...
        self.coordinates = Coordinates(x, y, z)

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

    def tick_movement(self):
        pass


class Ship(ObjectInSpace):
    pass
