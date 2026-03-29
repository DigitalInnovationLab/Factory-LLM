from nicegui import ui

from frontend.components.auth_middleware import get_chat_id, get_user_email


class NavBar:
    """
    A component to render a navigation bar.
    """

    async def render(self):
        """
        Render the navigation bar.
        """
        chat_path = "/"
        chat_id = await get_chat_id()
        if chat_id:
            chat_path = f"/chat/{chat_id}"

        with ui.header().style(
            "justify-content: space-between; background-color: var(--color-background-secondary)"
        ):
            ui.label("AI Playground").classes("text-xl font-bold")
            with ui.row().classes("items-center text-lg gap-24"):
                ui.link("🏡 Home", "/")
                ui.link("📝 Topic", "/topic")
                ui.link("💬 Chat", chat_path)
            with ui.row().classes("gap-4 align-right items-center"):
                ui.label(get_user_email())
                with ui.button().props("outline round padding='none'"):
                    with ui.avatar(size="2rem"):
                        ui.image("images/user_profile.png").props('alt="User profile"')
                    with ui.menu().classes("p-4"):
                        with ui.column().classes("gap-4"):
                            ui.label(f"User Email: {get_user_email()}")
                            ui.button(
                                "Logout", on_click=lambda: ui.navigate.to("/logout")
                            ).props("outline dense").classes("ml-auto capitalize px-3")
