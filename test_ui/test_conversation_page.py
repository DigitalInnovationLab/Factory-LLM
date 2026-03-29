import re

from playwright.sync_api import expect


def test_conversation_page(page):
    """Test the conversation page"""
    page.goto("/")
    expect(page.get_by_test_id("conv link")).to_have_count(2)

    # Should navigate to /task when creating a new conversation
    page.get_by_role("button", name="+ New Chat").click()
    page.get_by_role("button", name="Proceed").click()
    expect(page).to_have_url("/task")

    # Should navigate to /chat when clicking on a chat
    page.goto("/")
    page.get_by_test_id("conv link").first.click()
    expect(page).to_have_url(re.compile(r"\/chat\/\d+"))

    # TODO: The delete functionality is currently having bugs
    # Delete a chat
    # page.goto("/")
    # page.locator("button").filter(has_text="delete").first.click()
    # page.get_by_role("button", name="Delete").click()
    # expect(page.get_by_test_id("conv link")).to_have_count(1)
