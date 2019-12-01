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


def approve_password(word: str) -> bool:
    if not 8 <= len(word):
        raise ValueError("Password must be at least 8 characters.")
    elif not len(word) <= 80:
        raise ValueError(
            "Your security is commendable, but passwords cannot be more than 80"
            " characters."
        )
    else:
        return True


def approve_username(name: str) -> bool:
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


def new_keys(n: int = 1) -> Iterator[AccessKey]:
    with KEYS:
        for _ in range(n):
            tk = generate_token()
            KEYS[tk] = None
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
        user = user_get(username)

        if not user or not pwh.verify(password, user.get("password", "")):
            raise PermissionError("Bad Username or Password")
        elif KEYS.get(user.get("key"), {}).get("user", True) != user.get("name"):
            raise PermissionError("Key Disabled")

        else:
            self.user = user
            self.name = username
            logins[user.path.stem] = self
            return True

    def logout(self):
        self.name: str = "nobody"
        self.host: str = "ingress"
        self.path: str = "/login"

        if self.user:
            del logins[self.user.path.stem]
            self.user = None

    def register(self, username: str, password: str, key: AccessKey) -> bool:
        approve_password(password)
        approve_username(username)

        with KEYS:
            if key in KEYS and KEYS[key] is None:
                with user_new(username) as user:
                    KEYS[key] = dict(time=dt.utcnow().isoformat(), user=username)
                    user["name"] = username
                    user["password"] = pwh.hash(password)
                    user["key"] = key

                    self.user = user
                    self.name = username

                    logins[user.path.stem] = self
                    return True
            else:
                raise PermissionError("Invalid Key")
