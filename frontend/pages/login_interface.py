import re

from nicegui import app, ui

from backend.src.services.user import create_user, get_user_by_email


@ui.page("/login")
class LoginPage:
    """Login page"""

    def __init__(self):
        """Render the login page"""
        if app.storage.user.get("authenticated", False):
            ui.navigate.to("/")

        with ui.row().classes("w-full h-full"):
            with ui.column().classes("w-1/2 p-16 items-center h-full gap-6"):
                ui.label("FactoryLLM - An Open Safe AI Sandbox for Evaluating LLM in Smart Factories").classes(
                    "items-center text-4xl font-bold text-white"
                )
                ui.label(
                    "Explore the limitless possibilities of artificial intelligence "
                    "in a fun and engaging way."
                ).classes("text-center text-lg text-white")
                ui.image("images/banner.png").classes("w-2/3 mt-auto mb-auto")
            with ui.column().classes(
                "items-start justify-right p-16 h-full flex-1"
            ).style("background: #282C3E;"):
                ui.label("Try it now").classes(
                    "text-2xl font-bold mb-4 text-center text-white"
                )
                ui.label("Enter your Email").classes("text-lg")
                self.email_input = (
                    ui.input().classes("w-full mb-4").props("type=email dense outlined")
                )
                ui.button("Login", on_click=self.handle_login).classes(
                    "bg-primary text-white mb-4"
                )

    def validate_email(self, email):
        """Validate email address"""
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            return "Invalid email address"
        return None

    async def handle_login(self):
        """Get or create a user by email and redirect to the landing page"""
        email = self.email_input.value
        error = self.validate_email(email)
        if error:
            self.email_input.error = error
            return
        try:
            user = await get_user_by_email(email)
            if not user:
                user = await create_user(email)
        except Exception as e:
            ui.notify(f"Database error: {e}", type="negative", position="top")
            return

        app.storage.user["authenticated"] = True
        app.storage.user["email"] = email
        app.storage.user["user_id"] = user.id
        ui.navigate.to("/")  # Redirect to the landing page after login


@ui.page("/logout")
def logout():
    """Logout page"""
    app.storage.user.clear()
    ui.navigate.to("/login")
