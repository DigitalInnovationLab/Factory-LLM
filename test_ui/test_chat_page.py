import re

from playwright.sync_api import expect


def test_chat_page(page):
    """Test the chat page"""
    page.goto("/")
    page.get_by_test_id("conv link").first.click()

    # Can see the reasoning process
    page.get_by_role("button", name="Insight").click()
    expect(page.get_by_text("Reasoning Process")).to_be_visible()
    page.locator("button").filter(has_text="close").click()

    # Can add feedback
    page.get_by_role("button", name="Feedback").click()
    page.get_by_placeholder("Your response goes here").click()
    page.get_by_placeholder("Your response goes here").fill("Good")
    page.locator("button").filter(has_text=re.compile(r"^star$")).nth(3).click()
    page.get_by_role("button", name="Submit").click()
