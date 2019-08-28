from blessings import Terminal
from prompt_toolkit import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.document import Document
from prompt_toolkit.layout.containers import HSplit, VSplit, Window
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.key_binding import KeyBindings


T = Terminal()


def enter(buffer: Buffer):
    doc: Document = buffer.document
    with T.location(0, 3):
        print(*(l + " " * 10 for l in doc.lines), end="", sep="\n")
    buffer.reset()


buffer1 = Buffer(accept_handler=enter, multiline=False)  # Text Input.
root = VSplit(
    [
        # Command Prompt on the left.
        Window(content=BufferControl(buffer=buffer1)),
        # Vertical line divider.
        Window(char="|", width=1),
        # Two visualization scopes on the right.
        HSplit(
            [
                # Top-down on the upper panel.
                Window(content=FormattedTextControl(text="Top-Down")),
                # Horizontal line divider.
                Window(char="=", height=1),
                # Visualization from behind on the lower panel.
                Window(content=FormattedTextControl(text="Horizon")),
            ]
        ),
    ]
)

kb = KeyBindings()


@kb.add("c-d", "c-q", "c-x", "c-z")
def close(event):
    """Ctrl-Q: Exit program."""
    event.app.exit()


Client = Application(full_screen=True, key_bindings=kb, layout=Layout(root))
