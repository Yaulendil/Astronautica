from datetime import datetime as dt

from engine import physics


class Ship(physics.ObjectInSpace):
    """A pressurized vessel allowing living creatures to brave the void"""

    def __init__(self, name=None, *a, **kw):
        super().__init__(*a, **kw)
        self.name = str(name)
        self.hash = None
        self.updated = dt.utcnow().timestamp()
        self.struct = {}
