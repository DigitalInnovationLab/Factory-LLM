from fastapi import Request
from fastapi.responses import RedirectResponse
from nicegui import app
from starlette.middleware.base import BaseHTTPMiddleware

from backend.src.services.chat import get_chats_by_user

unrestricted_page_routes = {"/login", "/logout"}


class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware to restrict access to authenticated users only."""

    async def dispatch(self, request: Request, call_next):
        # Ensure the storage secret is set before using session storage
        if not app.storage.user.get("authenticated", False):
            if (
                not request.url.path.startswith("/_nicegui")
                and request.url.path not in unrestricted_page_routes
            ):
                app.storage.user[
                    "referrer_path"
                ] = request.url.path  # remember where the user wanted to go
                return RedirectResponse("/login")
        return await call_next(request)


STORAGE_SECRET = "private key to secure the browser session cookie"


def get_user_email():
    """Get the email of the current user"""
    return app.storage.user.get("email", None)


def get_user_id():
    """Get the user id of the current user"""
    return app.storage.user.get("user_id", None)


async def get_chat_id():
    """Get the chat id of the current user"""
    chat_id = app.storage.user.get("chat_id", None)
    if not chat_id:
        chats, _ = await get_chats_by_user(get_user_id(), limit=1)
        if len(chats) == 0:
            return None
        chat_id = chats[0].id
    return chat_id
