from abc import ABC, abstractmethod

from ..serial import Node


class Body(Node, ABC):
    ...


class Clock(ABC):
    @abstractmethod
    def __call__(self) -> float:
        ...
