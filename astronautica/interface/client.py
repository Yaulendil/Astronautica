from asyncio import AbstractEventLoop, Task
from enum import auto, Enum
from itertools import chain, cycle
from typing import Any, Callable, Dict, List, Optional, Union

from prompt_toolkit import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.filters import Condition
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.containers import (
    ConditionalContainer,
    HSplit,
    VSplit,
    Window,
)
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.layout.processors import BeforeInput
from prompt_toolkit.styles import Style
from prompt_toolkit.utils import Event
from prompt_toolkit.widgets import HorizontalLine, VerticalLine

from .execution import execute_function


STYLE = Style([("etc", ""), ("hostname", "fg:ansicyan"), ("path", "fg:ansiblue bold")])


def fmt(text: Union[FormattedText, str], style: str = "class:etc") -> FormattedText:
    if isinstance(text, FormattedText):
        return text
    else:
        return FormattedText([(style, text)])


N = fmt("\n")


def line(text: Union[FormattedText, str]) -> Window:
    win = Window(
        FormattedTextControl(text),
        dont_extend_height=True,
        ignore_content_width=True,
        wrap_lines=True,
    )
    return win


def keys(
    given: Dict[str, Callable[[Event], Any]] = None, *, bind_defaults: bool = True
) -> KeyBindings:
    kb = KeyBindings()

    if bind_defaults:

        @kb.add("c-q")
        def close(event):
            """Ctrl-Q: Exit program."""
            event.app.exit()

    if given:
        for k, v in given.items():
            kb.add(k)(v)

    return kb


class Mode(Enum):
    SCOPES = auto()
    SCANS = auto()
    ORDERS = auto()
    OFF = auto()


class Prompt(object):
    def __init__(
        self,
        username: str,
        host: str,
        path: str = "~",
        *,
        namestyle: str = None,
        prefix: str = "",
    ):
        self.username: str = username
        self.hostname: str = host
        self.path: str = path

        self.namestyle: str = namestyle
        self.prefix: str = prefix
        self.processor = BeforeInput(self)

        self.char: str = "$ "

    # @property
    # def char(self):
    #     return "# " if self.username.lower() == "root" else "$ "

    @property
    def prompt(self) -> FormattedText:
        return FormattedText(
            [
                ("class:etc", self.prefix),
                (
                    "class:hostname" if self.namestyle is None else self.namestyle,
                    f"{self.username}@{self.hostname}",
                ),
                ("class:etc", ":"),
                ("class:path", self.path),
                ("class:etc", self.char),
            ]
        )

    def __call__(
        self, text: Union[FormattedText, str] = None, style="class:etc"
    ) -> FormattedText:
        if text is None:
            return self.prompt
        elif isinstance(text, FormattedText):
            return self.prompt + text
        else:
            p = self.prompt
            p.append((style, text))
            return p


class Panel(object):
    def __init__(self):
        self.text = FormattedText([("class:etc", "Ready")])
        self.ftc = FormattedTextControl(self.text)
        self.window = Window(
            self.ftc,
            dont_extend_height=True,
            ignore_content_width=True,
            wrap_lines=True,
        )

    def write(self, *text, newline: bool = True):
        self.text.extend(
            chain(*((N + fmt(t) for t in text) if newline else map(fmt, text)))
        )


class Client(object):
    def __init__(self, loop: AbstractEventLoop, command_handler: Callable = None):
        self.LOOP: AbstractEventLoop = loop
        self.TASKS: List[Task] = []

        self.read_only = False
        self.kb = keys()
        # noinspection PyTypeChecker
        mode = cycle(Mode)
        self.state: Mode = next(mode)

        @self.kb.add("tab")
        def nextmode(*_) -> None:
            self.state = next(mode)

        # Create a Prompt Object with initial values.
        self.prompt = Prompt("anon", "ingress", "/login")

        # Build the UI.
        self.bar = FormattedTextControl("asdf qwert")
        self.cmd = Buffer(
            accept_handler=self.enter,
            multiline=False,
            read_only=Condition(lambda: self.read_only),
        )
        self.panel = Panel()  # HSplit((line("Interface ready."),))
        self.procs = [self.prompt.processor]
        self._procs = self.procs.copy()

        self.scope_topdown = FormattedTextControl(text="TopDown")
        self.scope_horizon = FormattedTextControl(text="Horizon")
        self.scans = FormattedTextControl(text="Scans")
        self.orders = FormattedTextControl(text="Orders")

        # Register the Command Handler.
        self.handler = command_handler
        self._app: Optional[Application] = None

    def cmd_hide(self):
        self.read_only = True
        self._procs.clear()

    def cmd_show(self):
        self.read_only = False
        self._procs[:] = self.procs

    def echo(self, *text: Union[FormattedText, str]):  # -> List[Window]:
        # lines = list(filter(None, (line(l) for l in text)))
        self.panel.write(*map(fmt, text))
        self.redraw()
        # return lines

    def enter(self, buffer: Buffer) -> None:
        try:
            self.cmd_hide()
            command: str = buffer.text
            buffer.reset(append_to_history=True)

            self.execute(command)
        finally:
            self.cmd_show()

    def execute(self, command: str) -> None:
        self.echo(self.prompt(command))

        if callable(self.handler):
            execute_function(command, self.echo, self.handler, self.LOOP, self.TASKS)

    def redraw(self) -> None:
        if self._app:
            self._app.renderer.render(self._app, self._app.layout)

    def __enter__(self) -> Application:
        root = VSplit(
            (
                # Command History on most of the left panel, Prompt at the bottom.
                HSplit(
                    (
                        self.panel.window,
                        Window(BufferControl(self.cmd, self._procs), wrap_lines=True),
                    )
                ),
                ConditionalContainer(  # Vertical Line.
                    VerticalLine(), Condition(lambda: self.state is not Mode.OFF)
                ),
                ConditionalContainer(  # Scopes Panel. Visualizes nearby Space.
                    HSplit(
                        (
                            # Top-down visualization on the upper panel.
                            Window(
                                self.scope_topdown,
                                ignore_content_height=True,
                                ignore_content_width=True,
                            ),
                            HorizontalLine(),
                            # Visualization from behind on the lower panel.
                            Window(
                                self.scope_horizon,
                                ignore_content_height=True,
                                ignore_content_width=True,
                            ),
                        )
                    ),
                    Condition(lambda: self.state is Mode.SCOPES),
                ),
                ConditionalContainer(  # Scans Panel. Lists nearby Objects.
                    Window(self.scans, ignore_content_width=True),
                    Condition(lambda: self.state is Mode.SCANS),
                ),
                ConditionalContainer(  # Orders Panel. Shows future actions.
                    Window(self.orders, ignore_content_width=True),
                    Condition(lambda: self.state is Mode.ORDERS),
                ),
            )
        )
        self._app = Application(
            Layout(
                HSplit(
                    (Window(self.bar, height=1, style="ansigray bold reverse"), root)
                )
            ),
            STYLE,
            full_screen=True,
            key_bindings=self.kb,
        )
        return self._app

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        # pass
        # self.app.exit()
        self._app = None
