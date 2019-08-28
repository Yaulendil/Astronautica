from enum import auto, Enum
from itertools import cycle
from typing import Callable, Dict, Union

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
from prompt_toolkit.widgets import HorizontalLine, VerticalLine


STYLE = Style([("etc", ""), ("hostname", "fg:ansicyan"), ("path", "fg:ansiblue bold")])


def line(text: Union[FormattedText, str]) -> Window:
    win = Window(
        FormattedTextControl(text),
        dont_extend_height=True,
        ignore_content_width=True,
        wrap_lines=True,
    )
    return win


def keys(given: Dict[str, Callable] = None, *, defaults: bool = True) -> KeyBindings:
    kb = KeyBindings()

    if defaults:

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


class Prompt:
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

    def __call__(self, text: str = None) -> FormattedText:
        if text is None:
            return self.prompt
        else:
            p = self.prompt
            p.append(("class:etc", text))
            return p


class Client:
    def __init__(self, command_handler: Callable = None):
        self.kb = keys()
        # noinspection PyTypeChecker
        mode = cycle(Mode)
        self.state: Mode = next(mode)

        @self.kb.add("tab")
        def nextmode(*_):
            self.state = next(mode)

        self.prompt = Prompt("anon", "ingress", "/login")

        self.bar = FormattedTextControl("asdf qwert")
        self.cmd = Buffer(accept_handler=self.enter, multiline=False)
        self.panel = HSplit((line("Interface ready."),))

        self.scope_topdown = FormattedTextControl(text="TopDown")
        self.scope_horizon = FormattedTextControl(text="Horizon")
        self.scans = FormattedTextControl(text="Scans")
        self.orders = FormattedTextControl(text="Orders")

        self.handler = command_handler

    def echo(self, *text: Union[FormattedText, str]):
        lines = [line(l) for l in text]
        self.panel.children += lines
        return lines

    def enter(self, buffer: Buffer):
        command: str = buffer.text
        buffer.reset(append_to_history=True)
        self.execute(command)

    def execute(self, command: str):
        self.echo(self.prompt(command))

        if callable(self.handler):
            self.handler(command)

    def __enter__(self):
        root = VSplit(
            (
                # Command History on most of the left panel, Prompt at the bottom.
                HSplit(
                    (
                        self.panel,
                        Window(
                            BufferControl(self.cmd, [self.prompt.processor]),
                            wrap_lines=True,
                        ),
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
        return Application(
            full_screen=True,
            key_bindings=self.kb,
            layout=Layout(
                HSplit(
                    (Window(self.bar, height=1, style="ansigray bold reverse"), root)
                )
            ),
            style=STYLE,
        )

    def __exit__(self, exc_type, exc_value, traceback):
        pass
        # self.app.exit()
        # self.app = None
