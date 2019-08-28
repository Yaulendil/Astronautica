from blessings import Terminal
from prompt_toolkit import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.layout.containers import HSplit, VSplit, Window
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.key_binding import KeyBindings


T = Terminal()

scrollback = FormattedTextControl(text="Command History")
cmd_panel = Window(
    content=scrollback,
    dont_extend_height=True,
    ignore_content_width=True,
    wrap_lines=True,
)


def echo(text: str):
    scrollback.text += f"\n{text}"


def enter(buffer: Buffer):
    command: str = buffer.text
    buffer.append_to_history()
    buffer.reset()
    echo(command)


cmd_line = Buffer(accept_handler=enter, multiline=False)


scope_topdown = FormattedTextControl(text="TopDown")
scope_horizon = FormattedTextControl(text="Horizon")
scopes = HSplit(
    (
        # Top-down visualization on the upper panel.
        Window(
            content=scope_topdown, ignore_content_height=True, ignore_content_width=True
        ),
        # Horizontal line divider.
        Window(char="=", height=1),
        # Visualization from behind on the lower panel.
        Window(
            content=scope_horizon, ignore_content_height=True, ignore_content_width=True
        ),
    )
)


panel_right = scopes #Window(content=scopes)
root = VSplit(
    [
        # Command History on most of the left panel, Command Prompt at the bottom.
        HSplit((cmd_panel, Window(content=BufferControl(buffer=cmd_line), height=1))),
        # Vertical line divider.
        Window(char="|", width=1),
        # Two visualization scopes on the right.
        panel_right,
    ]
)

kb = KeyBindings()


@kb.add("c-q")
def close(event):
    """Ctrl-Q: Exit program."""
    event.app.exit()


Client = Application(full_screen=True, key_bindings=kb, layout=Layout(root))
