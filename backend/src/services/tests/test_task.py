import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from backend.src import models
from backend.src.constants import LlmModel, Technique
from backend.src.models import Base, Task, User
from backend.src.services import task
from backend.src.services.task import (
    create_task,
    delete_task,
    get_task_by_id,
    get_tasks,
    update_task,
)


# pylint: disable=redefined-outer-name
# Async session fixture connected to an in-memory SQLite database
@pytest.fixture
async def async_session():
    """Set up the in-memory database and return an async session."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async_session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)
    yield async_session_factory
    await engine.dispose()


@pytest.fixture(autouse=True)
def patch_session(async_session, monkeypatch):
    """Monkeypatch the Session in models and services to use the async_session fixture"""
    monkeypatch.setattr(models, "Session", async_session)
    monkeypatch.setattr(task, "Session", async_session)


# Test creating a new task
@pytest.mark.asyncio
async def test_create_task(async_session):
    """Test the create_task function."""
    # Create a user
    async with async_session() as session:
        user = User(email="testuser@example.com")
        session.add(user)
        await session.commit()

    # Define task details
    task_name = "Test Task"
    task_description = "This is a test task."
    initial_system_prompt = "Initial prompt"
    llm_model = LlmModel.GPT4O
    prompting_technique = Technique.NONE

    # Call the function under test
    task = await create_task(
        user_id=user.id,
        task_name=task_name,
        task_description=task_description,
        initial_system_prompt=initial_system_prompt,
        llm_model=llm_model,
        prompting_technique=prompting_technique,
    )

    # Assertions
    assert task.id is not None
    assert task.user_id == user.id
    assert task.name == task_name
    assert task.description == task_description
    assert task.initial_system_prompt == initial_system_prompt
    assert task.llm_model == llm_model
    assert task.prompting_technique == prompting_technique

    # Verify that the task is stored in the database
    async with async_session() as session:
        stored_task = await session.get(Task, task.id)
        assert stored_task is not None
        assert stored_task.name == task_name


# Test getting a task by ID
@pytest.mark.asyncio
async def test_get_task_by_id(async_session):
    """Test the get_task_by_id function."""
    # Create a user and task
    async with async_session() as session:
        user = User(email="testuser2@example.com")
        session.add(user)
        await session.commit()

        task = Task(
            user_id=user.id,
            name="Test Task 2",
            description="Another test task.",
            initial_system_prompt="Initial prompt 2",
            llm_model=LlmModel.GPT4O,
            prompting_technique=Technique.NONE,
        )
        session.add(task)
        await session.commit()

    # Call the function under test
    fetched_task = await get_task_by_id(task_id=task.id)

    # Assertions
    assert fetched_task is not None
    assert fetched_task.id == task.id
    assert fetched_task.name == "Test Task 2"


# Test getting tasks for a user
@pytest.mark.asyncio
async def test_get_tasks(async_session):
    """Test the get_tasks function."""
    # Create a user and multiple tasks
    async with async_session() as session:
        user = User(email="testuser3@example.com")
        session.add(user)
        await session.commit()

        tasks = [
            Task(
                user_id=user.id,
                name=f"Task {i}",
                description=f"Description {i}",
                initial_system_prompt=f"Prompt {i}",
                llm_model=LlmModel.GPT4O,
                prompting_technique=Technique.NONE,
            )
            for i in range(5)
        ]
        session.add_all(tasks)
        await session.commit()

    # Call the function under test
    fetched_tasks, task_count = await get_tasks(user_id=user.id)

    # Assertions
    assert len(fetched_tasks) == 5
    assert task_count == 5
    fetched_task_names = [task.name for task in fetched_tasks]
    expected_task_names = [f"Task {i}" for i in (range(5))]
    assert fetched_task_names == expected_task_names


# Test updating a task
@pytest.mark.asyncio
async def test_update_task(async_session):
    """Test the update_task function."""
    # Create a user and a task
    async with async_session() as session:
        user = User(email="testuser4@example.com")
        session.add(user)
        await session.commit()

        task = Task(
            user_id=user.id,
            name="Original Task",
            description="Original Description",
            initial_system_prompt="Original Prompt",
            llm_model=LlmModel.GPT4O_MINI,
            prompting_technique=Technique.NONE,
        )
        session.add(task)
        await session.commit()
        task_id = task.id

    # Prepare updated task data
    updated_task = Task(
        name="Updated Task",
        description="Updated Description",
        initial_system_prompt="Updated Prompt",
        llm_model=LlmModel.GPT35,
        prompting_technique=Technique.GOT,
    )

    # Test non-exist task_id
    updated_task_result = await update_task(task_id=999, updated_task=updated_task)
    assert updated_task_result is None
    # Call the function under test
    updated_task_result = await update_task(task_id=task_id, updated_task=updated_task)

    # Assertions
    assert updated_task_result is not None
    assert updated_task_result.id == task_id
    assert updated_task_result.name == "Updated Task"
    assert updated_task_result.description == "Updated Description"
    assert updated_task_result.initial_system_prompt == "Updated Prompt"
    assert (
        updated_task_result.llm_model == LlmModel.GPT35
    )  # Remove this and we get intergrity error due to non nullable field so updated
    assert (
        updated_task_result.prompting_technique == Technique.GOT
    )  # Remove this and we get intergrity error due to non nullable field so updated

    # Verify changes in the database
    async with async_session() as session:
        stored_task = await session.get(Task, task_id)
        assert stored_task.name == "Updated Task"
        assert stored_task.description == "Updated Description"
        assert stored_task.initial_system_prompt == "Updated Prompt"
        assert (
            stored_task.llm_model == LlmModel.GPT35
        )  # Remove this and we get intergrity error due to non nullable field so updated
        assert (
            stored_task.prompting_technique == Technique.GOT
        )  # Remove this and we get intergrity error due to non nullable field so updated


# Test deleting a task
@pytest.mark.asyncio
async def test_delete_task(async_session):
    """Test the delete_task function."""
    # Create a user and a task
    async with async_session() as session:
        user = User(email="testuser5@example.com")
        session.add(user)
        await session.commit()

        task = Task(
            user_id=user.id,
            name="Task to Delete",
            description="Description",
            initial_system_prompt="Prompt",
            llm_model=LlmModel.GPT4O,
            prompting_technique=Technique.NONE,
        )
        session.add(task)
        await session.commit()
        task_id = task.id

    # Call the function under test
    await delete_task(task_id=task_id)

    # Verify that the task has been deleted
    async with async_session() as session:
        deleted_task = await session.get(Task, task_id)
        assert deleted_task is None
