from typing import Callable, Optional

from nicegui import events, ui
from pydantic import BaseModel

from backend.src.constants import LlmModel, RagTechnique, Technique
from backend.src.services.chat import create_chat, delete_chats_by_task_id
from backend.src.services.etl import insert_data
from backend.src.services.task import create_task, delete_task, update_task
from common import File
from frontend.components.auth_middleware import get_user_id
from frontend.components.backdrop import Backdrop
from frontend.components.task_form import EditForm, StartForm

tasks = []


class Task(BaseModel):
    """
    A task model.
    """

    id: Optional[int] = None
    name: str
    description: str
    initial_system_prompt: str
    llm_model: LlmModel
    prompting_technique: Technique


class TaskCard:
    """
    A component to render a task card.
    """

    description_limit = 150

    def __init__(
        self, task: Optional[Task] = None, on_new_task: Optional[Callable] = None
    ):
        self._card = None
        self._task = task
        self._on_new_task = on_new_task
        self.dialogs = {}
        self.forms = {}
        self.validation_messages = {}

        if task:
            self.render_delete_dialog()
            self.render_edit_dialog()
        self.render_start_dialog()

    @ui.refreshable
    def render_delete_dialog(self):
        """
        Render a dialog to delete the task.
        """
        with ui.dialog() as dialog, ui.card().props("flat").style(
            "background-color: var(--color-background-secondary); border-radius: 0.5rem; "
            "width: 20rem;"
        ):
            self.dialogs["delete"] = dialog
            with ui.card_section().classes("p-0 row items-center w-full"):
                ui.label("Delete Task?").classes("text-2xl font-bold")
                ui.space()
                ui.button(on_click=dialog.close).props("icon='close' flat round dense")

            with ui.card_section().classes("p-0"):
                ui.label(f"This will delete {self._task.name}")

            with ui.card_actions().props("align='right'").classes("w-full px-0"):
                ui.button("Cancel", on_click=dialog.close).props("outline").classes(
                    "rounded-lg"
                ).style("padding: 0 1rem;")
                ui.button("Delete", on_click=self.handle_delete).classes(
                    "rounded-lg"
                ).style("padding: 0 1rem;")

    @ui.refreshable
    def render_edit_dialog(self):
        """
        Render a dialog to edit the task.
        """
        if not self._task:
            return
        self.forms["edit"] = EditForm(
            name=self._task.name,
            description=self._task.description,
            prompt=self._task.initial_system_prompt,
            model=self._task.llm_model.name,
            technique=self._task.prompting_technique.name,
        )

        with ui.dialog() as dialog, ui.card().props("flat").classes("relative").style(
            "background-color: var(--color-background); border-radius: 0.5rem; \
            width: 700px; max-width: 80vw;"
        ):
            self.dialogs["edit"] = dialog
            with ui.card_section().classes(
                "pb-0 row items-center justify-center w-full"
            ):
                ui.label("Edit Task").classes("text-2xl font-bold")
                ui.button(on_click=dialog.close).props(
                    "icon='close' flat round dense"
                ).classes("absolute top-0 right-0")

            with ui.card_section().classes("w-full"):
                with ui.row().classes("gap-6 flex-wrap"):
                    with ui.column().classes("flex-1").style("min-width: 150px;"):
                        with ui.column().classes("gap-2 w-full"):
                            ui.label("Task Name")
                            ui.input(
                                value=self.forms["edit"].name,
                                on_change=lambda e: setattr(
                                    self.forms["edit"], "name", e.value[:26]
                                ),
                            ).props("dense outlined").classes("w-full")

                        with ui.column().classes("gap-2 w-full"):
                            ui.label("Task Description")
                            ui.input(
                                value=self.forms["edit"].description,
                                on_change=lambda e: setattr(
                                    self.forms["edit"], "description", e.value
                                ),
                            ).props("dense outlined").classes("w-full")

                        with ui.column().classes("gap-2 w-full"):
                            ui.label("Initial Prompt")
                            ui.textarea(
                                value=self.forms["edit"].prompt,
                                on_change=lambda e: setattr(
                                    self.forms["edit"], "prompt", e.value
                                ),
                            ).props("dense outlined").classes("w-full")

                    with ui.column().classes("flex-1").style("min-width: 150px;"):
                        with ui.column().classes("gap-2 w-full"):
                            ui.label("Default LLM Model")
                            ui.select(
                                options=[model.name for model in LlmModel],
                                value=self.forms["edit"].model,
                                on_change=lambda e: setattr(
                                    self.forms["edit"], "model", e.value
                                ),
                            ).props("dense outlined").classes("w-full")

                        with ui.column().classes("gap-2 w-full"):
                            ui.label("Default Prompt Technique")
                            ui.select(
                                options=[technique.name for technique in Technique],
                                value=self.forms["edit"].technique,
                                on_change=lambda e: setattr(
                                    self.forms["edit"], "technique", e.value
                                ),
                            ).props("dense outlined").classes("w-full")

                self.validation_messages["edit"] = ui.label("").classes(
                    "text-red-500 text-center"
                )

            with ui.card_actions().props("align='right'").classes("w-full px-0 gap-2"):
                ui.button("Cancel", on_click=dialog.close).props("outline").classes(
                    "rounded-lg"
                ).style("padding: 0 1rem;")
                ui.button("Save", on_click=self.handle_edit).props("primary").classes(
                    "rounded-lg"
                ).style("padding: 0 1rem;")

    @ui.refreshable
    def render_start_dialog(self):
        """
        Render a dialog before starting the task to upload documents.
        """
        self.forms["start"] = StartForm(
            rag_technique=RagTechnique.VECTOR.name,
            chunk_size=1024,
            chunk_overlap=40,
            vector_top_k=20,
            files=[],
        )
        with ui.dialog() as dialog, ui.card().props("flat").classes("relative").style(
            "background-color: var(--color-background); border-radius: 0.5rem; width: 500px;\
              max-width: 80vw;"
        ):
            self.dialogs["start"] = dialog
            with ui.card_section().classes(
                "pb-0 row items-center justify-center w-full"
            ):
                ui.label("Upload your documents").classes("text-2xl font-bold")
                ui.button(on_click=dialog.close).props(
                    "icon='close' flat round dense"
                ).classes("absolute top-0 right-0")

            with ui.card_section().classes("w-full"):
                with ui.column().classes("w-full"):
                    # with ui.column().classes("gap-2 w-full"):
                    #     ui.label("RAG Technique")
                    #     ui.select(
                    #         options=[
                    #             technique.name
                    #             for technique in RagTechnique
                    #             if technique != RagTechnique.NONE
                    #         ],
                    #         value=self.forms["start"].rag_technique,
                    #         on_change=lambda e: setattr(
                    #             self.forms["start"], "rag_technique", e.value
                    #         ),
                    #     ).props("dense outlined").classes("w-full")

                    # with ui.row().classes("gap-2 w-full"):
                    #     with ui.column().classes("gap-2 flex-1"):
                    #         ui.label("Chunk Size")
                    #         ui.number(
                    #             value=self.forms["start"].chunk_size,
                    #             min=1,
                    #             step=1,
                    #             on_change=lambda e: setattr(
                    #                 self.forms["start"], "chunk_size", int(e.value)
                    #             ),
                    #         ).props("dense outlined type='number'").classes("w-full")

                    #     with ui.column().classes("gap-2 flex-1"):
                    #         ui.label("Chunk Overlap")
                    #         ui.number(
                    #             value=self.forms["start"].chunk_overlap,
                    #             min=0,
                    #             step=1,
                    #             on_change=lambda e: setattr(
                    #                 self.forms["start"], "chunk_overlap", int(e.value)
                    #             ),
                    #         ).props("dense outlined type='number'").classes("w-full")

                    #     with ui.column().classes("gap-2 flex-1").bind_visibility_from(
                    #         self.forms["start"],
                    #         "rag_technique",
                    #         backward=lambda x: x == RagTechnique.VECTOR.name,
                    #     ):
                    #         ui.label("Top K for retrieval")
                    #         ui.number(
                    #             value=self.forms["start"].vector_top_k,
                    #             min=1,
                    #             step=1,
                    #             on_change=lambda e: setattr(
                    #                 self.forms["start"], "vector_top_k", int(e.value)
                    #             ),
                    #         ).props("dense outlined").classes("w-full")

                    def handle_single_upload(e: events.UploadEventArguments):
                        """
                        Handle the file upload.
                        """
                        self.forms["start"].files.append(
                            File(name=e.name, content=e.content)
                        )

                    def handle_remove_file(e: events.GenericEventArguments):
                        """
                        Handle the removal of a file.
                        """
                        self.forms["start"].files = [
                            file
                            for file in self.forms["start"].files
                            if e.args[0]["__key"].find(file.name) == -1
                        ]

                    with ui.column().classes("gap-2 w-full"):
                        ui.label("Content")

                        ui.upload(
                            multiple=True,
                            on_upload=handle_single_upload,
                            auto_upload=True,
                        ).props(
                            "label='Drag or drop files here (.pdf, .docx, .txt)' flat \
                        accept='.pdf,.docx,.doc,.txt'"
                        ).classes(
                            "w-full"
                        ).on(
                            "removed", handle_remove_file
                        ).style(
                            "color: #d3d3d3; background-color: transparent;"
                        )

                self.validation_messages["start_task"] = ui.label("").classes(
                    "text-red-500 text-center mt-1"
                )

            with ui.card_actions().props("align='right'").classes("w-full px-0 gap-2"):
                # disable if no files uploaded
                ui.button("Continue", on_click=self.handle_start).classes(
                    "rounded-lg"
                ).style("padding: 0 1rem;").bind_enabled_from(
                    self.forms["start"], "files", backward=lambda x: len(x) > 0
                )

    @ui.refreshable
    def render(self):
        """
        Render the task card.
        """
        card_style = (
            "min-height: 300px; max-height: 400px; display: flex; flex-direction: "
            "column; justify-content: space-between;"
        )

        if self._task:
            with ui.card().props("flat data-testid='task card'").classes(
                "p-3 rounded-lg cursor-pointer"
            ).style(
                f"background-color: var(--color-background-secondary); {card_style}"
            ) as card:
                self._card = card
                card.on("click", self.open_start)

                with ui.card_section().props("align='center'").classes(
                    "w-full px-0 pb-0"
                ):
                    ui.label(self._task.name).classes("text-2xl font-bold")

                with ui.card_section().props("align='center'").classes(
                    "w-full py-0 flex-grow"
                ):
                    shortened_description = (
                        self._task.description[: self.description_limit] + "..."
                        if len(self._task.description) > self.description_limit
                        else self._task.description
                    )
                    ui.label(shortened_description).classes("text-lg")

                with ui.card_actions().props("align='right'").classes("w-full mt-auto"):
                    ui.button(
                        "✏️", on_click=self.open_edit, color="var(--color-text);"
                    ).props("outline").style(
                        "padding-left: 13px; padding-right: 13px; "
                        "background-color: var(--color-background-secondary) !important;"
                    ).classes(
                        "rounded-lg"
                    ).on(
                        "click.stop", lambda: None
                    )
                    ui.button(
                        "🗑️", on_click=self.open_delete, color="var(--color-text);"
                    ).props("outline").style(
                        "padding-left: 13px; padding-right: 13px; "
                        "background-color: var(--color-background-secondary) !important;"
                    ).classes(
                        "rounded-lg"
                    ).on(
                        "click.stop", lambda: None
                    )
        else:
            self.render_add_task_card()

    def open_edit(self):
        """
        Open the edit dialog.
        """
        self.dialogs["edit"].open()

    async def handle_edit(self):
        """
        Save the edited task with validation.
        """
        edit_form: EditForm = self.forms.get("edit")
        if not edit_form.name.strip():
            self.validation_messages["edit"].set_text("Task Name is required!")
            return
        if not edit_form.description.strip():
            self.validation_messages["edit"].set_text("Task Description is required!")
            return
        if not edit_form.prompt.strip():
            self.validation_messages["edit"].set_text("Initial Prompt is required!")
            return

        self.validation_messages["edit"].set_text("")

        try:
            llm_model = LlmModel[edit_form.model]
        except ValueError:
            self.validation_messages["edit"].set_text(
                f"Invalid model: {edit_form.model}"
            )
            return

        try:
            prompt_technique = Technique[edit_form.technique]
        except ValueError:
            self.validation_messages["edit"].set_text(
                f"Invalid technique: {edit_form.technique}"
            )
            return

        updated_task = Task(
            id=self._task.id,
            name=edit_form.name.strip(),
            description=edit_form.description.strip(),
            initial_system_prompt=edit_form.prompt.strip(),  # Correct attribute name mapping
            llm_model=llm_model,
            prompting_technique=prompt_technique,
        )

        result = await update_task(self._task.id, updated_task)

        if result:
            self._task.name = updated_task.name
            self._task.description = updated_task.description
            self._task.initial_system_prompt = (
                updated_task.initial_system_prompt
            )  # Correct attribute name mapping
            self._task.llm_model = llm_model
            self._task.prompting_technique = prompt_technique

            # Refresh UI components
            self.render.refresh()
            self.dialogs["edit"].close()
            self.render_edit_dialog.refresh()
            self.render_delete_dialog.refresh()
        else:
            self.validation_messages["edit"].set_text(
                "Failed to update the task. Please try again."
            )

    def open_delete(self):
        """
        Open the delete dialog.
        """
        self.dialogs["delete"].open()

    async def handle_delete(self):
        """Delete the task."""
        if self._task:
            await delete_chats_by_task_id(self._task.id)

            await delete_task(self._task.id)

            if self._card:
                self._card.delete()

                if self._task in tasks:
                    tasks.remove(self._task)
                else:
                    print(f"Task {self._task} not found in the list.")

            self.dialogs["delete"].close()

    def open_start(self):
        """
        Open the start dialog.
        """
        self.dialogs["start"].open()

    async def handle_start(self):
        """
        Start the task.
        """
        if self.forms["start"].chunk_overlap >= self.forms["start"].chunk_size:
            self.validation_messages["start_task"].set_text(
                "Chunk overlap must be less than chunk size!"
            )
            return

        backdrop = Backdrop(
            [
                "Parsing documents...",
                "Chunking documents...",
                "Processing data...",
                "Inserting data...",
            ]
        )
        try:
            try:
                rag_technique = RagTechnique[self.forms["start"].rag_technique]
                if rag_technique == RagTechnique.VECTOR:
                    chat = await create_chat(
                        get_user_id(),
                        self._task.id,
                        rag_technique,
                        self.forms["start"].vector_top_k,
                    )
                else:
                    chat = await create_chat(get_user_id(), self._task.id, rag_technique)
            except Exception as e:
                raise Exception(f"Failed to create chat. Error: {e}")

            await insert_data(
                chat.id,
                self.forms["start"].files,
                technique=rag_technique,
                model=self._task.llm_model,
                chunk_size=self.forms["start"].chunk_size,
                chunk_overlap=self.forms["start"].chunk_overlap,
            )
            self.dialogs["start"].close()
            ui.navigate.to(f"/chat/{chat.id}")
        except Exception as e:
            self.validation_messages["start_task"].set_text(
                f"Failed to start the task. Please try again. Error: {e}"
            )
        finally:
            backdrop.close()

    def close_new_task_dialog(self):
        """
        Public method to close the new task dialog.
        """
        if self.dialogs.get("new_task"):
            self.dialogs["new_task"].close()

    def delete_card(self):
        """
        Public method to delete the card.
        """
        if self._card:
            self._card.delete()

    @ui.refreshable
    def render_add_task_card(self):
        """
        Render an Add new task card.
        """
        card_style = (
            "min-height: 300px; max-height: 400px; display: flex; flex-direction: column; "
            "justify-content: center; align-items: center;"
        )

        task_icon = "images/task_icon.png"

        with ui.card().props("flat").classes("p-3 rounded-lg cursor-pointer").style(
            f"background-color: var(--color-background-secondary); {card_style}"
        ) as card:
            self._card = card
            card.on("click", self.open_new_task_dialog)

            with ui.card_section().props("align='center'").classes("w-full px-0 pb-0"):
                ui.image(task_icon).classes("w-20 h-20")

            with ui.card_section().props("align='center'").classes("w-full px-0 pb-0"):
                ui.label("Add New Task").classes("font-bold").style("color: #606888;")

        self.render_new_task_dialog()

    def open_new_task_dialog(self):
        """
        Open the new task dialog.
        """
        self.dialogs["new_task"].open()

    @ui.refreshable
    def render_new_task_dialog(self):
        """
        Render the new task creation dialog.
        """
        self.forms["new_task"] = EditForm(
            name="",
            description="",
            prompt="",
            model=LlmModel.GPT4O_MINI.name,
            technique=Technique.COT.name,
        )
        with ui.dialog() as dialog, ui.card().props("flat").classes("relative").style(
            "background-color: var(--color-background); border-radius: 0.5rem; \
                 width: 700px; max-width: 80vw;"
        ):
            self.dialogs["new_task"] = dialog
            with ui.card_section().classes(
                "pb-0 row items-center justify-center w-full"
            ):
                ui.label("Create New Topic").classes("text-2xl font-bold")
                ui.button(on_click=dialog.close).props(
                    "icon='close' flat round dense"
                ).classes("absolute top-0 right-0")

            with ui.card_section().classes("w-full"):
                with ui.row().classes("gap-6 flex-wrap"):
                    with ui.column().classes("flex-1").style("min-width: 150px;"):
                        with ui.column().classes("gap-2 w-full"):
                            ui.label("Topic Name")
                            ui.input(
                                value=self.forms["new_task"].name,
                                on_change=lambda e: setattr(
                                    self.forms["new_task"], "name", e.value[:26]
                                ),
                            ).props("dense outlined").classes("w-full")

                        with ui.column().classes("gap-2 w-full"):
                            ui.label("Topic Description")
                            ui.input(
                                value=self.forms["new_task"].description,
                                on_change=lambda e: setattr(
                                    self.forms["new_task"], "description", e.value
                                ),
                            ).props("dense outlined").classes("w-full")

                        with ui.column().classes("gap-2 w-full"):
                            ui.label("Initial Prompt")
                            ui.textarea(
                                value=self.forms["new_task"].prompt,
                                on_change=lambda e: setattr(
                                    self.forms["new_task"], "prompt", e.value
                                ),
                            ).props("dense outlined").classes("w-full")

                    with ui.column().classes("flex-1").style("min-width: 150px;"):
                        with ui.column().classes("gap-2 w-full"):
                            ui.label("Default LLM Model")
                            ui.select(
                                options=[model.name for model in LlmModel],
                                value=self.forms["new_task"].model,
                                on_change=lambda e: setattr(
                                    self.forms["new_task"], "model", e.value
                                ),
                            ).props("dense outlined").classes("w-full")

                        with ui.column().classes("gap-2 w-full"):
                            ui.label("Default Prompt Technique")
                            ui.select(
                                options=[technique.name for technique in Technique],
                                value=self.forms["new_task"].technique,
                                on_change=lambda e: setattr(
                                    self.forms["new_task"], "technique", e.value
                                ),
                            ).props("dense outlined").classes("w-full")

                self.validation_messages["new_task"] = ui.label("").classes(
                    "text-red-500 text-center"
                )

            with ui.card_actions().props("align='right'").classes("w-full px-0 gap-2"):
                ui.button("Cancel", on_click=dialog.close).props("outline").classes(
                    "rounded-lg"
                ).style("padding: 0 1rem;")
                ui.button("Save", on_click=self.handle_new_task).classes(
                    "rounded-lg"
                ).style("padding: 0 1rem;")

    async def handle_new_task(self):
        """
        Add a new task card with validation.
        """
        new_task_form: EditForm = self.forms["new_task"]
        if not new_task_form.name.strip():
            self.validation_messages["new_task"].set_text("Task Name is required!")
            return
        if not new_task_form.description.strip():
            self.validation_messages["new_task"].set_text(
                "Task Description is required!"
            )
            return
        if not new_task_form.prompt.strip():
            self.validation_messages["new_task"].set_text("Initial Prompt is required!")
            return

        self.validation_messages["new_task"].set_text("")
        try:
            llm_model = LlmModel[new_task_form.model]
        except ValueError:
            self.validation_messages["new_task"].set_text(
                f"Invalid model: {new_task_form.model}"
            )
            return

        try:
            prompt_technique = Technique[new_task_form.technique]
        except ValueError:
            self.validation_messages["new_task"].set_text(
                f"Invalid technique: {new_task_form.technique}"
            )
            return

        task_data = {
            "name": new_task_form.name.strip(),
            "description": new_task_form.description.strip(),
            "initial_system_prompt": new_task_form.prompt.strip(),
            "llm_model": llm_model,
            "prompting_technique": prompt_technique,
        }

        task = await create_task(
            user_id=get_user_id(),
            task_name=task_data["name"],
            task_description=task_data["description"],
            initial_system_prompt=task_data["initial_system_prompt"],
            llm_model=task_data["llm_model"],
            prompting_technique=task_data["prompting_technique"],
        )

        new_task = Task(
            id=task.id,
            name=task.name,
            description=task.description,
            initial_system_prompt=task.initial_system_prompt,
            llm_model=task.llm_model,
            prompting_technique=task.prompting_technique,
        )
        if self._on_new_task:
            self._on_new_task(new_task)

        self.dialogs["new_task"].close()
