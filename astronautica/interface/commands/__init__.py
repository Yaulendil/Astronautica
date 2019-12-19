# noinspection PyUnresolvedReferences
from functools import cached_property, partial, update_wrapper
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
from shlex import shlex
from string import ascii_lowercase
from typing import (
    Any,
    Callable,
    Dict,
    Final,
    get_args,
    get_origin,
    Iterator,
    List,
    Mapping,
    MutableSet,
    Optional,
    overload,
    Sequence,
    Set,
    Tuple,
    Type,
    Union,
)
from unicodedata import normalize

from prompt_toolkit.buffer import Buffer
from prompt_toolkit.completion import CompleteEvent, Completer, Completion
from prompt_toolkit.document import Document

from ..etc import cached, T
from .exceptions import (
    CommandError,
    CommandExists,
    CommandNotAvailable,
    CommandNotFound,
    CommandFailure,
    CommandBadArguments,
    CommandBadInput,
)


HEAD = T.bold
OPTION = T.italic_bright_black

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


def typestr(typ, subscript: bool = True) -> str:
    if isinstance(typ, type):
        return typ.__name__
    else:
        orig = get_origin(typ)
        if orig:
            args = get_args(typ)
            if args and subscript:
                return "{}[{}]".format(
                    orig.__name__.title(), ", ".join(map(typestr, args))
                )
            else:
                return orig.__name__.title()
        else:
            return str(typ)


class Command(object):
    """Command Object. Stores a Function and a Keyword, and provides a support
        interface for Subcommands.
    """

    __slots__ = (
        "__dict__",
        "_func",
        "bools",
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

    def __init__(self, func: CmdType, keyword: str, task: bool = False):
        self._func: Final[CmdType] = func

        self.keyword: str = simplify(keyword)
        self.KEYWORD: str = self.keyword.upper()
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

    @cached_property
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
                    opts = {
                        (k1 := k.strip("-")): (
                            True if k1 in self.bools else self._cast(k1, v)
                        )
                        for k, v in opts
                    }

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

        # This cannot Return, because the resulting Iterator must not terminate
        #   a Zip it is used in.
        yield from repeat(None)

    def _cast(self, key: str, value: Optional[str]):
        """Given a Key and a Value, cast the Value to the Type annotated for the
            Keyword Argument of the Key.
        """
        if key in self.bools:
            return bool(value)
        elif key in self.sig.parameters:
            wanted: Type = self.sig.parameters[key].annotation
            if wanted is not str and wanted is not Signature.empty:
                orig = get_origin(wanted) or wanted
                try:
                    if issubclass(orig, Mapping):
                        dat = (term.split("=", 1) for term in value.split(",") if term)
                        if isinstance(wanted, type):
                            value = wanted(dat)
                        else:
                            # noinspection PyTypeChecker
                            value = dict(dat)

                    elif issubclass(orig, Sequence):
                        args = get_args(wanted)
                        dat = [term for term in value.split(",") if term]

                        if issubclass(orig, tuple):
                            len_want = len(args)
                            len_have = len(dat)

                            if ... in args:
                                value = tuple(map(args[0], dat))
                            elif len_want == len_have:
                                value = tuple(
                                    a(b) if isinstance(a, type) else b
                                    for a, b in zip(args, dat)
                                )
                            else:
                                raise ValueError(
                                    f"Expected {len_want} Values, got {len_have}"
                                )

                        elif issubclass(orig, list) and args:
                            value = list(map(args[0], dat))

                        elif isinstance(orig, type):
                            value = orig(dat)
                        else:
                            value = dat

                    elif isinstance(wanted, type):
                        value = wanted(value)
                    else:
                        value = orig(value)

                except ValueError as e:
                    raise TypeError(
                        "Value {!r} cannot be cast to {}: {}".format(
                            value, typestr(wanted, False), e,
                        )
                    )

                except Exception as e:
                    # raise e
                    raise TypeError(
                        "Value {!r} cannot be cast to {}.".format(
                            value, typestr(wanted, False),
                        )
                    ) from e

        return value

    def _cast_args(self, args: Sequence[str]) -> Sequence:
        return tuple(self._cast(a, b) for a, b in zip(self._arguments, args))

    def add(self, command: "Command") -> None:
        if command.keyword in self.subcommands:
            raise CommandExists(f"Subcommand {command.KEYWORD!r} already exists.")
        else:
            self.subcommands[command.keyword] = command

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
                Command(func, name or func.__name__, task=task), func
            )
            self.add(cmd)
            return cmd

    @cached_property
    def _usage(self) -> str:
        helpstr = []

        if self.opts:
            helpstr.append(OPTION("(OPTIONS)"))

        for arg, param in self.sig.parameters.items():
            ptp = param.annotation
            rep = (
                "<{name}>" if ptp is param.empty or ptp is str else "<{type}:{name}>"
            ).format(name=arg.upper(), type=typestr(ptp),)

            if (
                param.kind is param.POSITIONAL_ONLY
                or param.kind is param.POSITIONAL_OR_KEYWORD
            ):
                helpstr.append(
                    rep if param.default is param.empty else OPTION(f"[{rep}]")
                )

            elif param.kind is param.VAR_POSITIONAL:
                helpstr.append(OPTION(f"[{rep}...]"))
                break

        return "  ".join(helpstr)

    @cached
    def usage(self, pre: str = None) -> str:
        return "{}  {}".format(HEAD(pre or self.KEYWORD), self._usage)

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}"
            f"({self._func},"
            f" {self.keyword!r},"
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
                    yield "{}\n    {}".format(
                        cmd.usage(full),
                        "\n    ".join(
                            sline
                            for line in doc.splitlines()
                            if (sline := line.strip())
                        )
                        if (doc := cmd.doc)
                        else "No Help available.",
                    )

                    if cmd.opts:
                        yield "\nOptions:"
                        for opt, param in cmd.sig.parameters.items():
                            if param.kind is param.KEYWORD_ONLY:
                                yield "{:>10} :: {}".format(
                                    f"--{opt}" if len(opt) > 1 else f"-{opt}",
                                    "str"
                                    if param.annotation is Signature.empty
                                    else typestr(param.annotation),
                                )

                    if cmd.subcommands:
                        yield f"\nSubcommands ({len(cmd.subcommands)}):" + "".join(
                            sub.usage(f"\n    {full} {name.upper()}")
                            + (
                                f"    (+{len(sub.subcommands)})"
                                if sub.subcommands
                                else ""
                            )
                            for name, sub in cmd.subcommands.items()
                        )
                else:
                    yield f"Command {path[0].upper()!r} not found."
            else:
                yield "Commands:"
                for cmd in sorted(self.commands.values(), key=lambda x: x.keyword):
                    yield (
                        f"    {cmd.usage()}"
                        + (f"    (+{len(cmd.subcommands)})" if cmd.subcommands else "")
                    )
            yield ""

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
                Command(func, name or func.__name__, task=task), func
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
        self._len = len(buf.text)

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
        if line:
            sh = shlex(line, posix=True, punctuation_chars=True)
            sh.wordchars += ":+,"
            out = list(sh)

            if line.endswith(" "):
                out.append("")

            return out
        else:
            return [""]

    def split_and_get(self, line: str) -> Tuple[Optional[Command], Sequence[str]]:
        return self.get_command(self.split(line))

    def get_completions(
        self, document: Document, complete_event: CompleteEvent
    ) -> Iterator[Completion]:
        if not complete_event.completion_requested:
            self.completion = ""
            return

        *most, word = self.split(document.text_before_cursor.lstrip())

        if most:
            cmd, trail = self.get_command(most, completing=True)
            if not cmd or cmd.keyword in self.disabled:
                return
            cmd_dict = cmd.completions
        else:
            cmd = trail = None
            cmd_dict = self.commands

        if word.startswith("-"):
            # User has started with a dash. Complete --Options, not Subcommands.
            complete_longs = complete_shorts = False
            cur = word.strip("-")
            keys = []

            if word == "-":
                # Term is ONLY A DASH so far. Complete both Longs and Shorts.
                complete_longs = complete_shorts = True
            elif word.startswith("--"):
                # Term begins with TWO dashes. Complete Longs only.
                complete_longs = True
            else:
                # Term is ONE dash, and then something. Complete Shorts only.
                complete_shorts = True

            if complete_shorts:
                if cur:
                    # Term could be valid as it is.
                    keys.append(word)

                if set(cur) <= cmd.bools:
                    # All Short Opts in the Term are Boolean; More Short Opts
                    #   can be added onto the end.
                    keys.extend(
                        word + shopt
                        for shopt in cmd.shorts
                        if shopt != ":" and shopt not in word
                    )

            if complete_longs:
                keys.extend(
                    "--" + p.rstrip("=")
                    for p in cmd.longs
                    if p.startswith(word.lstrip("-")) and p not in most
                )

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
                # If there is only one possibility, append a Space or `=`.
                yield Completion(
                    keys[0][len(word) :]
                    + (
                        "="
                        if keys[0].startswith("--")
                        and keys[0].strip("-") not in cmd.bools
                        else " "
                    )
                )
