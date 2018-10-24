from astropy import units, constants
import numpy


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


class Department:
    def __init__(self, size, maximum=None):
        if maximum is None:
            maximum = size
        self.crew = size
        self.crew_cap = maximum


class Ship:
    pass
