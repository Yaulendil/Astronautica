from typing import Any, Callable, Dict, Union

from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style
from prompt_toolkit.utils import Event

from config import cfg


N = FormattedText([("class:etc", "\n")])
STYLE = Style(list(cfg.get("interface/style").items()))


def fmt(text: Union[FormattedText, str], style: str = "class:etc") -> FormattedText:
    if isinstance(text, FormattedText):
        return text
    else:
        return FormattedText([(style, str(text))])


def keys(
    given: Dict[str, Callable[[Event], Any]] = None, *, bind_defaults: bool = True
) -> KeyBindings:
    kb = KeyBindings()

    if bind_defaults:

        @kb.add("c-q")
        def close(event):
            """Ctrl-Q: Exit program."""
            event.app.exit()

    if given:
        for k, v in given.items():
            kb.add(k)(v)

    return kb
