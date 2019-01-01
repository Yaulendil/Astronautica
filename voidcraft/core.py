from astropy import units, constants
import numpy

from . import interior
import geometry


class ObjectInSpace:
    def __init__(self, x=0, y=0, z=0, size=100):
        self.radius = size * units.meter  # Assume a spherical cow in a vacuum...
        self.coordinates = geometry.Coordinates(car=[x, y, z])

    def tick_movement(self):
        pass


class Ship(ObjectInSpace):
    pass
