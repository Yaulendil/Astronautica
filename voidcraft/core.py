from astropy import units, constants
import numpy

from . import interior
from .. import geometry

class ObjectInSpace:
    def __init__(self, x=0, y=0, z=0, size=100):
        self.radius = size * units.meter  # Assume a spherical cow in a vacuum...
        self.coordinates = geometry.Coordinates(x, y, z)

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
