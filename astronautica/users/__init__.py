from datetime import datetime as dt
from pathlib import Path
from secrets import token_hex
from typing import Dict, Iterator, NewType, Optional, Type

from ezipc.remote import Remote
from passlib.hash import pbkdf2_sha512 as pwh

from config import cfg
from util.storage import PersistentDict


AccessKey: Type[str] = NewType("Access Key", str)

keys: Dict[AccessKey, Optional[Dict[str, str]]] = PersistentDict(
    Path(cfg["data/directory"], "KEYS").with_suffix(".json"), fmt="json"
)
logins: Dict[str, "Session"] = {}


def generate_token(chunks: int = 3, size: int = 5, div: str = "-") -> AccessKey:
    tk = token_hex(chunks * size).upper()
    return AccessKey(div.join(tk[i * size : (i + 1) * size] for i in range(chunks)))


def get_user(name: str, make: bool = False):
    path = Path(cfg["data/directory"], "users", name).with_suffix(".json")

    if path.is_file():
        return PersistentDict(path, fmt="json")
    elif make:
        return new_user(name)
    else:
        raise FileNotFoundError


def new_keys(n: int = 1) -> Iterator[AccessKey]:
    with keys:
        for _ in range(n):
            tk = generate_token()
            keys[tk] = None
            yield tk


def new_user(name: str, exist_ok: bool = True):
    path = Path(cfg["data/directory"], "users", name).with_suffix(".json")

    if path.exists() and not exist_ok:
        raise FileExistsError
    else:
        return PersistentDict(path, fmt="json")


class Session(object):
    def __init__(self, remote: Remote):
        self.remote: Remote = remote
        self.user: Optional[PersistentDict] = None

    @property
    def active(self) -> bool:
        return self.remote.open

    def login(self, username: str, password: str) -> bool:
        user = get_user(username, False)
        if user:
            if pwh.verify(password, user.get("password")):
                self.user = user
                logins[self.user.path.stem] = self
                return True
            else:
                raise PermissionError("Bad Password")
        else:
            raise FileNotFoundError

    def logout(self):
        if self.user:
            del logins[self.user.path.stem]
            self.user = None

    def register(self, username: str, password: str, key: AccessKey):
        with keys:
            if key in keys and keys[key] is None:
                keys[key] = dict(time=dt.utcnow().isoformat(), username=username)

                with new_user(username, False) as user:
                    user["password"] = pwh.hash(password)
                    user["key"] = key
            else:
                raise PermissionError("Invalid Key")
