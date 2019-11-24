from functools import partial, update_wrapper
from getopt import getopt
from inspect import (
    isasyncgenfunction,
    isawaitable,
    iscoroutinefunction,
    Signature,
    unwrap,
)
from itertools import repeat
from re import compile
from string import ascii_lowercase
from unicodedata import normalize

from prompt_toolkit.buffer import Buffer
from prompt_toolkit.completion import CompleteEvent, Completer, Completion
from prompt_toolkit.document import Document
from shlex import shlex
from typing import (
    Any,
    Callable,
    Dict,
    Iterator,
    List,
    MutableSet,
    Optional,
    overload,
    Sequence,
    Set,
    Tuple,
    Type,
    Union,
)


_del_extra = partial(compile(fr"[^{ascii_lowercase}-]").sub, "")
_no_repeat = partial(compile(r"-{2,}").sub, "-")
_to_dashes = partial(compile(r"[\s_]").sub, "-")
CmdType: Type[Callable] = Callable[..., Any]


# Command Keyword Specifications:
#   Keyword is composed of lower case ASCII letters and dashes.
#   Keyword does NOT begin OR end with a dash.
#   Keyword does NOT contain multiple dashes consecutively.
simplify = lambda word: _no_repeat(
    _del_extra(_to_dashes(normalize("NFKD", word.casefold()))).strip("-")
)


class CommandError(Exception):
    """Base Class for problems with Commands."""


class CommandNotAvailable(CommandError):
    """Command cannot be used."""


class CommandNotFound(CommandError):
    """Command cannot be located."""


class CommandExists(CommandError):
    """Command cannot be added."""


class Command(object):
    """Command Object. Stores a Function and a Keyword, and provides a support
        interface for Subcommands.
    """

    __slots__ = (
        "__dict__",
        "_func",
        "bools",
        "client",
        "completions",
        "dispatch_task",
        "keyword",
        "KEYWORD",
        "longs",
        "opts",
        "shorts",
        "sig",
        "subcommands",
    )

    def __init__(self, func: CmdType, keyword: str, client, task: bool = False):
        self._func: CmdType = func

        self.keyword: str = simplify(keyword)
        self.KEYWORD: str = self.keyword.upper()
        self.client = client
        self.dispatch_task: bool = task

        self.subcommands: Dict[str, Command] = {}
        self.completions = self.subcommands

        self.sig: Signature = Signature.from_callable(self._func)

        self.shorts: str = ""
        self.longs: List[str] = []
        self.bools: Set[str] = set()
        self.opts: List[str] = []

        for opt, parameter in self.sig.parameters.items():
            if parameter.kind is parameter.KEYWORD_ONLY:
                if len(opt) > 1:
                    # Long Opt.
                    self.opts.append(f"--{opt}")

                    if parameter.annotation is bool or type(parameter.default) is bool:
                        self.longs.append(opt)
                        self.bools.add(opt)
                    else:
                        self.longs.append(f"{opt}=")
                else:
                    # Short Opt.
                    self.opts.append(f"-{opt}")

                    self.shorts += opt
                    if parameter.annotation is bool or type(parameter.default) is bool:
                        self.bools.add(opt)
                    else:
                        self.shorts += ":"

    @property
    def doc(self) -> str:
        return self._func.__doc__

    @property
    def is_async(self):
        true = unwrap(self._func)
        return (
            iscoroutinefunction(true) or isasyncgenfunction(true) or isawaitable(true)
        )

    def __call__(self, tokens: Sequence[str] = None):
        """Execute the Command. Takes a Sequence of Strings."""
        if tokens:
            subcmd = self.subcommands.get(tokens[0].casefold())

            if subcmd:
                return subcmd(tokens[1:])

            else:
                if self.opts:
                    opts, args = getopt(tokens, self.shorts, self.longs)
                    opts = {k.strip("-"): self._cast(k.strip("-"), v) for k, v in opts}

                    return self._func(*self._cast_args(args), **opts)
                else:
                    return self._func(*self._cast_args(tokens))
        else:
            return self._func()

    @property
    def _arguments(self) -> Iterator[str]:
        for arg, param in self.sig.parameters.items():
            if (
                param.kind is param.POSITIONAL_ONLY
                or param.kind is param.POSITIONAL_OR_KEYWORD
            ):
                yield arg

            elif param.kind is param.VAR_POSITIONAL:
                yield from repeat(arg)
                return

        yield from repeat(None)

    def _cast(self, key: str, value: Optional[str]):
        """Given a Key and a Value, cast the Value to the Type annotated for the
            Keyword Argument of the Key.
        """
        if key in self.bools:
            return bool(value)
        elif key in self.sig.parameters:
            wanted: Type = self.sig.parameters[key].annotation
            if (
                isinstance(wanted, type)
                and not issubclass(wanted, str)
                and wanted is not Signature.empty
            ):
                try:
                    return wanted(value)
                except Exception as e:
                    raise TypeError(
                        f"Value for Argument {key!r} cannot be cast to"
                        f" {wanted.__name__}: {value!r}"
                    ) from e
            else:
                return value
        else:
            return value

    def _cast_args(self, args: Sequence[str]) -> Sequence:
        return tuple(self._cast(a, b) for a, b in zip(self._arguments, args))

    def add(self, command: "Command") -> None:
        if command.keyword in self.subcommands:
            raise CommandExists(f"Subcommand {command.KEYWORD!r} already exists.")
        else:
            self.subcommands[command.keyword] = command

    def set_client(self, client):
        self.client = client
        for cmd in self.subcommands.values():
            cmd.set_client(client)

    @overload
    def sub(self, name: str) -> Callable[[CmdType], "Command"]:
        ...

    @overload
    def sub(self, func: Callable, name: str = None, task: bool = False) -> "Command":
        ...

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

    def usage(self, pre: str = None, *, sep: str = "  ") -> str:
        helpstr = [pre or self.KEYWORD]

        if self.opts:
            helpstr.append("[options]")

        for arg, param in self.sig.parameters.items():
            ptype = param.annotation
            rep = (
                "<{name}>" if ptype is param.empty else "<{type}:{name}>"
            ).format(name=arg.upper(), type=ptype.__name__)

            if (
                param.kind is param.POSITIONAL_ONLY
                or param.kind is param.POSITIONAL_OR_KEYWORD
            ):
                helpstr.append(rep if param.default is param.empty else f"[{rep}]")

            elif param.kind is param.VAR_POSITIONAL:
                helpstr.append(f"[{rep}...]")
                break

        return sep.join(helpstr)

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}"
            f"({self._func},"
            f" {self.keyword!r},"
            f" {self.client},"
            f" {self.dispatch_task})"
        )

    def __str__(self):
        return f"Command with Keyword {self.KEYWORD!r} which calls: {self._func}"


class CommandRoot(Completer):
    __slots__ = (
        "_len",
        "client",
        "commands",
        "completion",
        "disabled",
    )

    def __init__(self, client=None):
        self.client = client
        self.commands: Dict[str, Command] = {}

        self.completion: str = ""
        self.disabled: MutableSet[str] = set()

        self._len: int = 0

        @self("help")
        def _help(*path: str):
            if path:
                cmd, args = self.get_command(path)
                if cmd and args:
                    path = path[: -len(args)]

                full = " ".join(path).upper()
                if cmd:
                    yield "{}\r\n    {}".format(
                        cmd.usage(full),
                        "\r\n    ".join(
                            sline
                            for line in doc.splitlines()
                            if (sline := line.strip())
                        )
                        if (doc := cmd.doc)
                        else "No Help available.",
                    )

                    if cmd.opts:
                        yield "\r\nOptions:"

                        for opt, param in cmd.sig.parameters.items():
                            if param.kind is param.KEYWORD_ONLY:
                                yield "{:>10} :: {}".format(
                                    f"--{opt}" if len(opt) > 1 else f"-{opt}",
                                    "str"
                                    if param.annotation is Signature.empty
                                    else param.annotation.__name__
                                )

                    if cmd.subcommands:
                        yield "\r\nSubcommands:"
                        for name, sub in sorted(
                                cmd.subcommands.items(), key=(lambda x: x[0])
                        ):
                            yield sub.usage(f"    {full} {name.upper()}")
                else:
                    yield f"Command {path[0].upper()!r} not found."
            else:
                yield "Commands:"
                for cmd in sorted(self.commands.values(), key=lambda x: x.keyword):
                    yield f"    {cmd.usage()}"

        _help.completions = self.commands

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
            raise CommandExists(f"Command {command.KEYWORD!r} already exists.")
        else:
            self.commands[command.keyword] = command

    def cap_set(self, *, disable: Sequence[str] = None, enable: Sequence[str] = None):
        if disable:
            self.disabled |= set(disable)  # Add every Disabling String.
        if enable:
            self.disabled -= set(enable)  # Remove all Enabling Strings.

    def change(self, buf: Buffer):
        l = len(buf.text)

        # # if buf.text.endswith(" "):
        # if l < self._len:
        #     # Empty the Completion if the Buffer has decreased in length.
        #     self.completion = ""

        self._len = l

    def get_command(
        self, tokens: Union[List[str], Tuple[str, ...]], *, completing: bool = False,
    ) -> Tuple[Optional[Command], Sequence[str]]:
        cmd_dict = self.commands
        cmd = here = None

        while tokens and (cmd := cmd_dict.get(tokens[0].casefold())):
            here = cmd
            cmd_dict = here.completions if completing else here.subcommands
            tokens = tokens[1:]

        return here, tokens

    @staticmethod
    def split(line: str) -> List[str]:
        sh = shlex(line, posix=True, punctuation_chars=True)
        sh.wordchars += ":+"
        return list(sh)

    def split_and_get(self, line: str) -> Tuple[Optional[Command], Sequence[str]]:
        return self.get_command(self.split(line))

    def get_completions(
        self, document: Document, complete_event: CompleteEvent
    ) -> Iterator[Completion]:
        if complete_event.text_inserted:
            self.completion = ""
            return

        line = document.text_before_cursor.lstrip()
        tokens = self.split(line)

        if line.endswith(" "):
            tokens.append("")

        if tokens:
            most, word = tokens[:-1], tokens[-1]
        else:
            most, word = [], line

        if most:
            cmd, trail = self.get_command(most, completing=True)
            if not cmd or cmd.keyword in self.disabled:
                return
            cmd_dict = cmd.completions
        else:
            cmd = trail = None
            word = line
            cmd_dict = self.commands

        if word.startswith("-"):
            # User has started with a dash. Complete --Options, not Subcommands.
            if cmd and all(t.startswith("-") for t in trail):
                keys = [p for p in cmd.opts if p.startswith(word) and p not in most]
            else:
                keys = []

        elif not trail:
            # User has not started with a dash, and has not entered any other
            #   Arguments after the last Command Term. Complete Subcommands.
            keys = [p for p in sorted(cmd_dict.keys()) if p.startswith(word)]

        else:
            # User has entered some input beyond the last Command Term. Do not
            #   perform Completion.
            return

        if len(keys) > 1:
            self.completion = "<TAB> / " + ", ".join(keys)
            yield from (Completion(possible[len(word) :]) for possible in keys)
        else:
            self.completion = ""
            if keys:
                # If there is only one possibility, append a Space.
                yield Completion(keys[0][len(word) :] + " ")

    def set_client(self, client):
        self.client = client
        for cmd in self.commands.values():
            cmd.set_client(client)
