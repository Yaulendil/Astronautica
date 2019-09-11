"""Module for generating designations for locations."""

from secrets import choice, randbelow
from typing import Dict


# # No I, M, O, or P.
# letters = "abcdefghjklnqrstuvwxyz"

probabilities: Dict[str, int] = {"ARSW": 5, "C": 10, "X": 40}
letters = "".join(l * n for l, n in probabilities.items())

firsts = "P" * 90 + "M" * 10


def sgc(first: str = None) -> str:
    first = (first or choice(firsts)).upper()
    return "{}{}{}-{:0>3}".format(
        first,
        randbelow(8) + 2,
        choice(letters.upper().replace(first, "")),
        randbelow(1000),
    )
