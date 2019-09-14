from itertools import repeat
from typing import Any, Callable, Dict, Tuple, Type, Union

from blessings import Terminal
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style
from prompt_toolkit.utils import Event

from config import cfg


N = FormattedText([("class:etc", "\n")])
NNN = repeat(("class:etc", "\n"))
STYLE = Style(list(cfg.get("interface/style").items()))

T = Terminal()


noact = lambda x: x
unstyle = {
    "class:etc": noact,
    "class:hostname": T.cyan,
    "class:path": T.bold_bright_blue,
}


EchoType: Type[Callable] = Callable[[Union[str, Tuple[str, ...]]], None]


def fmt(text: Union[FormattedText, str], style: str = "class:etc") -> FormattedText:
    if isinstance(text, FormattedText):
        return text
    else:
        return FormattedText([(style, str(text))])


attrs = ("bold", "italic", "reverse")


def resolve(style: str):
    fg = ""
    fg_attr = set()
    bg = ""
    bg_attr = set()
    terms = style.split()

    for term in terms:
        if term in attrs:
            if fg:
                bg_attr.add(term)
            else:
                fg_attr.add(term)

        elif ":" in term:
            g, color = term.split(":")

            if color.startswith("ansi"):
                color = color[4:]

            if g == "fg":
                fg = color
            elif g == "bg":
                bg = color

    try:
        return getattr(
            T,
            "_".join(
                filter(None, (*fg_attr, fg, *(("on", *bg_attr, bg) if bg else ())))
            ),
        )
    except:
        return noact


def unformat(text: FormattedText) -> str:
    return "".join((unstyle.get(style) or resolve(style))(line) for style, line in text)


def keys(
    given: Dict[str, Callable[[Event], Any]] = None, *, bind_defaults: bool = True
) -> KeyBindings:
    kb = KeyBindings()

    if bind_defaults:

        # @kb.add("c-c")
        # def interrupt(event):
        #     """Ctrl-Q: Exit program."""
        #     event.app.exit(exception=KeyboardInterrupt)

        @kb.add("c-d")
        def eof(event):
            """Ctrl-Q: Exit program."""
            event.app.exit(exception=EOFError)

        @kb.add("c-q")
        def close(event):
            """Ctrl-Q: Exit program."""
            event.app.exit()

    if given:
        for k, v in given.items():
            kb.add(k)(v)

    return kb
