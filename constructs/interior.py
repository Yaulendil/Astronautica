from random import randint


class Department:
    """
    A section of constructs housing equipment and personnel, serving a particular purpose.
    A Department has a number of Crew and a number of Machines.
        Crew represents people serving as Department staff who utilize Machines.
            A healthy Crewman can be injured, disabling them.
            An injured Crewman can be killed if damaged again.
            An assigned Medical Team can heal an injured Crewman, but not a dead one.
        Machines represent workstations where operations are carried out by Crew.
            An operational Machine can be damaged, disabling it.
            A damaged machine can be destroyed if damaged again.
            An assigned Engineering Team can repair a damaged machine, but not a destroyed one.
        Corpses of Crew members and debris from destroyed Machines can clutter a Department, resulting in slower operation.
        An assigned Medical Team will clear away corpses, while there is space in the Morgue, and an assigned Engineering Team will clear away debris, while there is space in the Hold.
    """

    difficulty = 2
    title = "Genericity Dept"

    def __init__(self, ship, size, crew=None, equip=None):
        self.ship = ship
        # Number of crewmembers/machines that can operate here
        self.size = size
        # Number of crewmembers assigned here
        self.crew = crew if crew is not None else size
        # Number of machines assigned here
        self.equip = equip if equip is not None else size

        self.crew_hurt = 0  # Injured crew needing medical attention
        self.crew_dead = 0  # Dead crew
        self.equip_dmg = 0  # Damaged machines needing maintenance
        self.equip_brk = 0  # Destroyed machines

        self.target = None

    @property
    def crew_healthy(self):
        crew = self.crew
        crew -= self.crew_dead
        crew -= self.crew_hurt
        return max([crew, 0])

    @property
    def crew_alive(self):
        crew = self.crew
        crew -= self.crew_dead
        return max([crew, 0])

    @property
    def equip_running(self):
        equip = self.equip
        equip -= self.equip_brk
        equip -= self.equip_dmg
        return max([equip, 0])

    @property
    def equip_avail(self):
        equip = self.equip
        equip -= self.equip_brk
        return max([equip, 0])

    def damage_crew(self, num):
        """Damage a number of personnel"""

        # First, make sure the number of people to damage is no more than the number alive
        num = min([num, self.crew_alive])
        # Then, pick a number of injured to kill no more than either:
        #   The number of people to damage
        #   The number of people who ARE hurt
        killed = randint(0, min([num, self.crew_hurt]))
        # The number of people injured is the remaining number
        injured = num - killed
        # Wait...Are there that many healthy people left?
        remaining_healthy = self.crew_healthy - injured
        if remaining_healthy < 0:
            # No? Then kill some more injured people.
            injured -= remaining_healthy
        # Time to ruin some lives.
        self.crew_hurt += injured
        self.crew_hurt -= killed
        self.crew_dead += killed

    def damage_equip(self, num):
        """Damage a number of machines"""

        # All the same logic as the last method
        num = min([num, self.equip_avail])
        destroyed = randint(0, min([num, self.crew_hurt]))
        damaged = num - destroyed
        remaining_running = self.equip_running - damaged
        if remaining_running < 0:
            damaged -= remaining_running
        # Time to put the sad in sysadmin.
        self.equip_dmg += damaged
        self.equip_dmg -= destroyed
        self.equip_brk += destroyed

    def work(self):
        cap = int(min(self.crew_healthy, self.equip_running)/self.difficulty)
        for i in range(cap):
            if randint(0, self.crew_dead) == 0:
                self.work_once()

    def work_once(self):
        pass


class DepartmentMedical(Department):
    title = "Medical Team"

    def work_once(self):
        if self.target.crew_hurt > 0:
            self.target.crew_hurt -= 1
        elif self.target.crew_dead > 0:
            self.target.crew_dead -= 1
            self.target.crew -= 1


class DepartmentMaintenance(Department):
    difficulty = 3
    title = "Maintenance Team"

    def work_once(self):
        if self.target.equip_dmg > 0:
            self.target.equip_dmg -= 1
        elif self.target.equip_brk > 0:
            self.target.equip_brk -= 1
            self.target.equip -= 1
