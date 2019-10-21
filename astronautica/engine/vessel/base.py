from collections import deque
from typing import List, Deque

from engine import Coordinates, Object


class Vessel(object):
    # __slots__ = ("frame", "obj", "orders")

    def __init__(self, obj: Object):
        self.obj: Object = obj
        self.orders: Deque[str] = deque()

    @property
    def frame(self) -> Coordinates:
        return self.obj.frame

    def add_order(self, order: str, idx: int = None) -> None:
        if idx is None:
            self.orders.append(order)
        else:
            self.orders.insert(idx, order)

    def exec_queue(self) -> List[bool]:
        return [self.execute(order) for order in self.orders]

    def execute(self, order: str) -> bool:
        ...
