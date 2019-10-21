from collections import deque
from itertools import compress
from typing import Deque, Sequence, Tuple

from .. import Coordinates, Object
from .subsystem import Section


class Vessel(object):
    # __slots__ = ("frame", "obj", "orders")

    def __init__(self, name: str, obj: Object, sections: Sequence[Section]):
        self.name: str = name
        self.obj: Object = obj
        self.orders: Deque[str] = deque()

        self.sections = {}
        for sys in sections:
            name__ = type(sys).__name__

            if name__ in self.sections:
                raise ValueError("Multiple {!r} Subsystems".format(name__))
            else:
                self.sections[name__] = sys

    @property
    def frame(self) -> Coordinates:
        return self.obj.frame

    def add_order(self, order: str, idx: int = None) -> None:
        if idx is None:
            self.orders.append(order)
        else:
            self.orders.insert(idx, order)

    def exec_queue(self) -> Tuple[bool, ...]:
        res = tuple(self.execute(order) for order in self.orders)
        self.orders[:] = tuple(compress(self.orders, res))
        return res

    def execute(self, order: str) -> bool:
        ...
