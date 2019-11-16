from pathlib import Path
from secrets import token_hex
from typing import Dict

from ezipc.remote import Remote
from passlib.hash import pbkdf2_sha512 as pwh

from config import cfg
from util.storage import PersistentDict


check_token = lambda tk, i: int(tk.replace("-", ""), base=16) == i
logins: Dict[str, "Session"] = {}


def generate_token():
    tk = token_hex(12).upper()
    o = []

    while tk:
        o.append(tk[:4])
        tk = tk[4:]

    return "-".join(tk)


def get_user(name: str):
    path = Path(cfg["data/directory"], "users", name).with_suffix(".json")
    if path.is_file():
        return PersistentDict(path, fmt="json")


def new_user(name: str):
    path = Path(cfg["data/directory"], "users", name).with_suffix(".json")

    if path.exists():
        raise FileExistsError
    else:
        return PersistentDict(path, flag="n", fmt="json")


class Session(object):
    def __init__(self, remote: Remote):
        self.remote: Remote = remote
        self.user = None

    def active(self) -> bool:
        return self.remote.open

    def login(self, username: str, password: str) -> bool:
        user = get_user(username)
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

    def register(self, username: str, password: str, key: str):
        # TODO: Require valid Key Token before allowing Registration.
        user = new_user(username)
        user["password"] = pwh.hash(password)
