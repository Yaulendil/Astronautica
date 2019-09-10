from astropy import units as u

from ..abc import Node
from ..physics.units import *


class MultiSystem(set, Node):
    """Representation of a Gravitational System without any clear "Master".
        Typically the case for Stars near each other.
    """

    def __init__(self, *bodies: Node):
        if len(bodies) < 2:
            raise ValueError("A Multi System must have at least two Objects.")

        super().__init__(bodies)
        # self.slaves: Tuple[Node, ...] = bodies

    @property
    def mass(self):
        return sum(self, u.kg * 0)

    @property
    def units(self):
        return tuple(self)[0].units

    def serialize(self):
        return dict(type=type(self).__name__, content=[o.serialize() for o in self])


class System(set, Node):
    """Representation of a Gravitational System with a clear "Master". Typically
        the case for Planetary Systems orbiting a single Star.
    """

    def __init__(self, master: Node, *slaves: Node):
        self.master: Node = master

        super().__init__(slaves)
        # self.slaves: Set[Node] = {*slaves}

    @property
    def mass(self):
        return sum(self, self.master.mass)

    @property
    def units(self):
        return self.master.units

    def serialize(self):
        return dict(
            type=type(self).__name__,
            master=self.master.serialize(),
            content=[o.serialize() for o in self],
        )


class Galaxy(System):
    units = UNITS_GALACTIC
