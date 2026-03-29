import re

from playwright.sync_api import expect


def test_navbar(page):
    """Test the navbar"""
    page.get_by_role("link", name="🏡 Home").click()
    expect(page).to_have_url("/")

    page.get_by_role("link", name="📝 Task").click()
    expect(page).to_have_url("/task")

    page.get_by_role("link", name="💬 Chat").click()
    expect(page).to_have_url(re.compile(r"\/chat\/\d+"))
