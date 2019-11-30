from datetime import datetime as dt
from pathlib import Path
from re import compile
from secrets import token_hex
from typing import Dict, Iterator, NewType, Optional, Type

from ezipc.remote import Remote
from passlib.hash import pbkdf2_sha512 as pwh

from config import cfg
from util.storage import PersistentDict


AccessKey: Type[str] = NewType("Access Key", str)
chars_not_ok = compile(r"[^-_a-zA-Z0-9]")

KEYS: Dict[AccessKey, Optional[Dict[str, str]]] = PersistentDict(
    Path(cfg["data/directory"], "KEYS").with_suffix(".json"), fmt="json"
)
logins: Dict[str, "Session"] = {}


def approve(name: str) -> bool:
    if not 3 <= len(name) <= 20:
        raise ValueError("Username must be between 3 and 20 ASCII characters.")
    elif bad := set(chars_not_ok.findall(name)):
        raise ValueError(
            "Unacceptable character{}: {}".format(
                "" if len(bad) == 1 else "s", ", ".join(map(repr, bad))
            )
        )
    else:
        return True


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
    with KEYS:
        for _ in range(n):
            tk = generate_token()
            KEYS[tk] = None
            yield tk


def new_user(name: str, exist_ok: bool = True):
    path = Path(cfg["data/directory"], "users", name).with_suffix(".json")

    if path.exists() and not exist_ok:
        raise FileExistsError
    else:
        return PersistentDict(path, fmt="json")


class Session(object):
    __slots__ = (
        "remote",
        "user",
        "name",
        "host",
        "path",
    )

    def __init__(self, remote: Remote):
        self.remote: Remote = remote
        self.user: Optional[PersistentDict] = None

        self.name: str = "nobody"
        self.host: str = "ingress"
        self.path: str = "/login"

    @property
    def active(self) -> bool:
        return self.remote.open

    async def echo(self, *text: str):
        return await self.remote.notif("ETC.PRINT", text)

    async def sync(
        self, *, username: str = None, hostname: str = None, path: str = None
    ):
        self.name = username or self.name
        self.host = hostname or self.host
        self.path = path or self.path
        await self.remote.notif(
            "USR.SYNC",
            {"username": self.name, "hostname": self.host, "path": self.path},
        )

    def login(self, username: str, password: str) -> bool:
        user = get_user(username, False)
        if user:
            if pwh.verify(password, user.get("password")):
                self.user = user
                self.name = username
                logins[user.path.stem] = self
                return True
            else:
                raise PermissionError("Bad Password")
        else:
            raise FileNotFoundError("Nonexistent User")

    def logout(self):
        self.name: str = "nobody"
        self.host: str = "ingress"
        self.path: str = "/login"

        if self.user:
            del logins[self.user.path.stem]
            self.user = None

    def register(self, username: str, password: str, key: AccessKey) -> bool:
        if not approve(username):
            raise ValueError("Username does not meet specifications.")

        with KEYS:
            if key in KEYS and KEYS[key] is None:
                KEYS[key] = dict(time=dt.utcnow().isoformat(), username=username)

                with new_user(username, False) as user:
                    user["password"] = pwh.hash(password)
                    user["key"] = key

                    self.user = user
                    self.name = username

                    logins[user.path.stem] = self
                    return True
            else:
                raise PermissionError("Invalid Key")