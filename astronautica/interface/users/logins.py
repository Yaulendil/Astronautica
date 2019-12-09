from re import compile
from typing import Dict, Optional

from ezipc.remote import Remote
from passlib.hash import pbkdf2_sha512 as pwh

from .tokens import AccessKey, KEYS, key_assign, user_get, user_new
from util.storage import PersistentDict


chars_not_ok = compile(r"[^-_a-zA-Z0-9]")
LOGINS: Dict[str, "Session"] = {}


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
            LOGINS[user.path.stem] = self
            return True

    def logout(self):
        self.name: str = "nobody"
        self.host: str = "ingress"
        self.path: str = "/login"

        if self.user:
            del LOGINS[self.user.path.stem]
            self.user = None

    def register(self, username: str, password: str, key: AccessKey) -> bool:
        approve_password(password)
        approve_username(username)

        with KEYS:
            if key in KEYS and KEYS[key].get("user") is None:
                with user_new(username) as user:
                    user["name"] = username
                    user["password"] = pwh.hash(password)
                    key_assign(key, user)

                    self.user = user
                    self.name = username

                    LOGINS[user.path.stem] = self
            else:
                raise PermissionError("Invalid Key")
        return True
