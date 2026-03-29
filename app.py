from nicegui import app, ui

# isort: off
# has to import in this order to avoid circular imports
import frontend.pages.task_interface  # pylint: disable=unused-import
import frontend.pages.chat_interface  # pylint: disable=unused-import

# isort: on

import frontend.pages.conv_interface  # pylint: disable=unused-import
import frontend.pages.login_interface  # pylint: disable=unused-import
from frontend.components import local_css
from frontend.components.auth_middleware import STORAGE_SECRET, AuthMiddleware



def setup_ui():
    """
    Setup the UI with custom theme and styles
    """
    ui.colors(primary="#6FEBFA")
    ui.dark_mode().enable()
    ui.add_css(
        r"a:link, a:visited {color: inherit !important; text-decoration: none; font-weight: 500}"
    )
    ui.add_css("* { color: #FFEAEF; }")
    local_css("frontend/components/css/theme.css")
    ui.query(".q-page").classes("flex")
    ui.query(".nicegui-content").classes("w-full p-0").style(
        "background-color: var(--color-background);"
    )


app.add_media_files("/images", "images")
app.add_media_files("/extracted_images", "extracted_images")
app.on_connect(setup_ui)

app.add_middleware(AuthMiddleware)
ui.run(storage_secret=STORAGE_SECRET, port=8888, title="AI Playground", reload=False, dark=True, uvicorn_reload_excludes=".venv/*")
