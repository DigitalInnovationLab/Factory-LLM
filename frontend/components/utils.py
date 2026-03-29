from nicegui import ui


def local_css(file_name):
    """Load local CSS file."""
    with open(file_name, encoding="utf-8") as f:
        css = f.read()
        ui.add_css(css)


def remote_css(url):
    """Load remote CSS file."""
    ui.add_head_html(f'<link href="{url}" rel="stylesheet">')
