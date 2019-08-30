from functools import partial, update_wrapper

# from getopt import getopt
from inspect import Parameter, Signature
from shlex import shlex
from typing import Any, Callable, Dict, List, Sequence, Set, Tuple, Type, Union


CmdType: Type[Callable] = Callable[..., Any]


class Command(object):
    """Command Object. Stores a Function and a Keyword, and provides a support
        interface for Subcommands.
    """

    def __init__(self, func: CmdType, keyword: str):
        self._func: CmdType = func
        self.keyword: str = keyword.lower()
        self.KEYWORD: str = keyword.upper()
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
            raise FileExistsError(f"Subcommand '{command.KEYWORD}' already exists.")
        else:
            self.subcommands[command.keyword] = command

    def sub(
        self, arg: Union[Callable, str]
    ) -> Union[Callable[[CmdType], "Command"], "Command"]:
        def make_command(func: CmdType, name: str) -> Command:
            cmd: Command = update_wrapper(Command(func, name), func)
            self.add(cmd)
            return cmd

        if isinstance(arg, Callable):
            return make_command(arg, arg.__name__)

        else:
            return partial(make_command, name=arg)


class CommandRoot(object):
    def __init__(self):
        self.commands: Dict[str, Command] = {}

    def __call__(
        self, arg: Union[Callable, str]
    ) -> Union[Callable[[CmdType], Command], Command]:
        def make_command(func: CmdType, name: str) -> Command:
            cmd: Command = update_wrapper(Command(func, name), func)
            self.add(cmd)
            return cmd

        if isinstance(arg, Callable):
            return make_command(arg, arg.__name__)

        else:
            return partial(make_command, name=arg)

    def add(self, command: Command) -> None:
        if command.keyword in self.commands:
            raise FileExistsError(f"Command '{command.KEYWORD}' already exists.")
        else:
            self.commands[command.keyword] = command

    def run(self, line: str):
        if line:
            sh = shlex(line)

            tokens: List[str] = list(sh)
            word = tokens.pop(0).lower()

            if word in self.commands:
                return self.commands[word](tokens)
            else:
                # TODO: Custom Exceptions
                raise NameError(f"Command '{word.upper()}' not found.")
