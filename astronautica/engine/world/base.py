from abc import ABC, abstractmethod

from astropy.units import Quantity

from ..objects import Data
from ..serial import Node
from ..units import Units, UNITS_PLANET


class Body(Node, ABC):
    __slots__ = ("data",)

    def __init__(self, mass: float, radius: float, units: Units = UNITS_PLANET):
        self.data = Data(mass, radius, units)

    @property
    def mass(self) -> float:
        return self.data.mass

    @property
    def mass_q(self) -> Quantity:
        return self.data.mass * self.units.mass

    @property
    def radius(self) -> float:
        return self.data.radius

    @property
    def radius_q(self) -> Quantity:
        return self.data.radius * self.units.distance

    @property
    def units(self) -> Units:
        return self.data.units


class Clock(ABC):
    @abstractmethod
    def __call__(self) -> float:
        ...
