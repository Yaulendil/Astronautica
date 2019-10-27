"""Module defining Celestial Bodies."""
from typing import Any, Dict, Type

from ..serial import Primitive, Serial, T
from .base import Body


class Star(Body):
    def serialize(self) -> Serial:
        pass

    @classmethod
    def from_serial(
        cls: Type[T], data: Dict[str, Primitive], subs: Dict[str, Any]
    ) -> T:
        pass
