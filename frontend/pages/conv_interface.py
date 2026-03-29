from nicegui import ui

from backend.src.services.chat import delete_chat_by_id, get_chats_by_user
from frontend.components import NavBar
from frontend.components.auth_middleware import get_user_id

# pylint: disable=too-many-statements


@ui.page("/")
async def conv_interface():
    """
    The conversation interface page.
    """
    await NavBar().render()

    page, per_page = 1, 8
    conv_count = 0

    @ui.refreshable
    async def load_conversations(conversation_list_container):
        """Load conversations from the chat service and update the UI."""
        nonlocal page, per_page, conv_count

        user_id = get_user_id()  # Get the user ID dynamically

        if user_id is None:
            ui.notify("User not authenticated.")
            return

        conversations, conv_count = await get_chats_by_user(
            user_id, page - 1, per_page, populate_task=True
        )

        if not conversations:
            ui.notify("No conversations found.")
            return  # Added return to prevent further execution if no conversations

        # Clear the container before adding new content
        conversation_list_container.clear()

        # Display each conversation
        for chat in conversations:
            task_name = chat.task.name if chat.task else "Unknown Task"

            # Modify the chat name to include task name and chat ID
            chat_name = f"{task_name} (Chat ID: {chat.id})"
            chat_link = f"/chat/{chat.id}"
            with conversation_list_container:
                with ui.card().classes(
                    "p-4 bg-gray-800 rounded-lg w-full no-shadow hover:bg-gray-700"
                ):
                    with ui.row().classes("w-full justify-between items-center"):
                        
                        with ui.link(target=chat_link).classes("contents").props(
                            'data-testid="conv link"'
                        ):
                            ui.label(f"Chat Name: {chat_name}").classes(
                                "text-lg font-semibold text-white"
                            )

                        # delete_chat function within the loop to capture chat.id and chat_name
                        def delete_chat(chat_id=chat.id, chat_name=chat_name):
                            """Delete the chat after confirmation."""
                            # Confirmation dialog
                            with ui.dialog() as dialog, ui.card().props("flat").style(
                                "background-color: var(--color-background-secondary);"
                                + " border-radius: 0.5rem;"
                            ):
                                with ui.card_section().classes(
                                    "p-0 row items-center w-full"
                                ):
                                    ui.label("Delete Chat?").classes(
                                        "text-2xl font-bold"
                                    )
                                    ui.space()
                                    ui.button(on_click=dialog.close).props(
                                        "icon='close' flat round dense"
                                    )

                                with ui.card_section().classes("p-0"):
                                    ui.label(f"This will delete chat '{chat_name}'")

                                with ui.card_actions().props("align='right'").classes(
                                    "w-full px-0"
                                ):
                                    ui.button("Cancel", on_click=dialog.close).props(
                                        "outline"
                                    ).classes("rounded-lg")
                                    # pylint: disable=cell-var-from-loop
                                    ui.button(
                                        "Delete",
                                        on_click=lambda: proceed_to_delete_chat(
                                            dialog, chat_id
                                        ),
                                    ).classes("rounded-lg")
                                # pylint: enable=cell-var-from-loop
                            dialog.open()

                        async def proceed_to_delete_chat(dialog, chat_id):
                            """Proceed with deleting the chat."""
                            await delete_chat_by_id(chat_id)
                            # Clear and reload conversations
                            conversation_list_container.clear()
                            load_conversations(conversation_list_container)
                            dialog.close()

                        # Attach the delete_chat function to the delete button
                        ui.button(icon="delete", on_click=delete_chat).props("outline")

        ui.pagination(
            1,
            conv_count // per_page + 1,
            value=page,
            on_change=lambda event, container=conversation_list_container: on_page_change(
                event, container
            ),
            direction_links=True,
        ).classes("mx-auto mt-auto mb-5")

    async def on_page_change(event, conversation_list_container):
        """Handle the page change event."""
        nonlocal page
        page = event.value
        await load_conversations.refresh(conversation_list_container)

    async def render():
        with ui.column().classes("max-w-screen-md w-full h-full mx-auto px-2"):
            # Add the '+ New Chat' button aligned to the right
            with ui.row().classes("w-full justify-front mt-8"):

                def open_new_conversation_dialog():
                    """Open a confirmation dialog to create a new conversation."""
                    with ui.dialog() as dialog, ui.card().props("flat").style(
                        "background-color: var(--color-background-secondary);"
                        + " border-radius: 0.5rem;"
                    ):
                        with ui.card_section().classes("p-0 row items-center w-full"):
                            ui.label("Create New Chat?").classes("text-2xl font-bold")
                            ui.space()
                            ui.button(on_click=dialog.close).props(
                                "icon='close' flat round dense"
                            )

                        with ui.card_section().classes("p-0"):
                            ui.label("Do you want to create a new conversation?")

                        with ui.card_actions().props("align='right'").classes(
                            "w-full px-0"
                        ):
                            ui.button("Cancel", on_click=dialog.close).props(
                                "outline"
                            ).classes("rounded-lg")
                            ui.button(
                                "Proceed",
                                on_click=lambda: proceed_to_create_new_conversation(
                                    dialog
                                ),
                            ).classes("rounded-lg")
                    dialog.open()  # Ensure the dialog is explicitly opened

                ui.button("+ New Chat", on_click=open_new_conversation_dialog).props(
                    "flat"
                ).classes("text-lg font-semibold text-white bg-gray-500")

            conversation_list_container = ui.column().classes("w-full")
            await load_conversations(conversation_list_container)

    async def proceed_to_create_new_conversation(dialog):
        """Proceed with creating a new conversation and redirect to the task page."""
        dialog.close()  # Close the dialog first
        ui.navigate.to("/task")  # Redirect to the task creation page

    # Ensure to call the render function at the right place in your app
    await render()


# pylint: enable=too-many-statements
