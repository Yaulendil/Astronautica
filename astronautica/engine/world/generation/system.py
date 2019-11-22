from pathlib import Path
from uuid import UUID

from ..gravity import MultiSystem, Orbit, System
from util.storage import PersistentDict


__all__ = ["generate_system"]


def generate_system(system: PersistentDict):
    if system:
        raise ValueError("System is not empty.")
