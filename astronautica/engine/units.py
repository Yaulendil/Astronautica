from typing import NamedTuple

from astropy import units as u

__all__ = [
    "Units",
    "UNITS_GALACTIC",
    "UNITS_GIANT",
    "UNITS_LOCAL",
    "UNITS_PLANET",
    "UNITS_STAR",
]


class Units(NamedTuple):
    distance: u.Unit = u.meter
    mass: u.Unit = u.kg


UNITS_LOCAL = Units()
UNITS_PLANET = Units(u.km, u.M_earth)
UNITS_GIANT = Units(u.km, u.M_jup)
UNITS_STAR = Units(u.au, u.M_sun)
UNITS_GALACTIC = Units(u.lyr, u.M_sun)
