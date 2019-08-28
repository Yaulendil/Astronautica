from enum import auto, Enum
from itertools import cycle
from typing import Sequence, Tuple

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


prompt = Prompt(
    [
        ("class:hostname", "asdf@qwert"),
        ("class:etc", ":"),
        ("class:path", "~"),
        ("class:etc", "$ "),
    ]
)


scrollback = FormattedTextControl(text=[])
cmd_panel = Window(
    scrollback, dont_extend_height=True, ignore_content_width=True, wrap_lines=True
)


def echo(*text: str, style: str = "class:etc"):
    for t in text:
        scrollback.text.append((style, f"\n{t}"))


def echo_with_prompt(text: FormattedText):
    echo("")
    scrollback.text += text


def enter(buffer: Buffer):
    command: str = buffer.text
    # buffer.reset(append_to_history=True)
    echo_with_prompt(prompt(command))
    return False


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

        self.bar = FormattedTextControl("asdf qwert")
        root = VSplit(
            (
                # Command History on most of the left panel, Prompt at the bottom.
                HSplit(
                    (
                        cmd_panel,
                        Window(
                            BufferControl(cmd_line, [prompt.processor]), wrap_lines=True
                        ),
                    )
                ),
                ConditionalContainer(
                    VerticalLine(), Condition(lambda: self.state is not Mode.OFF)
                ),
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

        self.app = Application(
            full_screen=True,
            key_bindings=kb,
            layout=Layout(
                HSplit(
                    (Window(self.bar, height=1, style="ansigray bold reverse"), root)
                )
            ),
            style=STYLE,
        )
