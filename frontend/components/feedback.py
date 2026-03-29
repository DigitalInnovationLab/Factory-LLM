from nicegui import ui

from backend.src.services.feedback import create_feedback


class Feedback:
    """
    A component to render a feedback form.
    """

    rating = 0
    feedback = ""
    message_id = 0
    user_id = 0

    def __init__(self, message_id: int, user_id: int):
        self.message_id = message_id
        self.user_id = user_id

        with ui.dialog() as dialog, ui.card().props("flat").style(
            "background-color: var(--color-background); width: 25rem"
        ):
            self.dialog = dialog
            with ui.card_section().classes("p-0 row items-center w-full"):
                ui.label("Feedback").classes("text-2xl font-bold")
                ui.space()
                ui.button(on_click=dialog.close).props("icon='close' flat round dense")

            with ui.card_section().classes("p-0 w-full"), ui.row().classes("gap-2"):
                ui.label("Please provide details: (optional)")
                ui.textarea(
                    placeholder="Your response goes here ...",
                    validation={
                        "Feedback must be less than 500 characters": lambda x: len(x)
                        < 500
                    },
                    on_change=lambda event: setattr(self, "feedback", event.value),
                ).props("outlined").classes("w-full").style(
                    "background-color: var(--color-background-secondary)"
                )

                self.star_rating()

            with ui.card_actions().props("align='right'").classes("w-full px-0"):
                ui.button("Cancel", on_click=dialog.close).props("outline").style(
                    "padding: 0 1rem"
                )
                ui.button("Submit", on_click=self.handle_submit).style(
                    "padding: 0 1rem"
                )

    @ui.refreshable
    def star_rating(self):
        """
        Render the star rating.
        """
        with ui.card_section().classes("p-0"), ui.row().classes("items-center gap-0"):
            for rating in range(1, 6):
                with ui.button(
                    on_click=lambda rating=rating: (
                        setattr(self, "rating", rating),
                        self.star_rating.refresh(),
                    )
                ).style("background-color: transparent").props("flat").classes(
                    "text-xl p-2"
                ):
                    ui.icon("star").props(
                        f'color={"yellow" if rating <= self.rating else "gray"}'
                    )

    def render(self):
        """
        Render the feedback form.
        """
        self.dialog.open()

    async def handle_submit(self):
        """
        Submit the feedback form.
        """
        await create_feedback(self.message_id, self.user_id, self.feedback, self.rating)
        self.dialog.close()
