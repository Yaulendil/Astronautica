class Department:
    def __init__(self, size, maximum=None):
        if maximum is None:
            maximum = size
        self.crew = size
        self.crew_cap = maximum


class Ship:
    pass
