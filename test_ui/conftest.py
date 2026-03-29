import pytest
from playwright.sync_api import Page, expect


@pytest.fixture(scope="function", autouse=True)
def authenticate_user(page: Page):
    """Authenticate user"""
    page.goto("/login")
    page.get_by_label("").click()
    page.get_by_label("").fill("testuser@mail.com")
    page.get_by_role("button", name="Login").click()

    # Ensure the user is authenticated
    expect(page).to_have_url("/")

    yield

    # Logout user
    page.get_by_role("button", name="User profile").click()
    page.get_by_role("button", name="Logout").click()
