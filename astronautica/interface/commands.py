from functools import partial, update_wrapper

# from getopt import getopt
from inspect import Parameter, Signature
from shlex import shlex
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Sequence,
    Set,
    Tuple,
    Type,
    Union,
    Optional,
)


CmdType: Type[Callable] = Callable[..., Any]


class CommandError(Exception):
    """Base Class for problems with Commands."""


class CommandNotFound(CommandError):
    """Command cannot be located."""


class CommandExists(CommandError):
    """Command cannot be added."""


class Command(object):
    """Command Object. Stores a Function and a Keyword, and provides a support
        interface for Subcommands.
    """

    def __init__(self, func: CmdType, keyword: str, client, task: bool = False):
        self._func: CmdType = func
        self.keyword: str = keyword.lower()
        self.KEYWORD: str = keyword.upper()
        self.client = client
        self.dispatch_task: bool = task

        self.subcommands: Dict[str, Command] = {}

        self.sig: Signature = Signature.from_callable(self._func)

        self.shorts: str = ""
        self.longs: List[str] = []
        self.bools: Set[str] = set()

        self.params: List[Tuple[str, Parameter]] = self.sig.parameters.items()

        # for k, p in self.params:
        #     if p.kind is p.KEYWORD_ONLY:
        #         if len(k) > 1:
        #             # Long Opt.
        #             if p.annotation is not bool and type(p.default) is not bool:
        #                 self.longs.append(f"{k}=")
        #             else:
        #                 self.longs.append(k)
        #                 self.bools.add(k)
        #         else:
        #             # Short Opt.
        #             self.shorts += k
        #             if p.annotation is not bool and type(p.default) is not bool:
        #                 self.shorts += ":"
        #             else:
        #                 self.bools.add(k)
        #     else:
        #         pass

    def __call__(self, tokens: Sequence[str]):
        """Execute the Command. Takes a Sequence of Strings."""
        # opts, args = getopt(tokens, self.shorts, self.longs)
        # opts = {k: (True if k in self.bools else v) for k, v in opts}
        # return self._func(*args, **opts)

        if tokens:
            func = self.subcommands.get(tokens[0].lower())
            if func:
                return func(tokens[1:])
            else:
                return self._func(*tokens)
        else:
            return self._func()

    def add(self, command: "Command") -> None:
        if command.keyword in self.subcommands:
            raise CommandExists(f"Subcommand '{command.KEYWORD}' already exists.")
        else:
            self.subcommands[command.keyword] = command

    def set_client(self, client):
        self.client = client
        for cmd in self.subcommands.values():
            cmd.set_client(client)

    def sub(
        self, func: Union[Callable, str] = None, name: str = None, task: bool = False
    ) -> Union[Callable[[CmdType], "Command"], "Command"]:
        if func is None:
            # noinspection PyTypeChecker
            return partial(self.sub, name=name, task=task)

        elif isinstance(func, str):
            # noinspection PyTypeChecker
            return partial(self.sub, name=func, task=task)

        elif isinstance(func, Callable):
            cmd: Command = update_wrapper(
                Command(func, name or func.__name__, self.client, task=task), func
            )
            self.add(cmd)
            return cmd

    def __str__(self):
        return f"Command with Keyword {self.KEYWORD!r} which calls: {self._func}"


class CommandRoot(object):
    def __init__(self, client=None):
        self.client = client
        self.commands: Dict[str, Command] = {}

    def __call__(
        self, func: Union[Callable, str] = None, name: str = None, task: bool = False
    ) -> Union[Callable[[CmdType], Command], Command]:
        if func is None:
            # noinspection PyTypeChecker
            return partial(self, name=name, task=task)

        elif isinstance(func, str):
            # noinspection PyTypeChecker
            return partial(self, name=func, task=task)

        elif isinstance(func, Callable):
            cmd: Command = update_wrapper(
                Command(func, name or func.__name__, self.client, task=task), func
            )
            self.add(cmd)
            return cmd

    def add(self, command: Command) -> None:
        if command.keyword in self.commands:
            raise CommandExists(f"Command '{command.KEYWORD}' already exists.")
        else:
            self.commands[command.keyword] = command

    def get_command(self, line: str) -> Tuple[Optional[Command], List[str]]:
        if line:
            sh = shlex(line, posix=True, punctuation_chars=True)
            sh.wordchars += ":+"
            tokens: List[str] = list(sh)

            cmd_dict, here = self.commands, None

            while tokens and tokens[0] in cmd_dict:
                here = cmd_dict[tokens[0]]
                cmd_dict = here.subcommands
                tokens = tokens[1:]

            return here, tokens

        else:
            return None, []

    def set_client(self, client):
        self.client = client
        for cmd in self.commands.values():
            cmd.set_client(client)
