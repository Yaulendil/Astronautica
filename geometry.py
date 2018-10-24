from astropy import units, constants
import numpy


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