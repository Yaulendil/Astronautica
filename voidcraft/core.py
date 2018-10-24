from astropy import units, constants
import numpy

from . import interior


def get_bearing(a, b):
    pass


class ObjectInSpace:
    def __init__(self, x=0, y=0, z=0):
        self.coordinates = (
            x * units.kilometer,
            y * units.kilometer,
            z * units.kilometer,
        )
        self.velocity = 0 * (units.meter / units.second)

        self.heading = (
            0 * units.rad,
            0 * units.rad,
        )  # (azimuth, altitude); Direction object is FACING
        self.course = (
            0 * units.rad,
            0 * units.rad,
        )  # (azimuth, altitude); Direction object is MOVING


class Ship:
    pass
