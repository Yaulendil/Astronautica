from collections import deque
from itertools import compress
from typing import Deque, Sequence, Tuple, Dict

from ..objects import Object
from ..space import Coordinates
from .subsystem import Section


class Vessel(object):
    # __slots__ = ("frame", "obj", "orders")

    def __init__(self, name: str, obj: Object, sections: Sequence[Section]):
        self.name: str = name
        self.obj: Object = obj
        self.orders: Deque[str] = deque()

        self.sections: Dict[str, Section] = {}
        for sys in sections:
            # name__ = type(sys).__name__

            if (name__ := type(sys).__name__) in self.sections:
                raise ValueError("Multiple {!r} Subsystems".format(name__))
            else:
                self.sections[name__] = sys

    @property
    def crew(self) -> int:
        return sum(sec.staff.crew for sec in self.sections.values())

    @property
    def crew_hurt(self) -> int:
        return sum(sec.staff.crew_hurt for sec in self.sections.values())

    @property
    def crew_dead(self) -> int:
        return sum(sec.staff.crew_dead for sec in self.sections.values())

    @property
    def equip(self) -> int:
        return sum(sec.staff.equip for sec in self.sections.values())

    @property
    def equip_damaged(self) -> int:
        return sum(sec.staff.equip_damaged for sec in self.sections.values())

    @property
    def equip_destroy(self) -> int:
        return sum(sec.staff.equip_destroy for sec in self.sections.values())

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
