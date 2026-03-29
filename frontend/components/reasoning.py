from typing import List, Union

from nicegui import ui
from nicegui.page_layout import RightDrawer
from pydantic import BaseModel

from frontend.components.utils import local_css


class ReasoningSubstep(BaseModel):
    """Model for a substep in the reasoning process."""

    name: str
    content: Union[str, List[str]]


class ReasoningStep(BaseModel):
    """Model for a step in the reasoning process."""

    name: str
    substeps: List[ReasoningSubstep]


class Reasoning:
    """
    A component to render the reasoning process.
    """

    def __init__(self, steps: List[ReasoningStep], drawer: RightDrawer = None):
        local_css("frontend/components/css/reasoning.css")
        self._steps = steps
        self._drawer = drawer

    def render(self):
        """
        Render the reasoning process.
        """
        self._drawer.clear()
        with self._drawer:
            ui.label("Reasoning Process").classes("text-2xl font-bold relative mt-2")
            ui.button(on_click=self._drawer.hide, icon="close").props(
                "flat round"
            ).classes("absolute top-1 right-1")

            with ui.scroll_area().classes("h-full w-full p-0 reasoning-frame"):
                for step in self._steps:
                    with ui.expansion(step.name).classes("w-full rounded-md").style(
                        "border: 1px solid var(--color-primary); background-color: #111529;"
                    ):
                        for substep in step.substeps:
                            ui.label(substep.name).classes("text-lg font-bold")
                            if isinstance(substep.content, list):
                                # Render a list of content
                                for chunk in substep.content:
                                    with ui.card().classes("w-full px-3 py-2").style(
                                        "background-color: var(--color-background-secondary); \
                                            border-radius: 5px;"
                                    ):
                                        ui.label(chunk)
                            else:
                                ui.label(substep.content)

        self._drawer.show()
