from enum import auto, Enum
from itertools import cycle
from typing import Callable, Dict, List, Sequence, Tuple, Union

from prompt_toolkit import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.document import Document
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
doc = Document("asdf@qwert~$ ")


class Prompt:
    def __init__(self, text: Sequence[Tuple[str, str]]):
        self.processor = BeforeInput(self)
        self.prompt = list(text)

    def __call__(self, text: str = ""):
        return FormattedText([*self.prompt, ("class:etc", text)])


def line(text: Union[List[Tuple[str, str]], str]) -> Window:
    win = Window(
        FormattedTextControl(text),
        dont_extend_height=True,
        ignore_content_width=True,
        wrap_lines=True,
    )
    return win


scrollback = FormattedTextControl(text=[])
cmd_panel = HSplit((line("asdf"),))


def echo(text: FormattedText):
    cmd_panel.children.append(line(text))


def keys(given: Dict[str, Callable] = None, *, defaults: bool = True) -> KeyBindings:
    kb = KeyBindings()

    if defaults:

        @kb.add("c-q")
        def close(event):
            """Ctrl-Q: Exit program."""
            event.app.exit()

    for k, v in given.items():
        kb.add(k)(v)

    return kb


class Mode(Enum):
    SCOPES = auto()
    SCANS = auto()
    ORDERS = auto()
    OFF = auto()


class Client:
    def __init__(self):
        self.kb = keys()
        # noinspection PyTypeChecker
        mode = cycle(Mode)
        self.state: Mode = next(mode)

        @self.kb.add("tab")
        def nextmode(*_):
            self.state = next(mode)

        self.prompt = Prompt(
            [
                ("class:hostname", "asdf@qwert"),
                ("class:etc", ":"),
                ("class:path", "~"),
                ("class:etc", "$ "),
            ]
        )

        self.app = None
        self.bar = FormattedTextControl("asdf qwert")
        self.cmd_line = Buffer(accept_handler=self.enter, multiline=False)

        self.scope_topdown = FormattedTextControl(text="TopDown")
        self.scope_horizon = FormattedTextControl(text="Horizon")
        self.scopes = HSplit(
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
        )
        self.scans = FormattedTextControl(text="Scans")
        self.orders = FormattedTextControl(text="Orders")

    def enter(self, buffer: Buffer):
        command: str = buffer.text
        buffer.reset(append_to_history=True)
        echo(self.prompt(command))

    def __enter__(self):
        if self.app:
            raise RuntimeError("Client already has an Application open.")
        root = VSplit(
            (
                # Command History on most of the left panel, Prompt at the bottom.
                HSplit(
                    (
                        cmd_panel,
                        Window(
                            BufferControl(self.cmd_line, [self.prompt.processor]),
                            wrap_lines=True,
                        ),
                    )
                ),
                ConditionalContainer(
                    VerticalLine(), Condition(lambda: self.state is not Mode.OFF)
                ),
                ConditionalContainer(
                    self.scopes, Condition(lambda: self.state is Mode.SCOPES)
                ),
                ConditionalContainer(
                    Window(self.scans, ignore_content_width=True),
                    Condition(lambda: self.state is Mode.SCANS),
                ),
                ConditionalContainer(
                    Window(self.orders, ignore_content_width=True),
                    Condition(lambda: self.state is Mode.ORDERS),
                ),
            )
        )
        self.app = Application(
            full_screen=True,
            key_bindings=self.kb,
            layout=Layout(
                HSplit(
                    (Window(self.bar, height=1, style="ansigray bold reverse"), root)
                )
            ),
            style=STYLE,
        )
        return self.app

    def __exit__(self, exc_type, exc_value, traceback):
        # self.app.exit()
        self.app = None
