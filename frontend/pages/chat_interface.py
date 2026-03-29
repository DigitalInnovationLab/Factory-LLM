from typing import List

from nicegui import ui

from backend.src.constants import LlmModel, RagTechnique, Technique
from backend.src.models import Message, MessageRole, Task
from backend.src.services.ask import ChatService
from backend.src.services.chat import add_message_to_chat, get_chat_by_id
from backend.src.services.file import get_files_by_chat
from backend.src.services.task import get_task_by_id
from frontend.components import AssistantMessage, NavBar, UserMessage
from frontend.components.auth_middleware import get_chat_id


class ChatContext:
    """
    Chat context containing chat ID, technique, and model.
    """

    def __init__(
        self,
        chat_id: int,
        technique: Technique,
        model: LlmModel,
        rag_technique: RagTechnique,
        vector_top_k: int = 3,
    ):
        self.chat_id = chat_id
        self.technique = technique
        self.model = model
        self.rag_technique = rag_technique
        self.vector_top_k = vector_top_k


# def handle_file_upload(e):
#     """
#     Handle file upload.
#     """
#     print(f"Uploaded {e.name}, content length: {len(e.content)}")


async def add_task_details(task: Task, context: ChatContext):
    """
    Adds task details to left drawer
    """
    ui.label(f"{task.name}").classes("text-lg font-bold")
    ui.label(f"Description: {task.description}").classes("text-md").style(
        "white-space: pre-wrap;"
    )
    ui.label(f"Initial Prompt: {task.initial_system_prompt}").classes("text-md").style(
        "white-space: pre-wrap;"
    )

    # ui.label("Prompt Technique:").classes("text-md mt-3")

    # def set_technique(e):
    #     context.technique = Technique[e.value]

    # ui.select(
    #     options=[technique.name for technique in Technique],
    #     value=context.technique.name,
    #     on_change=set_technique,
    # ).props("dense outlined").classes("w-full")

    # if context.rag_technique == RagTechnique.VECTOR:
    #     ui.label("Top K for retrieval:").classes("text-md mt-3")

    #     def set_top_k(e):
    #         context.vector_top_k = int(e.value)

    #     ui.number(
    #         value=context.vector_top_k,
    #         min=1,
    #         step=1,
    #         on_change=set_top_k,
    #     ).props("dense outlined type='number'").classes("w-full")

    ui.label("Model:").classes("text-md mt-3")

    # def set_model(e):
    #     context.technique = LlmModel[e.value]
    with ui.card().props("flat bordered").classes("bg-transparent w-full"):
                # remove the .*.bin. if it exists
                ui.label(context.model.name).classes("text-md").style("white-space: pre-wrap;")

    # ui.select(
    #     options=[model.name for model in LlmModel],
    #     value=context.model.name
    # ).props("dense outlined disable").classes("w-full")

    # ui.label("RAG Technique:").classes("text-md mt-3")
    # ui.select(
    #     options=[technique.name for technique in RagTechnique],
    #     value=context.rag_technique.name,
    # ).props("dense outlined disable").classes("w-full")
    

    files = await get_files_by_chat(context.chat_id)

    if files:
        ui.label("Files:").classes("text-md mt-3")
        for file in files:
            with ui.card().props("flat bordered").classes("bg-transparent w-full"):
                # remove the .*.bin. if it exists
                file_name = file.name.split(".bin.")[-1]
                ui.label(file_name).classes("text-md").style("white-space: pre-wrap;")

    # Disable model selection and file upload for now
    # ui.label("LLM Model:").classes("text-md mt-3")

    # def set_model(e):
    #     context.model = e.value

    # ui.select(
    #     options=[model.name for model in LlmModel],
    #     value=context.model,
    #     on_change=set_model,
    # ).props("dense outlined").classes("w-full")

    # ui.label("Upload your documents").classes("text-lg font-bold mt-6")
    # ui.upload(multiple=True, on_upload=handle_file_upload, auto_upload=True).props(
    #     "label='Drag or drop files here (.pdf, .docx, .txt)' flat accept='.pdf,.docx,.doc,.txt'"
    # ).classes("w-full")


# pylint: disable=too-many-statements
# Chat interface must get initial-prompt from task and append it into the messages array
@ui.page("/chat/{chat_id}")
async def chat_interface(chat_id: int):
    """
    The chat interface page.
    """
    await NavBar().render()

    if not chat_id:
        chat_id = await get_chat_id()
        if not chat_id:
            ui.navigate.to("/")
            return

    chat_service = ChatService()

    chat = await get_chat_by_id(chat_id)
    if not chat:
        ui.navigate.to("/")
        return

    messages: List[Message] = []

    task = await get_task_by_id(chat.task_id)
    context = ChatContext(
        chat_id,
        task.prompting_technique,
        task.llm_model,
        chat.rag_technique,
        chat.vector_top_k,
    )

    async def send() -> None:
        """
        Sends the user's input.
        """
        question = text.value
        if not question:
            return

        text.value = ""

        with message_container:
            user_message = UserMessage(text=question)
            user_message.render()

            assistant_message = AssistantMessage(loading=True, drawer=right_drawer)
            assistant_message.render()
            message_container.scroll_to(percent=100, duration=2)

        input_message = await add_message_to_chat(
            chat_id=context.chat_id, content=question, role=MessageRole.USER
        )
        response = await chat_service.get_response(
            context.chat_id,
            question,
            messages,
            context.technique,
            context.model,
            context.rag_technique,
            context.vector_top_k,
        )
        messages.extend([input_message, response])

        await assistant_message.set_message_id(response.id)
        assistant_message.text = response.content
        assistant_message.loading = False
        message_container.scroll_to(percent=100, duration=2)

    ui.add_css(".main-chat .q-scrollarea__content { align-items: stretch; }")
    message_container = ui.scroll_area().classes(
        "h-full w-full max-w-3xl mx-auto main-chat"
    )

    with ui.left_drawer(bottom_corner=True).style(
        "background-color: var(--color-background-secondary)"
    ):
        if task:
            await add_task_details(task, context)
        else:
            ui.label("No task selected.")

    right_drawer = (
        ui.right_drawer(value=False, fixed=False, bottom_corner=True)
        .props("width=350")
        .style("background-color: var(--color-background-secondary)")
    )

    with message_container:
        for message in chat.messages:
            if message.role == MessageRole.USER:
                user_message = UserMessage(text=message.content, message_id=message.id)
                user_message.render()
            else:
                assistant_message = AssistantMessage(
                    text=message.content, message_id=message.id, drawer=right_drawer
                )
                await assistant_message.setup()
                assistant_message.render()

            messages.append(message)

    message_container.scroll_to(percent=100, duration=0)

    with ui.footer().style("background-color: var(--color-background);"):
        placeholder = "message"
        text = (
            ui.input(placeholder=placeholder)
            .props("outlined input-class=mx-3 input-style='color: #FFEAEF;'")
            .classes("w-full max-w-3xl mx-auto self-center")
            .on("keydown.enter", send)
        )
        with text:  # pylint: disable=not-context-manager # (note: false positive)
            ui.button(on_click=send, icon="send").props("flat dense").bind_enabled_from(
                text, "value"
            )


# pylint: enable=too-many-statements
