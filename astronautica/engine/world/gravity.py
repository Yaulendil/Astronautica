from typing import List

from astropy import units as u

from ..serial import Node


class Orbit(object):
    __slots__ = ("primary", "satellite")

    def __init__(self, primary: Node, satellite: Node):
        self.primary: Node = primary
        self.satellite: Node = satellite


class MultiSystem(List[Node], Node):
    """Representation of a Gravitational System without any clear Primary.
        Typically the case for Stars near each other.
    """

    def __init__(self, *bodies: Node):
        if len(bodies) < 2:
            raise ValueError("A Multi System must have at least two Objects.")

        super().__init__(self, bodies)

    @property
    def mass(self):
        return sum((o.mass for o in self), u.kg * 0)

    def serialize(self):
        return dict(
            type=type(self).__name__,
            subs=dict(bodies=[s for o in self if (s := o.serialize())]),
        )

    @classmethod
    def from_serial(cls, data, subs):
        return cls(*subs["bodies"])


class System(List[Node], Node):
    """Representation of a Gravitational System with a clear Primary. Typically
        the case for Planetary Systems orbiting a single Star.
    """

    __slots__ = ("primary",)

    def __init__(self, primary: Node, *satellites: Node):
        self.primary: Node = primary

        super().__init__(self, satellites)

    @property
    def mass(self):
        return sum((o.mass for o in self), self.primary.mass)

    def serialize(self):
        return dict(
            type=type(self).__name__,
            subs=dict(
                primary=self.primary.serialize(),
                slaves=[s for o in self if (s := o.serialize())]
            ),
        )

    @classmethod
    def from_serial(cls, data, subs):
        return cls(subs["primary"], *subs["satellites"])
