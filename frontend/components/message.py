import json
from abc import ABC, abstractmethod
import re

from nicegui import ui
from nicegui.page_layout import RightDrawer

from backend.src.services.chat import get_reasoning_steps_by_message
from frontend.components.auth_middleware import get_user_id
from frontend.components.reasoning import Reasoning, ReasoningStep

from .feedback import Feedback


class ChatMessage(ABC):
    """
    An abstract class for a chat message.
    """

    def __init__(self, text="", loading=False, container_style="", message_id=None):
        self._text = text
        self._loading = loading
        self._container_style = container_style
        self.message_id = message_id

    async def setup(self):
        """
        Async logic to setup the chat message.

        Ideally a separate factory class should be used to create and setup the message
        but let keep it simple for now.
        """

    @ui.refreshable
    def render(self):
        """
        Render the chat message.
        """
        with ui.row().classes("w-full no-wrap rounded-lg p-4 items-start").style(
            self._container_style
        ):
            self.render_avatar()
            if self._loading:
                ui.spinner(type="dots").classes("mt-4")
            else:
                print(self._text)

                ui.markdown(self._text).classes("text-lg")

    @abstractmethod
    def render_avatar(self):
        """
        Render the avatar component for the chat message.
        """

    @property
    def text(self):
        """
        The text content of the chat message.
        """
        return self._text

    @text.setter
    def text(self, value):
        self._text = value
        self.render.refresh()

    @property
    def loading(self):
        """
        The loading status of the chat message.
        """
        return self._loading

    @loading.setter
    def loading(self, value):
        self._loading = value
        self.render.refresh()

    async def set_message_id(self, message_id):
        """
        Update the message id of the chat message
        """
        self.message_id = message_id

    async def set_context_images(self, image_paths = []):
        """
        Set the image paths for the chat message.
        """
        for image_path in image_paths:
            self._text += f"""\n ![image]({image_path[1:]})"""
        self.render.refresh()


class UserMessage(ChatMessage):
    """
    A component to render a user message in the chat.
    """

    def __init__(self, text="", loading=False, message_id=None):
        super().__init__(text, loading, "background-color: #26293D;", message_id)

    def render_avatar(self):
        ui.avatar(
            icon="img:/images/noto_man.png",
            color="#C83C3C",
            rounded=True,
            size="2.75rem",
        )


class AssistantMessage(ChatMessage):
    """
    A component to render an assistant message in the chat.
    """

    def __init__(
        self, text="", loading=False, drawer: RightDrawer = None, message_id=None
    ):
        super().__init__(text, loading, message_id=message_id)
        self._drawer = drawer
        self._reasoning_steps = []

    async def setup(self):
        await self.get_reasoning_steps()

    @ui.refreshable
    def render(self):
        with ui.column().classes("w-full"):
            super().render()
            if not self.loading and self.message_id:
                with ui.row().classes("self-end"):
                    reasoning = Reasoning(
                        steps=self._reasoning_steps, drawer=self._drawer
                    )
                    ui.button(
                        "Insight",
                        icon="lightbulb",
                        on_click=reasoning.render,
                    ).props("outline")

                    ui.button(
                        "Feedback",
                        icon="star",
                        on_click=lambda: Feedback(
                            self.message_id, get_user_id()
                        ).render(),
                    ).props("outline")

    def render_avatar(self):
        ui.avatar(
            icon="img:/images/assistant.png",
            color="#E3AF28",
            rounded=True,
            size="2.75rem",
        )

    async def get_reasoning_steps(self):
        """
        Get the reasoning steps for the assistant message.
        """
        if self.message_id is None:
            self._reasoning_steps = []
            return

        self._reasoning_steps = []
        raw_reasoning_steps = await get_reasoning_steps_by_message(self.message_id)
        for step in raw_reasoning_steps:
            substeps = json.loads(step.content)
            if not len(self._reasoning_steps) != 0 and len(substeps) != 0:
                # Add a knowledge retrieval step if it is the first step
                # A separate knowledge retrieval step is not needed for now
                # since each step may have its own knowledge retrieval in the future
                self._reasoning_steps.append(
                    ReasoningStep(
                        name="KNOWLEDGE RETRIEVAL",
                        substeps=[
                            {"name": f"Data {i + 1}", "content": data}
                            for i, data in enumerate(substeps[0]["contexts"])
                        ],
                    )
                )
                # images_paths = []
                # for i, data in enumerate(substeps[0]["contexts"]):
                #     pattern = r'###IMAGES_START###\[(.*?)\]###IMAGES_END###'
                #     match = re.search(pattern, data)
                #     if match:
                #         image_paths_str = match.group(1)  # Get the matched content inside the brackets
                #         image_paths_str = image_paths_str.replace("'", '"') # Convert the string of image paths to a list                        
                #         try:
                #             image_paths_list = json.loads(f"[{image_paths_str}]")  # Wrap in brackets to form a valid JSON list
                #             images_paths.extend(image_paths_list)
                #         except json.JSONDecodeError as e:
                #             print(f"Error decoding JSON: {e}")
                
                # await self.set_context_images(images_paths)
            self._reasoning_steps.append(
                ReasoningStep(
                    name=step.name,
                    substeps=[
                        {"name": f"Thought {i + 1}", "content": substep["current"]}
                        for i, substep in enumerate(substeps)
                    ],
                )
            )

    async def set_message_id(self, message_id):
        await super().set_message_id(message_id)
        await self.get_reasoning_steps()
        self.render.refresh()
