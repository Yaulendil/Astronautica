from prompt_toolkit.layout import FormattedTextControl


def display(name: str, obj: dict):
    yield f"{name}: {obj.get('type')}"

    data = obj.get("data")
    if data:
        yield from (f"  {n}: {v}" for n, v in data.items())

    subs = obj.get("subs")
    if subs:
        for name_, sub in subs.items():
            yield from ("    " + x for x in display(name_, sub))


class TelemetryDisplay(FormattedTextControl):
    header = "TELEMETRY"

    def __init__(self, *a, **kw):
        self._telemetry = []
        self._output: str = self.header
        super().__init__(self.output, *a, **kw)

    @property
    def telemetry(self):
        return self._telemetry

    @telemetry.setter
    def telemetry(self, value):
        self._telemetry = value
        self._output = "\n".join(self.update())

    def output(self) -> str:
        return self._output

    def update(self) -> str:
        yield self.header
        for loc in self.telemetry:
            for obj in loc:
                yield from display("Contact", obj)
