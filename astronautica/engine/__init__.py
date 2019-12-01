"""Package containing the working components of the Game Engine.

The Engine Package contains most of the "moving parts" of the Game World. It
    implements the Space Class, as well as all Coordinate systems that fall
    under it, and the Spacetime Class, which applies the concept of Time to
    Space.
"""

from asyncio import CancelledError, sleep
from collections import defaultdict
from datetime import datetime as dt, timedelta as td
from inspect import isawaitable
from time import time
from typing import Dict, Iterable, List, Tuple

from ezipc.util import echo

from .collision import find_collisions
from .objects import Object
from .serial import deserialize, Serial, Serializable
from .space import Coordinates, LocalSpace, Space
from .world import Clock, Galaxy, MultiSystem, System


CB_PRE_TICK = []
CB_POST_TICK = []


is_power_of_2 = lambda n: n == 2 ** (n.bit_length() - 1)


async def run_iter(it: Iterable):
    for func in it:
        try:
            result = func()
            while isawaitable(result):
                result = await result
        except Exception as e:
            echo(f"Callback {func!r} raised {type(e).__name__!r}:\n    {e}")


class RealTime(Clock):
    def __call__(self):
        return time()


class Spacetime:
    def __init__(self, space_: Space = None, world_: Galaxy = None):
        self.space: Space = space_ or Space()
        self.world: Galaxy = world_

    def _tick(self, target: float = 1, allow_collision: bool = True) -> int:
        """Simulate the passing of time. The target amount should be one second
            divided by a power of two.
        """
        key = lambda o: o[0]
        hits: int = 0
        passed: float = 0
        collisions: List[Tuple[float, Tuple[Object, Object]]] = []

        # Repeat this until there are no Collisions left to be simulated.
        while allow_collision and (collisions := find_collisions(target - passed)):
            # Find the soonest Collision.
            seconds, (obj_a, obj_b) = min(collisions, key=key)

            # Progress Time to the point of the soonest Collision.
            self.space.progress(seconds - passed)
            passed += seconds

            # Simulate the Collision.
            obj_a.collide_with(obj_b)
            hits += 1
            # Objects have now had their Velocities changed. Future Collisions
            #   may no longer be valid, so recalculate the Collisions which have
            #   not happened yet.

        # Then, simulate the rest of the time.
        self.space.progress(target - passed)
        return hits

    @property
    def index(self) -> Dict[LocalSpace, List[Object]]:
        out: Dict[LocalSpace, List[Object]] = defaultdict(list)

        for obj in Object.ALL:
            if obj.frame.domain:
                out[obj.frame.domain].append(obj)

        return out

    @property
    def objects(self) -> List[Tuple[List[Object], List[Object]]]:
        return [(l, l.copy()) for l in self.index.values()]

    def progress(self, seconds: int, granularity: int = 2):
        """Simulate the passing of time."""
        if seconds == 0:
            return
        elif seconds < 0:
            raise ValueError(
                "Unfortunately, the Laws of Thermodynamics prohibit time reversal."
            )
        elif granularity <= 0:
            raise ValueError("Progression Granularity must be greater than zero.")
        elif not is_power_of_2(granularity):
            raise ValueError("Progression Granularity must be an integral power of 2.")

        for i in range(seconds * granularity):
            self._tick(1 / granularity, True)

    async def run(self, turn_length: int = 300):
        try:
            turn = td(seconds=turn_length)
            start = dt.utcnow()
            tick_next = start.replace(minute=0, second=0, microsecond=0)

            while tick_next <= (start - turn):
                tick_next += turn

            while True:
                await sleep((tick_next - dt.utcnow()).total_seconds())
                echo(f"Simulating {turn_length} seconds...")
                await run_iter(CB_PRE_TICK)

                self.progress(turn_length)

                echo("Simulation complete.")
                await run_iter(CB_POST_TICK)
                tick_next += turn

        except CancelledError:
            echo("Simulation Coroutine cancelled.")  # Saving...")
        # finally:
            # self.save_to_file()
            # echo("win", "Spacetime Saved.")
