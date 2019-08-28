from shlex import shlex
from typing import Callable, Dict, List

from .client import Client


class CommandRoot(object):
    def __init__(self, client: Client):
        self.client: Client = client
        self.commands: Dict[str, Callable] = {}

    def run(self, command: str):
        sh = shlex(command)

        tokens: List[str] = list(sh)
        word = tokens.pop(0)

        if word in self.commands:
            self.commands[word](tokens)
