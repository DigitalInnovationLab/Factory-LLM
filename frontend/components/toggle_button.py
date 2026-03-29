from nicegui import ui


class ToggleButton(ui.button):
    """
    A toggle button component.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._state = False
        self.on("click", self.toggle)

    def toggle(self) -> None:
        """
        Toggle the button state.
        """
        self._state = not self._state
        self.update()

    def update(self) -> None:
        """
        Update the button based on the state.
        """
        self._state = getattr(self, "_state", False)
        if not self._state:
            self.props("outline")
        else:
            self.props("outline=false")
        super().update()

    @property
    def state(self) -> bool:
        """
        The state of the button.
        """
        return self._state
