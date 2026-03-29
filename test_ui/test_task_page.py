from playwright.sync_api import expect


def test_task_page(page):
    """Test the task page"""
    page.goto("/task")
    expect(page.get_by_test_id("task card")).to_have_count(1)

    # Add a new task
    page.get_by_role("main").locator("img").click()
    page.get_by_label("", exact=True).first.click()
    page.get_by_label("", exact=True).first.fill("New Test Task")
    page.get_by_label("", exact=True).first.press("Tab")
    page.get_by_label("", exact=True).nth(1).fill("Sample Description")
    page.locator("textarea").fill("Sample Initial Prompt")
    page.get_by_role("button", name="Save").click()

    expect(page.get_by_text("New Test Task")).to_be_visible()
    expect(page.get_by_test_id("task card")).to_have_count(2)

    # Edit task
    page.get_by_role("button", name="✏️").first.click()
    expect(page.get_by_text("Edit Task")).to_be_visible()
    page.locator("button").filter(has_text="close").click()

    # Delete task
    page.get_by_role("button", name="🗑️").first.click()
    page.get_by_role("button", name="Delete").click()
    expect(page.get_by_test_id("task card")).to_have_count(1)

    # Can Start a task
    page.get_by_test_id("task card").first.click()
    expect(page.get_by_text("Upload your documents")).to_be_visible()
    page.locator("button").filter(has_text="close").click()
