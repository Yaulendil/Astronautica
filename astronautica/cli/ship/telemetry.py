"""
Module for analysis and presentation of telemetric scans to the user.
"""

from math import degrees

from astropy import units as u
from numpy import round as npr

from astronautica.config import Scan as Cfg
from astronautica.engine import geometry


def get_name(obj: dict) -> str:
    c = obj.__class__.__name__
    n = obj.get("name", None)
    if n:
        return "{} ({})".format(n, c)
    else:
        return c


def get_data(data, *, indent=1) -> list:
    """
    Generate a Scan Report for the given data
    """

    pad = " " * (Cfg.indent * indent)
    o = []

    if isinstance(data, geometry.Coordinates):
        # Include Cartesian Position, simple position of this object in Vector3
        pos, vel = npr(data.position, Cfg.decimals), npr(data.velocity, Cfg.decimals)
        o.append("Pos+Vel: {}m + {}m/s\n".format(pos, vel))

        # Include Distance and Bearing, direction in which this object is seen
        dist, *pos = data.position_pol
        o.append("Distance: {}".format(npr(dist * u.meter, Cfg.decimals)))
        if dist > 0:
            o.append("Bearing: [θ={}°, φ={}°]\n".format(*npr(pos, Cfg.decimals)))

        # Include Speed and Course, direction this object is moving
        spd, *direc = data.velocity_pol
        o.append("Speed: {}".format(npr(spd * u.meter / u.second, Cfg.decimals)))
        if spd > 0:
            o.append("Course: [θ={}°, φ={}°]\n".format(*npr(direc, Cfg.decimals)))

        # Include Heading, direction this object is facing
        _, *heading = geometry.cart3_polar3(*geometry.facing(data.heading))
        o.append("Heading: [θ={}°, φ={}°]\n".format(*npr(heading, Cfg.decimals)))

        # Include Spin and Axis (of rotation), describing rotational velocity
        spin, axis = geometry.break_rotor(data.rotate)
        o.append("Spin: {}°/s".format(npr(degrees(spin), Cfg.decimals)))
        if spin != 0:
            o.append("-Axis: [θ={}°, φ={}°]".format(*npr(axis, Cfg.decimals)))

    return [pad + line for line in o if line]


class Scan:
    """
    Convenient framework for the storage and display of a Scan
    """

    def __init__(self, data: list, host=None):
        self.data = data
        self.host = host

    @property
    def full(self):
        return [self.host] + self.data

    def report_named(self):
        c = 0
        for obj in self.data:
            if obj.get("name"):
                c += 1
                self.report(obj)
        if not c:
            print(Cfg.result_none.format("Named Objects"))

    def report_minor(self):
        c = 0
        for obj in self.data:
            if not obj.get("name"):
                c += 1
                self.report(obj)
        if not c:
            print(Cfg.result_none.format("Minor Objects"))

    def report_self(self):
        if self.host:
            self.report(self.host)
        else:
            print(Cfg.result_none.format("diagnostics"))

    def report_all(self):
        self.report_named()
        self.report_minor()

    def report(self, obj: dict):
        o = []
        for attr in Cfg.display_attr:
            v = obj.get(attr)
            if v:
                o.append("{}: <{}>".format(attr, v.__class__.__name__))
                o += get_data(v)
        print("\n".join(o))
