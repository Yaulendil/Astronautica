from abc import ABC, abstractmethod
from typing import Dict, NewType, Type, Union

from astropy.units import Quantity

from .physics.units import Units

__all__ = ["Node", "Serial"]


Serializable = Union[dict, float, int, list, str]
Serial: Type = NewType("Serial", Dict[str, Serializable])


class Node(ABC):
    """ABC for the definition of Gravitational Systems. Defines Abstract Methods
        of the interface required for the Spatial Hierarchy.
    """

    @abstractmethod
    @property
    def mass(self) -> Quantity:
        ...

    @abstractmethod
    @property
    def units(self) -> Units:
        ...

    @abstractmethod
    def serialize(self) -> Serial:
        ...
