"""Rotation Module: Dedicated to angles and orientations in three-dimensional
    Space.
"""

from quaternion import quaternion

from .base import Rotation


class Pointer(Rotation):
    def __init__(self, domain, index: int):
        self.domain = domain
        self.index: int = index

    @property
    def heading(self) -> quaternion:
        return self.domain.quat_heading[self.index]

    @heading.setter
    def heading(self, value: quaternion) -> None:
        self.domain.quat_heading[self.index] = value

    @property
    def rotate(self) -> quaternion:
        return self.domain.quat_rotate[self.index]

    @rotate.setter
    def rotate(self, value: quaternion) -> None:
        self.domain.quat_rotate[self.index] = value


class Virtual(Rotation):
    def __init__(self, aim: quaternion, rot: quaternion):
        # Orientation.
        self._heading = aim
        # Spin per second.
        self._rotate = rot

    @property
    def heading(self) -> quaternion:
        return self._heading

    @heading.setter
    def heading(self, value: quaternion) -> None:
        self._heading = value

    @property
    def rotate(self) -> quaternion:
        return self._rotate

    @rotate.setter
    def rotate(self, value: quaternion) -> None:
        self._rotate = value
