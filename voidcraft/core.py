from datetime import datetime as dt

from . import interior
import physics


class Ship(physics.ObjectInSpace):
    """A pressurized vessel allowing living creatures to brave the void"""

    def __init__(self, name, *a, **kw):
        super().__init__(*a, **kw)
        self.name = name
        self.hash = None
        self.updated = dt.utcnow().timestamp()
        self.struct = {}


class Sloop(Ship):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.struct["medbay"] = interior.DepartmentMedical(self, 4)
        self.struct["maint"] = interior.DepartmentMaintenance(self, 6)
