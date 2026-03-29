from typing import List, Optional

from sqlalchemy import delete, func, select

from backend.src.constants import LlmModel, Technique
from backend.src.models import Session, Task


# pylint: disable=too-many-arguments
async def create_task(
    user_id: int,
    task_name: str,
    task_description: str,
    initial_system_prompt: str,
    llm_model: LlmModel = LlmModel.GPT4O,
    prompting_technique: Technique = Technique.NONE,
) -> Task:
    """
    Create a new task
    """
    async with Session() as session:
        task = Task(
            user_id=user_id,
            name=task_name,
            description=task_description,
            initial_system_prompt=initial_system_prompt,
            llm_model=llm_model,
            prompting_technique=prompting_technique,
        )
        session.add(task)
        await session.commit()
        return task


async def get_task_by_id(task_id: int) -> Optional[Task]:
    """
    Get a task by id
    """
    async with Session() as session:
        return await session.get(Task, task_id)


async def get_tasks(
    user_id: int, page: int = 0, limit: int = 10
) -> tuple[List[Task], int]:
    """
    Get a list of tasks and the total count of tasks for a user.
    """
    async with Session() as session:
        count = (
            await session.execute(
                # pylint: disable-next=not-callable # false positive
                select(func.count())
                .select_from(Task)
                .where(Task.user_id == user_id)
            )
        ).scalar()
        stmt = (
            select(Task)
            .where(Task.user_id == user_id)
            .limit(limit)
            .offset(page * limit)
            .order_by(Task.created_at.desc())
        )
        tasks = (await session.scalars(stmt)).all()

        return tasks, count


async def update_task(task_id: int, updated_task: Task) -> Optional[Task]:
    """
    Edit an existing task with new values.
    """
    async with Session() as session:
        task = await session.get(Task, task_id)
        if task is None:
            return None

        task.name = updated_task.name
        task.description = updated_task.description
        task.initial_system_prompt = updated_task.initial_system_prompt
        task.llm_model = updated_task.llm_model
        task.prompting_technique = updated_task.prompting_technique
        await session.commit()
        return task


async def delete_task(task_id: int):
    """
    Delete a task by its ID.
    """
    async with Session.begin() as session:
        stmt = delete(Task).where(Task.id == task_id)
        await session.execute(stmt)
