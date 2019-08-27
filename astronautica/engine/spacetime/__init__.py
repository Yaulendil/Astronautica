"""Spacetime Package: Contains abstract classes and handlers."""

from typing import List, Tuple, Type

from numba import jit

from .collision import distance_between_lines, find_collision
from .geometry import Coordinates, Space
from .physics import ObjectInSpace as Object

# from pytimer import Timer

__all__ = ["Coordinates", "Object", "Space", "Spacetime"]


@jit(forceobj=True, nopython=False)
def _find_collisions(
    seconds: float, list_a: List[Object], list_b: List[Object]
) -> List[Tuple[float, Tuple[Object, Object]]]:
    # TODO: Move into Collision module.
    #       Complication: References to Object in Type Hints.
    collisions: List[Tuple[float, Tuple[Object, Object]]] = []

    for obj_a in list_a[-1:0:-1]:
        list_b.pop(-1)
        start_a = obj_a.coords.position
        end_a = obj_a.coords.pos_after(seconds)

        for obj_b in list_b:
            if obj_a.coords.domain != obj_b.coords.domain:
                continue
            start_b = obj_b.coords.position
            contact = obj_a.radius + obj_b.radius

            if (start_a - start_b).length < contact:
                continue

            end_b = obj_b.coords.pos_after(seconds)
            nearest_a, nearest_b, proximity = distance_between_lines(
                start_a, end_a, start_b, end_b
            )

            if proximity < contact:
                # Objects look like they might collide.
                impact = find_collision(
                    obj_a.coords.position,
                    obj_a.coords.velocity,
                    obj_b.coords.position,
                    obj_b.coords.velocity,
                    0.0,
                    seconds,
                    contact,
                )
                if impact is not False:
                    collisions.append((impact, (obj_a, obj_b)))

    return collisions


class Spacetime:
    def __init__(self, space: Space = None):
        self.space: Space = space or Space()
        self.index: List[Object] = []

    def add(self, obj: Object):
        """Add an Object to the Index of the Spacetime."""
        self.index.append(obj)

    def new(self, cls: Type[Object] = Object, *a, **kw) -> Object:
        """Create a new Instance of an Object. Arguments are passed directly to
            the Object Instantiation. This Method handles adding the new
            Instance to the Index of the Spacetime, and provides its Space
            object to the appropriate Keyword Argument. It then returns the new
            Object Instance.
        """
        kw["space"] = self.space
        obj: Object = cls(*a, **kw)
        self.add(obj)
        return obj

    def _tick(self, target=1.0, allow_collision=True):
        """Simulate the passing of time. The target amount should be one second
            divided by a power of two.
        """
        key = lambda o: o[0]

        def collisions_until(_time) -> List[Tuple[float, Tuple[Object, Object]]]:
            return (
                _find_collisions(_time, self.index.copy(), self.index.copy())
                if allow_collision
                else []
            )

        collisions = collisions_until(target)

        passed = 0
        while collisions:
            # Find the soonest Collision.
            time, (obj_a, obj_b) = min(collisions, key=key)

            # Progress Time to the point of the soonest Collision.
            self.space.progress(time - passed)
            passed += time

            # Simulate the Collision.
            obj_a.collide_with(obj_b)
            # Objects have now had their Velocities changed. Future Collisions
            #   may no longer be valid.

            # Recalculate the Collisions which have not happened yet.
            collisions = collisions_until(target - passed)
        # Repeat this until there are no Collisions to be simulated.

        # Then, simulate the rest of the time.
        self.space.progress(target - passed)

    def progress(self, time: int, granularity=2):
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
