from abc import ABC, abstractmethod
from secrets import randbelow

from attr import attrs


@attrs
class Staff(object):
    crew: int  # Number of People assigned to work a System.
    equip: int  # Number of Workstations in a System.

    crew_hurt: int = 0  # Number of People temporarily unable to work.
    crew_dead: int = 0  # Number of People permanently unable to work.
    equip_damaged: int = 0  # Number of Workstations temporarily inoperable.
    equip_destroy: int = 0  # Number of Workstations permanently inoperable.

    work: int = 0
    work_goal: int = 2

    @property
    def crew_fine(self) -> int:
        return max(self.crew - (self.crew_hurt + self.crew_dead), 0)

    @property
    def crew_alive(self) -> int:
        return max((self.crew - self.crew_dead), 0)

    @property
    def equip_fine(self) -> int:
        return max(self.equip - (self.equip_damaged + self.equip_destroy), 0)

    @property
    def equip_intact(self) -> int:
        return max((self.equip - self.equip_destroy), 0)

    @property
    def work_capable(self) -> int:
        return min(self.crew_fine, self.equip_fine)

    def injure(self, number: int):
        for i in range(number):
            if self.crew_alive > 0:
                if randbelow(self.crew_alive) < self.crew_hurt:
                    self.crew_hurt -= 1
                    self.crew_dead += 1
                else:
                    self.crew_hurt += 1

    def damage(self, number: int):
        for i in range(number):
            if self.equip_intact > 0:
                if randbelow(self.equip_intact) < self.equip_damaged:
                    self.equip_damaged -= 1
                    self.equip_destroy += 1
                else:
                    self.equip_damaged += 1

    def work_points(self) -> int:
        points, self.work = divmod(self.work + self.work_capable, self.work_goal)
        return points


class Section(ABC):
    def __init__(self, staff: Staff):
        self.staff: Staff = staff

    @abstractmethod
    def work_auto(self):
        ...

    @abstractmethod
    def work_command(self, command: str):
        ...
