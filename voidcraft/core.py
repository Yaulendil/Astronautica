import crypt
from datetime import datetime as dt

from astropy import units#, constants
# import numpy as np

from . import interior
import geometry


_SALT = crypt.mksalt()


class ObjectInSpace:
    def __init__(self, x=0, y=0, z=0, size=100):
        self.radius = size * units.meter  # Assume a spherical cow in a vacuum...
        self.coordinates = geometry.Coordinates([x, y, z])

    def tick_movement(self, time):
        # TODO:
        # Return a vector from start position to end position of this tick
        # Vector returned will be checked against all other motion vectors
        # If two motion vectors pass closer together than the sum of the radii of the objects, they collided
        pass


class Ship(ObjectInSpace):
    """A pressurized vessel allowing living creatures to brave the void"""

    def __init__(self, name, *a, **kw):
        super().__init__(*a, **kw)
        self.name = name
        self.hash = None
        self.salt = _SALT
        self.updated = dt.utcnow().timestamp()
        self.struct = {}


class Sloop(Ship):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.struct["medbay"] = interior.DepartmentMedical(self, 4)
        self.struct["maint"] = interior.DepartmentMaintenance(self, 6)
