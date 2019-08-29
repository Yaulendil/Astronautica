# from getopt import getopt
from inspect import Parameter, Signature
from shlex import shlex
from typing import Callable, Dict, List, Sequence, Set, Tuple, Type


CmdType: Type[Callable] = Callable


class Command(object):
    """Command Object. Stores a Function and a Keyword, and provides a support
        interface for Subcommands.
    """

    def __init__(self, func: Callable, keyword: str):
        self._func: Callable = func
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

        kw = tokens[0].lower()
        if kw in self.subcommands:
            return self.subcommands[kw](tokens[1:])
        else:
            return self._func(*tokens)

    def add(self, command: "Command"):
        if command.keyword in self.subcommands:
            raise FileExistsError(f"Subcommand '{command.KEYWORD}' already exists.")
        else:
            self.subcommands[command.keyword] = command

    def sub(self, keyword: str) -> Callable[[Callable], "Command"]:
        def make_command(func: CmdType) -> Command:
            cmd = Command(func, keyword)
            self.add(cmd)
            return cmd

        return make_command


class CommandRoot(object):
    def __init__(self):
        self.commands: Dict[str, Command] = {}

    def __call__(self, keyword: str) -> Callable[[Callable], Command]:
        def make_command(func: CmdType) -> Command:
            cmd = Command(func, keyword)
            self.add(cmd)
            return cmd

        return make_command

    def add(self, command: Command):
        if command.keyword in self.commands:
            raise FileExistsError(f"Command '{command.KEYWORD}' already exists.")
        else:
            self.commands[command.keyword] = command

    def run(self, line: str):
        sh = shlex(line)

        tokens: List[str] = list(sh)
        word = tokens.pop(0).lower()

        if word in self.commands:
            self.commands[word](tokens)
        else:
            # TODO: Custom Exceptions
            raise NameError(f"Command '{word.upper()}' not found.")
