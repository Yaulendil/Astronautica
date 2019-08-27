from datetime import datetime as dt

from astronautica.engine.spacetime import physics


class Ship(physics.ObjectInSpace):
    """A pressurized vessel allowing living creatures to brave the void"""

    def __init__(self, name, *a, **kw):
        super().__init__(*a, **kw)
        self.name = str(name)
        self.hash = None
        self.updated = dt.utcnow().timestamp()
        self.struct = {}

    def serialize(self):
        flat = super().serialize()
        flat.update({
            "name": self.name,
            "hash": self.hash,
            "updated": self.updated,
            "struct": {x: self.struct[x].serialize() for x in self.struct}
        })
        return flat
