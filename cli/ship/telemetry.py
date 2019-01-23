"""
Module for analysis and presentation of telemetric scans to the user.
"""

from astropy import units

import config
from engine import geometry


def get_name(obj: dict) -> str:
    c = obj.__class__.__name__
    n = obj.get("name", None)
    if n:
        return "{} ({})".format(n, c)
    else:
        return c


def get_data(data, *, indent=1) -> list:
    pad = " " * (config.Scan.indent * indent)
    o = []

    if isinstance(data, geometry.Coordinates):
        cart = data.position
        o.append("Cartesian: {}".format(cart))

        dist, *pos = data.position_pol
        o.append("Distance: {}".format(dist * units.meter))
        o.append("Bearing: {}".format(pos))

        spd, *direc = data.velocity_pol
        o.append("Speed: {}".format(spd * (units.meter/units.second)))
        o.append("Course: {}".format(direc))

    return [pad + line for line in o]


class Scan:
    """
    Convenient framework for the storage and display of a Scan
    """

    def __init__(self, data, host=None):
        self.data = data
        self.host = host

    def report_named(self):
        c = 0
        for obj in self.data:
            if "name" in obj:
                c += 1
                self.report(obj)
        if not c:
            print(config.Scan.result_none.format("Named Objects"))

    def report_minor(self):
        c = 0
        for obj in self.data:
            if "name" not in obj:
                c += 1
                self.report(obj)
        if not c:
            print(config.Scan.result_none.format("Minor Objects"))

    def report_all(self):
        self.report_named()
        self.report_minor()

    def report_self(self):
        if self.host:
            self.report(self.host)
        else:
            print(config.Scan.result_none.format("diagnostics"))

    def report(self, obj: dict):
        o = []
        for attr in config.Scan.display_attr:
            v = obj.get(attr)
            if v:
                o.append("{}: <{}>".format(attr, v))
                o += get_data(v)
        print("\n".join(o))
