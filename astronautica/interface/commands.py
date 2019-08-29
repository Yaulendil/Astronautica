from getopt import getopt
from inspect import Signature
from shlex import shlex
from typing import Callable, Dict, List, Sequence, Type

from .client import Client


CmdType: Type[Callable] = Callable


class Command(object):
    """Command Object. Stores a Function and a Keyword, and provides a support
        interface for Subcommands.
    """
    def __init__(self, func: Callable, keyword: str):
        self._func: Callable = func
        self.keyword: str = keyword
        self.subcommands: Dict[str, Command] = {}

        self.sig: Signature = Signature.from_callable(self._func)

        shorts = ""
        longs = []

        # TODO: Assemble Opts from Signature

        self.shorts: str = shorts
        self.longs: List[str] = longs

    def __call__(self, tokens: Sequence[str]):
        """Execute the Command. Takes a Sequence of Strings."""
        opts, args = getopt(tokens, self.shorts, self.longs)
        return self._func(*args, **opts)

    def add(self, command: "Command"):
        if command.keyword in self.subcommands:
            raise FileExistsError(f"Subcommand '{command.keyword}' already exists.")
        else:
            self.subcommands[command.keyword] = command

    def sub(self, keyword: str) -> Callable[[Callable], "Command"]:
        def make_command(func: CmdType) -> Command:
            cmd = Command(func, keyword)
            self.add(cmd)
            return cmd

        return make_command


class CommandRoot(object):
    def __init__(self, client: Client):
        self.client: Client = client
        self.commands: Dict[str, Command] = {}

    def __call__(self, keyword: str) -> Callable[[Callable], Command]:
        def make_command(func: CmdType) -> Command:
            cmd = Command(func, keyword)
            self.add(cmd)
            return cmd

        return make_command

    def add(self, command: Command):
        if command.keyword in self.commands:
            raise FileExistsError(f"Command '{command.keyword}' already exists.")
        else:
            self.commands[command.keyword] = command

    def run(self, line: str):
        sh = shlex(line)

        tokens: List[str] = list(sh)
        word = tokens.pop(0)

        if word in self.commands:
            self.commands[word](tokens)
        else:
            # TODO: Custom Exceptions
            raise NameError(f"Command '{word}' not found.")
