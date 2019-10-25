from abc import ABC, abstractmethod
from inspect import isabstract
from typing import Any, Dict, Iterator, List, NewType, Type, TypeVar, Union

from astropy.units import Quantity

from .units import Units


Primitive = Union[Dict["Primitive", "Primitive"], float, int, List["Primitive"], str]
Serial: Type = NewType("Serial", Dict[str, "Primitive"])
T = TypeVar("T")


# Recursively check for Subclasses to map out all Types that should implement a
#   .from_serial() Classmethod.
def get_subs(t: type) -> Iterator[type]:
    yield from map(get_subs, t.__subclasses__())


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


MAP: Dict[str, Type[Serializable]] = {
    t.__name__: t for t in get_subs(Serializable) if not isabstract(t)
}


def deserialize(obj: Union[List[Serial], Serial]):
    if isinstance(obj, list):
        return list(map(deserialize, obj))

    classname: str = obj.get("class")
    cls = MAP.get(classname)

    if cls is not None:
        data = obj.get("data")
        subs = {k: deserialize(v) for k, v in obj.get("subs", {}).items()}
        return cls.from_serial(data, subs)
    else:
        return None
