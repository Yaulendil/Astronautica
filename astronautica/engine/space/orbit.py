from typing import Tuple

from astropy import units as u
from vectormath import Vector3

from engine.space import Position, Clock


class Orbit(Position):
    """A Relative Frame of Reference which is based on a Primary, whose real
        position is a function of Time.
    """

    # TODO

    __slots__ = ("offset", "primary", "radius", "time")

    def __init__(
        self,
        primary: Position,
        radius: float,
        time: Clock,
        unit: u.Unit = u.meter,
        *,
        offset: float = 0,
    ):
        self.primary = primary
        self.radius = radius
        self.time = time

        self.offset = offset

        self.domain = self.primary.domain
        self.unit = unit

    @property
    def position(self) -> Vector3:
        pass

    @property
    def velocity(self) -> Vector3:
        pass

    @property
    def position_pol(self) -> Tuple[float, float, float]:
        pass

    @property
    def velocity_pol(self) -> Tuple[float, float, float]:
        pass

    @property
    def position_cyl(self) -> Tuple[float, float, float]:
        pass

    @property
    def velocity_cyl(self) -> Tuple[float, float, float]:
        pass


class Lagrangian(Position):
    """A Relative Frame of Reference which is based on an Orbit; The five
        Lagrangian Points are the points relative to an Orbiting Body at which
        a Body can maintain a stable secondary Orbit.
    """

    # TODO: Return Real values relative to Leader as appropriate for Point.

    def __init__(self, leader: Orbit, point: int):
        self.leader: Orbit = leader
        self.point: int = point
        self.real: Orbit = Orbit(
            self.leader.primary,
            self.leader.radius,
            self.leader.time,
            self.leader.unit,
            offset=self.leader.offset,
        )

    @property
    def position(self) -> Vector3:
        return self.real.position

    @property
    def velocity(self) -> Vector3:
        return self.real.velocity

    @property
    def position_pol(self) -> Tuple[float, float, float]:
        return self.real.position_pol

    @property
    def velocity_pol(self) -> Tuple[float, float, float]:
        return self.real.velocity_pol

    @property
    def position_cyl(self) -> Tuple[float, float, float]:
        return self.real.position_cyl

    @property
    def velocity_cyl(self) -> Tuple[float, float, float]:
        return self.real.velocity_cyl
