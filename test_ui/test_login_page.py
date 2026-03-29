from playwright.sync_api import expect


def test_login_page(page):
    """Test the login page"""
    page.get_by_role("button", name="User profile").click()
    page.get_by_role("button", name="Logout").click()
    # Expect navigation to the login page
    expect(page).to_have_url("/login")

    page.get_by_label("").click()
    page.get_by_label("").fill("testuser@mail.com")
    page.get_by_role("button", name="Login").click()

    # Expect navigation to the landing page
    expect(page).to_have_url("/")

    # Expect the user to be authenticated
    expect(page.get_by_text("testuser@mail.com")).to_be_visible()
