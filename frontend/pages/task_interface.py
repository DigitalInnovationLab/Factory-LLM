from nicegui import ui

from backend.src.constants import LlmModel, Technique
from backend.src.services.task import get_tasks
from frontend.components import NavBar, Task, TaskCard
from frontend.components.auth_middleware import get_user_id

tasks = []


async def initialize_cards(page=0, per_page=10):
    """Fetch tasks from the DB and returns a list of task cards with names and descriptions"""
    tasks.clear()
    db_tasks, task_count = await get_tasks(get_user_id(), page, per_page)

    for db_task in db_tasks:
        tasks.append(
            Task(
                id=db_task.id,
                name=db_task.name,
                description=db_task.description,
                initial_system_prompt=db_task.initial_system_prompt,
                llm_model=LlmModel(db_task.llm_model),
                prompting_technique=Technique(db_task.prompting_technique),
            )
        )

    return tasks, task_count


@ui.page("/topic")
async def task_interface():
    """
    The task interface page.
    """
    await NavBar().render()

    page, per_page = 1, 7
    task_cards, task_count = await initialize_cards(page - 1, per_page)

    async def on_page_change(event):
        nonlocal page, task_count
        page = event.value
        task_cards, task_count = await initialize_cards(page - 1, per_page)
        render_task_cards.refresh(task_cards)

    with ui.column().classes("h-full w-full max-w-7xl mx-auto p-4 pt-8 gap-4"):
        ui.label("Choose a topic to start").classes(
            "w-full text-2xl font-bold text-center"
        )
        render_task_cards(task_cards)
        ui.pagination(
            1,
            task_count // per_page + 1,
            value=page,
            on_change=on_page_change,
            direction_links=True,
        ).classes("mx-auto")


@ui.refreshable
def render_task_cards(task_cards):
    """
    Renders the task cards on the task interface page
    """
    task_container = ui.scroll_area().classes("h-full w-full mx-auto")
    with task_container:
        with ui.grid(columns="repeat(auto-fill, minmax(240px, 1fr))").classes(
            "w-full gap-6"
        ) as grid:
            for task in task_cards:
                TaskCard(task).render()
            add_new_task_card = TaskCard(
                on_new_task=lambda new_task: add_task_to_grid(
                    new_task, grid, add_new_task_card
                )
            )
            add_new_task_card.render()


def add_task_to_grid(new_task, grid, add_new_task_card):
    """Adds a new task to the grid and makes sure add task card is at the end"""
    tasks.append(new_task)

    add_new_task_card.close_new_task_dialog()

    with grid:
        TaskCard(new_task).render()
        add_new_task_card.delete_card()
        add_new_task_card.render()
