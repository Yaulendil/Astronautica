from asyncio import AbstractEventLoop, Task
from enum import Enum
from itertools import cycle
from pathlib import Path
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
from prompt_toolkit.layout.processors import BeforeInput, Processor
from prompt_toolkit.widgets import HorizontalLine, VerticalLine
from ptterm import Terminal

from .commands import CommandRoot
from .etc import keys, STYLE, T, unstyle
from .execution import execute_function
from config import cfg


class Mode(Enum):
    OFF = "OFF"  # auto()
    SCOPES = "SCOPES"  # auto()
    SCANS = "SCANS"  # auto()
    ORDERS = "ORDERS"  # auto()


class Prompt(object):
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

    # @property
    # def char(self):
    #     return "# " if self.username.lower() == "root" else "$ "

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
    def __init__(self, loop: AbstractEventLoop, command_handler: CommandRoot = None):
        self.LOOP: AbstractEventLoop = loop
        self.TASKS: List[Task] = []

        self.first = True
        self.read_only = False
        self.kb = keys(self)
        # noinspection PyTypeChecker
        mode = cycle(Mode)
        self.state: Mode = next(mode)

        @self.kb.add("s-tab")
        def nextmode(*_) -> None:
            self.state = next(mode)

        @self.kb.add("pageup")
        def hist_first(*_) -> None:
            self.cmd.go_to_history(0)

        @self.kb.add("pagedown")
        def hist_last(*_) -> None:
            self.cmd.go_to_history(len(self.cmd.history.get_strings()))

        @self.kb.add("c-c")
        def interrupt(*_):
            """Ctrl-C: Interrupt running Job."""
            self.echo("^C")
            if self.job and not self.job.done():
                self.job.cancel()
            self.job = None

        # Create a Prompt Object with initial values.
        self.prompt = Prompt(
            cfg["interface/initial/user", "nobody"],
            cfg["interface/initial/host", "local"],
            cfg["interface/initial/wdir", "~"],
        )

        # Build the UI.
        self.bar = FormattedTextControl(
            lambda: "{left:{pad}^{half}}│{right:{pad}^{half}}".format(
                left=self.console_header(),
                right=f"Panel Display: {self.state.value} [Shift-Tab]",
                half=(int(T.width / 2)),
                pad="",
            )
        )
        self.cmd = Buffer(
            accept_handler=self.enter,
            completer=command_handler,
            multiline=False,
            read_only=Condition(self.busy),
            on_text_changed=command_handler.change,
        )
        self.term = Terminal(sim_prompt=True)
        self.console = self.term.terminal_control.process.terminal
        self.console_header = lambda: ""

        self.procs: List[Processor] = [self.prompt.processor]

        self.scope_topdown = FormattedTextControl(text="TopDown")
        self.scope_horizon = FormattedTextControl(text="Horizon")
        self.scans = FormattedTextControl(text="Scans")
        self.orders = FormattedTextControl(text="Orders")

        # Register the Command Handler.
        self.handler = command_handler
        self._app: Optional[Application] = None

        self.job: Optional[Task] = None

        # self.echo("Ready.", start="")

    def busy(self) -> bool:
        return self.job is not None and not self.job.done()

    def set_job(self, job: Task):
        self.job = job
        self.redraw()

    def cmd_hide(self):
        """Make the Command Prompt invisible, and then update the display."""
        self.read_only = True
        self.redraw()

    def cmd_show(self, *_):
        """Make the Command Prompt visible, and then update the display.

        This must take an Argument, because it may be used as a Callback from a
            Task. However, we do not need to do anything with it, because no
            matter what, the Prompt MUST be reenabled after a Command completes.
        """
        self.read_only = False
        self.redraw()

    def echo(self, *text, sep: str = "\r\n", start: str = "\r\n"):
        """Print Text to the Console Output, and then update the display."""
        self.console.write_text(
            ("" if self.first else start)
            + sep.join(
                fragment_list_to_text(line)
                if isinstance(line, FormattedText)
                else str(line)
                for line in text
            )
        )
        self.first = False
        self.redraw()

    def enter(self, buffer: Buffer) -> None:
        """The User has Accepted the LineBuffer. Read the Buffer, reset the
            line, and then forward the text to the Execute Function.
        """
        self.handler.completion = ""
        command: str = buffer.text
        buffer.reset(append_to_history=True)
        self.execute(command)

    def execute(self, line: str, hide: bool = True) -> None:
        """A Command is being run. Print it alongside the Prompt, and then pass
            it to the Handler.
        """
        self.echo(self.prompt.raw(line))

        if line:
            if self.handler:
                if hide:
                    self.read_only = True
                execute_function(
                    line.strip(), self.echo, self.handler, self.LOOP, self.TASKS, self.set_job
                )
            else:
                self.echo("No handler.")

    def redraw(self) -> None:
        """Signal the Console to run its Callbacks, and then rerun the Renderer
            of the Application, if we have one.
        """
        self.console.ready()
        if self._app:
            self._app.renderer.render(self._app, self._app.layout)

    def __enter__(self) -> Application:
        """Build a Layout and instantiate an Application around it."""
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
                                    ConditionalContainer(
                                        Window(
                                            BufferControl(self.cmd, self.procs),
                                            dont_extend_height=True,
                                            # height=1,
                                            wrap_lines=True,
                                        ),
                                        Condition(lambda: not self.busy()),
                                    ),
                                    ConditionalContainer(
                                        Window(FormattedTextControl("..."), height=1),
                                        Condition(self.busy),
                                    ),
                                    ConditionalContainer(
                                        Window(
                                            FormattedTextControl(
                                                lambda: self.handler.completion
                                            ),
                                            height=1,
                                            style="ansigray bold reverse",
                                        ),
                                        Condition(lambda: self.handler.completion),
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
