"""Package containing the working components of the Physics Engine.

The Spacetime Package contains abstract classes and handlers that expose
    interactions. Another Package will contain implementations of the abstract
    classes, such as vehicles and weaponry.
"""

from asyncio import CancelledError, sleep
from datetime import datetime as dt, timedelta as td
from typing import List, Union

from .objects import Object
from .physics import Coordinates, Space, Spacetime
from .world import MultiSystem, System
from _abc import Serial


# This List MUST contain every Type which can be Serialized. It serves as the
#   seed from which the Deserialization Map is built. Only Objects whose Types
#   are in this List are able to be reconstructed.
SERIALS = [Coordinates, MultiSystem, Object, System]
MAP = lambda: {t.__name__: t for t in SERIALS}


def deserialize(obj: Union[List[Serial], Serial]):
    if isinstance(obj, list):
        return list(map(deserialize, obj))

    classname: str = obj.get("class")
    cls = MAP().get(classname)

    if cls is not None:
        data = obj.get("data")
        subs = {k: deserialize(v) for k, v in obj.get("subs", {}).items()}
        return cls.from_serial(data, subs)
    else:
        return None


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
            st.progress(turn_length)
            echo("Simulation complete.")

    except CancelledError:
        echo("Simulation Coroutine cancelled. Saving...")
    finally:
        # st.save_to_file()
        echo("Spacetime Saved.")
