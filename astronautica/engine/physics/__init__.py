"""Physics Package: Contains Functions to calculate physical interactions."""

from typing import List, Tuple, Type, TypeVar

from .collision import distance_between_lines, find_collisions
from .space import Coordinates, Space


__all__ = ["Coordinates", "Space", "Spacetime"]


O: Type = TypeVar("O")


class Spacetime:
    def __init__(self, space: Space = None):
        self.space: Space = space or Space()
        self.index: List[O] = []

    def add(self, obj: O):
        """Add an Object to the Index of the Spacetime."""
        self.index.append(obj)

    def new(self, cls: Type[O] = O, *a, **kw) -> O:
        """Create a new Instance of an Object. Arguments are passed directly to
            the Object Instantiation. This Method handles adding the new
            Instance to the Index of the Spacetime, and provides its Space
            object to the appropriate Keyword Argument. It then returns the new
            Object Instance.
        """
        kw["space"] = self.space
        obj: O = cls(*a, **kw)
        self.add(obj)
        return obj

    def _tick(self, target=1.0, allow_collision=True):
        """Simulate the passing of time. The target amount should be one second
            divided by a power of two.
        """
        key = lambda o: o[0]

        def collisions_until(_time) -> List[Tuple[float, Tuple[O, O]]]:
            return (
                find_collisions(_time, self.index.copy(), self.index.copy())
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

        for obj in self.index:
            obj.frame.increment_rotation(target)

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
