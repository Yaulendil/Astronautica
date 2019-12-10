from prompt_toolkit.layout import FormattedTextControl


class OrdersDisplay(FormattedTextControl):
    def __init__(self, *a, **kw):
        self._output: str = ""
        self._orders = []
        super().__init__(self.output, *a, **kw)

    @property
    def orders(self):
        return self._orders

    @orders.setter
    def orders(self, value):
        self._orders = value
        self._output = self.update()

    def output(self) -> str:
        return self._output

    def update(self) -> str:
        return ""
