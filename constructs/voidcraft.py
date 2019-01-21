from constructs import interior
from constructs.synthetic import Ship


class Sloop(Ship):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.struct["medbay"] = interior.DepartmentMedical(self, 4)
        self.struct["maint"] = interior.DepartmentMaintenance(self, 6)


classes = [Sloop]
