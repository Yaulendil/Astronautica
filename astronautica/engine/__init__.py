"""Package containing the working components of the Game Engine.

The Engine Package contains most of the "moving parts" of the Game World. It
    implements the Space Class, as well as all Coordinate systems that fall
    under it, and the Spacetime Class, which applies the concept of Time to
    Space.
"""

from asyncio import CancelledError, sleep
from datetime import datetime as dt, timedelta as td
from inspect import isabstract, isawaitable
from itertools import filterfalse
from typing import Dict, Iterable, Iterator, List, Type, Union

from .objects import Object
from .physics import Spacetime
from .space import Coordinates, Space
from .space.base import Serial, Serializable
from .world import MultiSystem, System


def get_subs(t: type) -> Iterator[type]:
    yield from map(get_subs, t.__subclasses__())


# Recursively check for Subclasses to map out all Types that should implement a
#   .from_serial() Classmethod.
MAP: Dict[str, Type[...]] = {
    t.__name__: t for t in filterfalse(isabstract, get_subs(Serializable))
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


async def run_world(st: Spacetime, turn_length: int = 300, echo=print):
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
            st.progress(turn_length)
            await run_iter(CB_POST_TICK)

            echo("Simulation complete.")

    except CancelledError:
        echo("Simulation Coroutine cancelled. Saving...")
    finally:
        # st.save_to_file()
        echo("Spacetime Saved.")
