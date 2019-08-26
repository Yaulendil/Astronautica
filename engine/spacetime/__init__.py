from typing import List, Tuple, Type

from numba import jit

from .collision import distance_between_lines, find_collision
from .geometry import Coordinates, Space
from .physics import ObjectInSpace as Object


__all__ = ["Coordinates", "Object", "Space", "Spacetime"]


class Spacetime:
    def __init__(self, space: Space = None):
        self.space: Space = space or Space()
        self.index: List[Object] = []

    def add(self, obj: Object):
        self.index.append(obj)

    def new(self, cls: Type[Object] = Object, *a, **kw) -> Object:
        kw["space"] = self.space
        obj: Object = cls(*a, **kw)
        self.add(obj)
        return obj

    @jit(forceobj=True, nopython=False)
    def _find_collisions(
        self, seconds: float, list_a: List[Object], list_b: List[Object]
    ) -> List[Tuple[float, Tuple[Object, Object]]]:
        collisions: List[Tuple[float, Tuple[Object, Object]]] = []

        for obj_a in list_a[-1:0:-1]:
            list_b.pop(-1)
            start_a = obj_a.coords.position
            end_a = obj_a.coords.pos_after(seconds)

            for obj_b in list_b:
                if obj_a.coords.domain != obj_b.coords.domain:
                    continue
                start_b = obj_b.coords.position
                end_b = obj_b.coords.pos_after(seconds)
                proximity = distance_between_lines(start_a, end_a, start_b, end_b)[2]

                if proximity < obj_a.radius + obj_b.radius:
                    # Objects look like they might collide.
                    impact = find_collision(obj_a, obj_b, seconds)
                    if impact is not False:
                        collisions.append((impact, (obj_a, obj_b)))

        return collisions

    def _tick(self, seconds=1.0, allow_collision=True):
        """Simulate the passing of one second"""
        list_a: List[Object] = self.index.copy()
        list_b: List[Object] = list_a.copy()
        collisions = (
            self._find_collisions(seconds, list_a, list_b) if allow_collision else []
        )
        collisions.sort(key=lambda o: o[0])

        total = 0
        for time, (obj_a, obj_b) in collisions:
            # Simulate to the time of each collision, and then run the math
            self.space.progress(time - total)
            total += time

            obj_a.collide(obj_b)

        # Then, simulate the rest of the time.
        self.space.progress(seconds - total)

    def progress(self, time: int, granularity=10):
        """Simulate the passing of time"""
        if time == 0:
            return
        elif time < 0:
            raise ValueError(
                "Unfortunately the laws of thermodynamics prohibit time reversal."
            )
        elif granularity <= 0:
            raise ValueError("Progression granularity must be greater than zero.")

        for i in range(time * granularity):
            self._tick(1 / granularity, True)
