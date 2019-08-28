from enum import auto, Enum
from itertools import cycle

from blessings import Terminal
from prompt_toolkit import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.filters import Condition
from prompt_toolkit.layout.containers import (
    ConditionalContainer,
    HSplit,
    VSplit,
    Window,
)
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.widgets import HorizontalLine, VerticalLine


T = Terminal()

scrollback = FormattedTextControl(text="Command History")
cmd_panel = Window(
    scrollback, dont_extend_height=True, ignore_content_width=True, wrap_lines=True
)


def echo(text: str):
    scrollback.text += f"\n{text}"


def enter(buffer: Buffer):
    command: str = buffer.text
    buffer.append_to_history()
    buffer.reset()
    echo(command)


cmd_line = Buffer(accept_handler=enter, multiline=False)


kb = KeyBindings()


@kb.add("c-q")
def close(event):
    """Ctrl-Q: Exit program."""
    event.app.exit()


scope_topdown = FormattedTextControl(text="TopDown")
scope_horizon = FormattedTextControl(text="Horizon")
scopes = HSplit(
    (
        # Top-down visualization on the upper panel.
        Window(scope_topdown, ignore_content_height=True, ignore_content_width=True),
        HorizontalLine(),
        # Visualization from behind on the lower panel.
        Window(scope_horizon, ignore_content_height=True, ignore_content_width=True),
    )
)


scans = FormattedTextControl(text="Scans")
orders = FormattedTextControl(text="Orders")


class Mode(Enum):
    SCOPES = auto()
    SCANS = auto()
    ORDERS = auto()
    OFF = auto()


class Client:
    def __init__(self):
        # noinspection PyTypeChecker
        mode = cycle(Mode)
        self.state: Mode

        @kb.add("tab")
        def nextmode(*_):
            self.state = next(mode)

        nextmode()

        root = VSplit(
            (
                # Command History on most of the left panel, Prompt at the bottom.
                HSplit(
                    (cmd_panel, Window(BufferControl(buffer=cmd_line), wrap_lines=True))
                ),
                VerticalLine(),
                # Two visualization scopes on the right.
                ConditionalContainer(
                    scopes, Condition(lambda: self.state is Mode.SCOPES)
                ),
                ConditionalContainer(
                    Window(scans, ignore_content_width=True),
                    Condition(lambda: self.state is Mode.SCANS),
                ),
                ConditionalContainer(
                    Window(orders, ignore_content_width=True),
                    Condition(lambda: self.state is Mode.ORDERS),
                ),
            )
        )

        self.app = Application(full_screen=True, key_bindings=kb, layout=Layout(root))
