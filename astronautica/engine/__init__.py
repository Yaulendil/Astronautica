"""Package containing the working components of the Game Engine.

The Engine Package contains most of the "moving parts" of the Game World. It
    implements the Space Class, as well as all Coordinate systems that fall
    under it, and the Spacetime Class, which applies the concept of Time to
    Space.
"""

from asyncio import CancelledError, sleep
from datetime import datetime as dt, timedelta as td
from inspect import isabstract, isawaitable
from typing import Dict, Iterable, Iterator, List, Tuple, Type, Union

from .collision import find_collisions
from .objects import Object
from .space import Coordinates, Space
from .space.base import Clock, Serial, Serializable
from .world import Galaxy, MultiSystem, System


def get_subs(t: type) -> Iterator[type]:
    yield from map(get_subs, t.__subclasses__())


# Recursively check for Subclasses to map out all Types that should implement a
#   .from_serial() Classmethod.
MAP: Dict[str, Type[Serializable]] = {
    t.__name__: t for t in get_subs(Serializable) if not isabstract(t)
}

CB_PRE_TICK = set()
CB_POST_TICK = set()


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


async def run_iter(it: Iterable):
    for func in it:
        try:
            result = func()
            while isawaitable(result):
                result = await result
        except Exception as e:
            print(f"Callback {func!r} raised {type(e).__name__!r}:\n    {e}")


class Spacetime:
    def __init__(self, space_: Space = None, world_: Galaxy = None):
        # self.index: List[Object] = []
        self.space: Space = space_ or Space()
        self.world: Galaxy = world_  # or Galaxy.generate((1.4, 1, 0.2), arms=3)

    # def add(self, obj: Object):
    #     """Add an Object to the Index of the Spacetime."""
    #     self.index.append(obj)
    #
    # def new(self, cls: Type[Object] = Object, *a, **kw) -> Object:
    #     """Create a new Instance of an Object. Arguments are passed directly to
    #         the Object Instantiation. This Method handles adding the new
    #         Instance to the Index of the Spacetime, and provides its Space
    #         object to the appropriate Keyword Argument. It then returns the new
    #         Object Instance.
    #     """
    #     kw["space"] = self.space
    #     obj: Object = cls(*a, **kw)
    #     self.add(obj)
    #     return obj

    def _tick(self, target: float = 1, allow_collision: bool = True) -> int:
        """Simulate the passing of time. The target amount should be one second
            divided by a power of two.
        """
        key = lambda o: o[0]

        def collisions_until(_time) -> List[Tuple[float, Tuple[Object, Object]]]:
            return (
                find_collisions(_time, self.index.copy(), self.index.copy())
                if allow_collision
                else []
            )

        collisions = collisions_until(target)

        hits: int = 0
        passed: float = 0
        while collisions:
            # Find the soonest Collision.
            time, (obj_a, obj_b) = min(collisions, key=key)

            # Progress Time to the point of the soonest Collision.
            self.space.progress(time - passed)
            passed += time

            # Simulate the Collision.
            obj_a.collide_with(obj_b)
            hits += 1
            # Objects have now had their Velocities changed. Future Collisions
            #   may no longer be valid, so recalculate the Collisions which have
            #   not happened yet.
            collisions = collisions_until(target - passed)
            # Repeat this until there are no Collisions left to be simulated.

        # Then, simulate the rest of the time.
        self.space.progress(target - passed)
        return hits

    def progress(self, time: int, granularity: int = 2):
        """Simulate the passing of time."""
        if time == 0:
            return
        elif time < 0:
            raise ValueError(
                "Unfortunately, the laws of thermodynamics prohibit time reversal."
            )
        elif granularity <= 0:
            raise ValueError("Progression granularity must be greater than zero.")

        for i in range(time * granularity):
            self._tick(1 / granularity, True)

    async def run(self, turn_length: int = 300, echo=print):
        try:
            turn = td(seconds=turn_length)
            start = dt.utcnow()
            tick_latest = start.replace(minute=0, second=0, microsecond=0)

            while tick_latest < (start - turn):
                tick_latest += turn

            while True:
                tick_next = tick_latest + turn
                await sleep((tick_next - dt.utcnow()).total_seconds())

                tick_latest = tick_next
                echo(f"Simulating {turn_length} seconds...")

                await run_iter(CB_PRE_TICK)
                self.progress(turn_length)
                await run_iter(CB_POST_TICK)

                echo("Simulation complete.")

        except CancelledError:
            echo("Simulation Coroutine cancelled. Saving...")
        finally:
            # self.save_to_file()
            echo("Spacetime Saved.")
