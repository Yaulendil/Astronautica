from asyncio import AbstractEventLoop, Task
from enum import auto, Enum
from itertools import cycle
from typing import List, Optional, Union

from prompt_toolkit import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.filters import Condition
from prompt_toolkit.formatted_text import FormattedText, fragment_list_to_text
from prompt_toolkit.layout.containers import (
    ConditionalContainer,
    HSplit,
    VSplit,
    Window,
)
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.layout.processors import BeforeInput
from prompt_toolkit.widgets import HorizontalLine, VerticalLine
from ptterm import Terminal

from .commands import CommandRoot
from .etc import keys, STYLE, unstyle
from .execution import execute_function


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

    def raw(self, append: str = "") -> str:
        return "{}{}:{}{}{}".format(
            self.prefix,
            unstyle["class:hostname"](f"{self.username}@{self.hostname}"),
            unstyle["class:path"](self.path),
            self.char,
            append,
        )

    def __call__(
        self, text: Union[FormattedText, str] = None, style="class:etc"
    ) -> FormattedText:
        if text is None:
            return self.prompt
        elif isinstance(text, FormattedText):
            return self.prompt + text
        else:
            return self.prompt + [(style, str(text))]


class Client(object):
    def __init__(self, loop: AbstractEventLoop, command_handler: CommandRoot = None):
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
        self.prompt = Prompt("nobody", "ingress", "/login")

        # Build the UI.
        self.bar = FormattedTextControl("asdf qwert")
        self.cmd = Buffer(
            accept_handler=self.enter,
            multiline=False,
            read_only=Condition(lambda: self.read_only),
        )
        self.term = Terminal(sim_prompt=True)
        self.console = self.term.terminal_control.process.terminal

        self.procs = [self.prompt.processor]
        self._procs = self.procs.copy()

        self.scope_topdown = FormattedTextControl(text="TopDown")
        self.scope_horizon = FormattedTextControl(text="Horizon")
        self.scans = FormattedTextControl(text="Scans")
        self.orders = FormattedTextControl(text="Orders")

        # Register the Command Handler.
        self.handler = command_handler
        self._app: Optional[Application] = None

        self.echo("Ready.", start="")

    def cmd_hide(self):
        self.read_only = True
        self._procs.clear()

    def cmd_show(self, *_):
        self.read_only = False
        self._procs[:] = self.procs
        self.redraw()

    def echo(self, *text, sep: str = "\r\n", start: str = "\r\n"):
        self.console.write_text(
            start
            + sep.join(
                fragment_list_to_text(line)
                if isinstance(line, FormattedText)
                else str(line)
                for line in text
            )
        )
        self.redraw()

    def enter(self, buffer: Buffer) -> None:
        command: str = buffer.text
        buffer.reset(append_to_history=True)

        self.execute(command)

    def execute(self, line: str, no_hide: bool = False) -> None:
        self.echo(self.prompt.raw(line))
        if not no_hide:
            self.cmd_hide()

        if self.handler:
            execute_function(line, self.echo, self.handler, self.LOOP, self.TASKS)
        else:
            self.echo("No handler.")

    def redraw(self) -> None:
        self.console.ready()
        if self._app:
            self._app.renderer.render(self._app, self._app.layout)

    def __enter__(self) -> Application:
        root = Layout(
            HSplit(
                (
                    Window(self.bar, height=1, style="ansigray bold reverse"),
                    VSplit(
                        (
                            # Command History on most of the left panel, Prompt at the bottom.
                            HSplit(
                                (
                                    self.term,
                                    Window(
                                        BufferControl(self.cmd, self._procs),
                                        wrap_lines=True,
                                        height=1,
                                    ),
                                )
                            ),
                            ConditionalContainer(  # Vertical Line.
                                VerticalLine(),
                                Condition(lambda: self.state is not Mode.OFF),
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
                    ),
                )
            )
        )
        root.focus(self.cmd)
        self._app = Application(root, STYLE, full_screen=True, key_bindings=self.kb)
        return self._app

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        # pass
        # self.app.exit()
        self._app = None
