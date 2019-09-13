from abc import ABC, abstractmethod
from typing import Any, Dict, List, NewType, Type, TypeVar, Union

from astropy.units import Quantity

from .physics.units import Units

__all__ = ["Domain", "Node", "Serial", "Serializable"]


Primitive = Union[Dict["Primitive", "Primitive"], float, int, List["Primitive"], str]
Serial: Type = NewType("Serial", Dict[str, Primitive])
T = TypeVar("T")


class Serializable(ABC):
    """ABC for Types that can be Serialized."""

    @abstractmethod
    def serialize(self) -> Serial:
        """Return a Dict representing this Object in a form that can be written
            as Text. The Dict may have the following fields:

        type -- This MUST be the NAME OF THIS CLASS as a String.
        data -- This may be anything Serializable. It will be passed as-is to
            the `from_serial()` classmethod during reconstruction.
        subs -- This should be a Dict. Its Keys should be Strings. During
            reconstruction, `deserialize()` will be called on each of its
            Values, and the Values will be replaced with the Return of that
            call. The final Dict will then be passed to `from_serial()`.
        """
        ...

    @classmethod
    @abstractmethod
    def from_serial(
        cls: Type[T], data: Dict[str, Primitive], subs: Dict[str, Any]
    ) -> T:
        ...


class Node(Serializable):
    """ABC for the definition of Gravitational Systems. Defines Abstract Methods
        of the interface required for the Spatial Hierarchy.
    """

    @property
    @abstractmethod
    def mass(self) -> Quantity:
        ...


class Domain(Node):
    """A specialized Node which defines the core of a local Coordinates System.
    """

    @property
    @abstractmethod
    def units(self) -> Units:
        ...
