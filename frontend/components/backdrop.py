from nicegui import ui


class Backdrop:
    """
    Backdrop component.
    """

    def __init__(self, progress_texts: list[str]) -> None:
        self.container = (
            ui.row()
            .classes("fixed inset-0 z-50")
            .style("background-color: rgba(0, 0, 0, 0.7);")
        )
        self.progress_index = 0
        self.progress_texts = progress_texts
        with self.container:
            with ui.column(align_items="center").classes("m-auto"):
                ui.spinner(size="5em")
                self.progress_label = ui.label(
                    self.progress_texts[self.progress_index]
                    if self.progress_texts
                    else ""
                ).classes("text-white text-center mt-4 text-lg")

        if self.progress_texts and len(self.progress_texts) > 0:
            ui.timer(5, self.update_progress_text)

    def update_progress_text(self) -> None:
        """
        Update the progress text.
        """
        if self.progress_texts:
            self.progress_label.set_text(self.progress_texts[self.progress_index])
            self.progress_index = (self.progress_index + 1) % len(self.progress_texts)

    def close(self) -> None:
        """
        Hide the backdrop.
        """
        self.container.delete()
