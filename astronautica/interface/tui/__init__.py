from asyncio import AbstractEventLoop, Task
from enum import Enum
from itertools import cycle
from pathlib import Path
from typing import List, Optional, Union

from prompt_toolkit import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.filters import Condition
from prompt_toolkit.formatted_text import FormattedText, fragment_list_to_text
from prompt_toolkit.keys import Keys
from prompt_toolkit.layout import Float, FloatContainer
from prompt_toolkit.layout.containers import (
    ConditionalContainer,
    HSplit,
    VSplit,
    Window,
)
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.layout.processors import (
    BeforeInput,
    HighlightMatchingBracketProcessor,
    PasswordProcessor,
    Processor,
)
from prompt_toolkit.widgets import Frame, HorizontalLine, VerticalLine
from ptterm import Terminal

from ..commands import CommandRoot
from ..etc import crlf, keys, STYLE, T, unstyle
from ..execution import execute_function
from .orders import OrdersDisplay
from .scans import TelemetryDisplay
from config import cfg


class Alert(Enum):
    NORM = "#000 bg:ansigray bold"
    WARN = "#000 bg:ansiyellow bold"
    CRIT = "bg:ansired bold"


class Mode(Enum):
    OFF = "OFF"
    SCANS = "SCANS"
    SCOPES = "SCOPES"
    ORDERS = "ORDERS"


class Prompt(object):
    __slots__ = (
        "char",
        "hostname",
        "namestyle",
        "path",
        "prefix",
        "processor",
        "username",
    )

    def __init__(
        self,
        username: str,
        host: str,
        path: Union[Path, str] = "~",
        *,
        namestyle: str = None,
        prefix: str = "",
    ):
        self.username: str = username
        self.hostname: str = host
        self.path: Path = Path(path)

        self.namestyle: str = namestyle
        self.prefix: str = prefix
        self.processor = BeforeInput(self)

        self.char: str = "$ "

    @property
    def prompt(self) -> FormattedText:
        """Generate the Command Prompt as a FormattedText. This format is mostly
            only useful for things in PTK.
        """
        return FormattedText(
            [
                ("class:etc", self.prefix),
                (
                    "class:hostname" if self.namestyle is None else self.namestyle,
                    f"{self.username}@{self.hostname}",
                ),
                ("class:etc", ":"),
                ("class:path", str(self.path)),
                ("class:etc", self.char),
            ]
        )

    def raw(self, append: str = "") -> str:
        """Generate the Command Prompt as a String with coloring sequences
            suited to a regular Terminal. This format works for the console, but
            is unlikely to be useful with PTK.
        """
        return "{}{}:{}{}{}".format(
            self.prefix,
            unstyle["class:hostname"](f"{self.username}@{self.hostname}"),
            unstyle["class:path"](str(self.path)),
            self.char,
            append,
        )

    def __call__(
        self, text: Union[FormattedText, str] = None, style="class:etc"
    ) -> FormattedText:
        """Return the Prompt alongside the given text input, if any. This allows
            use of the Object as an Input Preprocessor to put the Prompt
            directly into the PTK Buffer Object.
        """
        if text is None:
            return self.prompt
        elif isinstance(text, FormattedText):
            return self.prompt + text
        else:
            return self.prompt + [(style, str(text))]


class Interface(object):
    __slots__ = {
        "LOOP",
        "TASKS",
        "first",
        "kb",
        "state",
        "prompt",
        "header_bar",
        "command_buffer",
        "terminal",
        "console_backend",
        "console_header",
        "floating_elems",
        "procs",
        "scope_topdown",
        "scope_horizon",
        "scans",
        "orders",
        "handler",
        "current_job",
        "_app",
        "_style",
    }

    def __init__(self, loop: AbstractEventLoop, command_handler: CommandRoot = None):
        self.LOOP: AbstractEventLoop = loop
        self.TASKS: List[Task] = []

        self.first = True
        self.kb = keys(self)
        # noinspection PyTypeChecker
        mode = cycle(Mode)
        self.state: Mode = next(mode)
        self._style: Alert = Alert.NORM

        @self.kb.add("s-tab")
        def nextmode(*_) -> None:
            self.state = next(mode)

        @self.kb.add("pageup")
        def hist_first(*_) -> None:
            self.command_buffer.go_to_history(0)

        @self.kb.add("pagedown")
        def hist_last(*_) -> None:
            self.command_buffer.go_to_history(
                len(self.command_buffer.history.get_strings())
            )

        @self.kb.add("c-c")
        def interrupt(*_):
            """Ctrl-C: Interrupt running Job."""
            self.print("^C")
            if self.current_job and not self.current_job.done():
                self.current_job.cancel()
            self.current_job = None

        # Create a Prompt Object with initial values.
        self.prompt = Prompt(
            cfg["interface/initial/user", "nobody"],
            cfg["interface/initial/host", "local"],
            cfg["interface/initial/wdir", "~"],
        )

        # Build the UI.
        self.header_bar = FormattedTextControl(
            lambda: FormattedText(
                [
                    (
                        "",
                        f"{self.console_header():^{int(T.width / 2)}}│<⇧TAB> / ",
                    ),
                    *(
                        ("reverse" if self.state is m else "", f" {m.value} ")
                        for m in Mode
                    ),
                ]
            )
        )
        # self.header_bar = FormattedTextControl(
        #     lambda: "{left:{pad}^{half}}│{right:{pad}^{half}}".format(
        #         left=self.console_header(),
        #         right=f"Panel Display: {self.state.value} [Shift-Tab]",
        #         half=int(T.width / 2),
        #         pad="",
        #     )
        # )
        self.command_buffer = Buffer(
            accept_handler=self.enter,
            complete_while_typing=True,
            completer=command_handler,
            multiline=False,
            on_text_changed=command_handler.change,
            read_only=Condition(self.busy),
        )

        self.terminal = Terminal(sim_prompt=True)
        self.console_backend = self.terminal.terminal_control.process.terminal
        self.console_header = lambda: ""

        self.floating_elems = []
        self.procs: List[Processor] = [
            self.prompt.processor,
            HighlightMatchingBracketProcessor(),
        ]

        self.scope_topdown = FormattedTextControl(text="TopDown")
        self.scope_horizon = FormattedTextControl(text="Horizon")
        self.scans = TelemetryDisplay()
        self.orders = OrdersDisplay()

        # Register the Command Handler.
        self.handler = command_handler
        self.current_job: Optional[Task] = None
        self._app: Optional[Application] = None

    def busy(self) -> bool:
        return not (self.current_job is None or self.current_job.done())

    def set_job(self, job: Task):
        self.current_job = job
        self.redraw()

    async def get_input(self, title: str = "", hide: bool = False) -> str:
        try:
            # Create a new Future.
            fut = self.LOOP.create_future()

            def finish(_buf: Buffer) -> bool:
                fut.set_result(_buf.text)
                return False

            # Create a Buffer, and assign its Handler to set the Result of the
            #   Future created above.
            buf = Buffer(accept_handler=finish, multiline=False)
            self.floating_elems[:] = [
                Float(
                    Frame(
                        Window(
                            BufferControl(
                                buf,
                                input_processors=[
                                    PasswordProcessor(),
                                    BeforeInput("   "),
                                ]
                                if hide
                                else [BeforeInput("   ")],
                            ),
                            get_horizontal_scroll=(lambda *_: 0),
                        ),
                        title=title,
                    ),
                    width=35,
                    height=3,
                )
            ]
            self._app.layout.focus(buf)
            # Open a popup Float, and wait for the Future to be fulfilled.
            self.redraw()
            return await fut
        finally:
            self._app.layout.focus(self.command_buffer)
            self.floating_elems.clear()

    def print(self, *text, sep: str = "\n", start: str = "\n") -> None:
        """Print Text to the Console Output, and then update the display."""
        self.console_backend.write_text(
            crlf(
                ("" if self.first else start)
                + sep.join(
                    fragment_list_to_text(line)
                    if isinstance(line, FormattedText)
                    else str(line)
                    for line in text
                    if line is not None
                )
            )
        )
        self.first = False
        self.redraw()

    def enter(self, buffer: Buffer) -> bool:
        """The User has Accepted the LineBuffer. Read the Buffer, reset the
            line, and then forward the text to the Execute Function.
        """
        self.handler.completion = ""
        command: str = buffer.text
        buffer.reset(append_to_history=not command.startswith(" "))
        self.execute(command)
        return False

    def execute(self, line: str) -> None:
        """A Command is being run. Print it alongside the Prompt, and then pass
            it to the Handler.
        """
        self.print(self.prompt.raw(line))

        if line:
            if self.handler:
                execute_function(
                    line.strip(),
                    self.print,
                    self.handler,
                    self.LOOP,
                    self.TASKS,
                    self.set_job,
                )
            else:
                self.print("No handler.")

    def redraw(self) -> None:
        """Signal the Console to run its Callbacks, and then rerun the Renderer
            of the Application, if we have one.
        """
        self.console_backend.ready()
        if self._app:
            self._app.renderer.render(self._app, self._app.layout)

    def shortcut(self, command: str, *keys_: Union[Keys, str]):
        """Easily add a Keyboard Shortcut to Execute a Command."""
        return self.kb.add(*keys_)(lambda *_: self.execute(command))

    def style_meth(self, new: Alert = None) -> str:
        if new is None:
            return str(self._style.value)
        else:
            self._style = new

    def __enter__(self) -> Application:
        """Build a Layout and instantiate an Application around it."""
        main = VSplit(
            (
                # Command History on most of the left panel, Prompt at the bottom.
                HSplit(
                    (
                        self.terminal,
                        ConditionalContainer(
                            Window(  # Command Prompt.
                                BufferControl(self.command_buffer, self.procs),
                                dont_extend_height=True,
                                wrap_lines=True,
                            ),
                            Condition(lambda: not self.busy()),
                        ),
                        ConditionalContainer(
                            Window(  # "Busy" Prompt, blocks Commands.
                                FormattedTextControl("..."),
                                height=1,
                                ignore_content_width=True,
                            ),
                            Condition(self.busy),
                        ),
                        ConditionalContainer(
                            Window(  # Completion Bar.
                                FormattedTextControl(lambda: self.handler.completion),
                                height=1,
                                ignore_content_width=True,
                                style=self.style_meth,
                            ),
                            Condition(lambda: bool(self.handler.completion)),
                        ),
                    )
                ),
                ConditionalContainer(  # Vertical Line.
                    HSplit(
                        (
                            VerticalLine(),
                            Window(
                                FormattedTextControl(
                                    lambda: "├" if self.state is Mode.SCOPES else "│"
                                ),
                                width=1,
                                height=1,
                            ),
                            VerticalLine(),
                        )
                    ),
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
        )
        root = Layout(
            HSplit(
                (
                    Window(self.header_bar, height=1, style=self.style_meth),
                    FloatContainer(main, self.floating_elems),
                )
            )
        )
        root.focus(self.command_buffer)
        self._app = Application(root, STYLE, full_screen=True, key_bindings=self.kb)
        return self._app

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self._app = None
