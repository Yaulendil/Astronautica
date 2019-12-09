from datetime import datetime as dt
from pathlib import Path
from secrets import token_hex
from typing import Dict, Iterator, NewType, Optional, overload, Type, Union

from config import cfg
from util.storage import PersistentDict


AccessKey: Type[str] = NewType("Access Key", str)
KEYS: Dict[AccessKey, Dict[str, Optional[str]]] = PersistentDict(
    Path(cfg["data/directory"], "KEYS").with_suffix(".json"), fmt="json"
)


def _generate_token(chunks: int = 3, size: int = 5, div: str = "-") -> AccessKey:
    return AccessKey(
        div.join(
            token_hex(chunks * size).upper()[i * size: (i + 1) * size]
            for i in range(chunks)
        )
    )


def key_assign(keystr: AccessKey, user: PersistentDict):
    with KEYS:
        if user.get("key"):
            raise ValueError("User is already assigned a Key.")
        elif (key := KEYS[keystr])["user"]:
            raise ValueError("Key is already assigned to a User.")
        else:
            user["key"] = keystr
            key["user"] = user["name"].lower()
            key["claimed"] = dt.utcnow().replace(microsecond=0).isoformat()


@overload
def key_free(key: AccessKey):
    ...


@overload
def key_free(user: PersistentDict):
    ...


# noinspection PyTypeChecker
def key_free(obj: Union[AccessKey, PersistentDict]):
    with KEYS:
        if isinstance(obj, str):
            keystr = obj
            key = KEYS[keystr]
            user = user_get(key["user"] or "")

            if not user:
                raise ValueError("Key is not claimed.")

        elif isinstance(obj, dict):
            user = obj
            keystr = user["key"]

            if not keystr or keystr not in KEYS:
                raise ValueError("User does not have a valid Key.")
            else:
                key = KEYS[keystr]

        else:
            raise TypeError(f"Type of Argument ({type(obj).__name__!r}) invalid.")

        if key["user"].lower() != user["name"].lower() or user["key"] != keystr:
            raise ValueError("Registration inconsistency found; Check the DB.")
        else:
            key["claimed"] = None
            key["user"] = None
            user["key"] = None


def keys_new(n: int = 1, note: str = None) -> Iterator[AccessKey]:
    now: str = dt.utcnow().replace(microsecond=0).isoformat()
    with KEYS:
        for i in range(n):
            tk = _generate_token()
            KEYS[tk] = dict(
                batch_idx=i + 1, note=note, generated=now, claimed=None, user=None
            )
            yield tk


def user_get(name: str, make: bool = False) -> Optional[PersistentDict]:
    path = Path(cfg["data/directory"], "users", name.lower()).with_suffix(".json")

    if path.is_file() or make:
        return PersistentDict(path, fmt="json")


def user_new(name: str) -> PersistentDict:
    path = Path(cfg["data/directory"], "users", name.lower()).with_suffix(".json")

    if path.exists():
        raise FileExistsError
    else:
        return PersistentDict(path, fmt="json")
