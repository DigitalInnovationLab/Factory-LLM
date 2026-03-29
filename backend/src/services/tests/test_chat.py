# pylint: disable=redefined-outer-name, import-outside-toplevel, R0801
import json
from datetime import datetime

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from backend.src.models import (
    Base,
    Chat,
    Message,
    MessageRole,
    ReasoningStep,
    Task,
    User,
)
from backend.src.services.chat import (
    add_message_to_chat,
    add_reasoning_step_to_message,
    add_reasoning_steps_to_message,
    create_chat,
    delete_chat_by_id,
    delete_chats_by_task_id,
    get_chat_by_id,
    get_chats_by_user,
    get_reasoning_steps_by_message,
)


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


# Monkeypatch the Session in backend.src.models and services to use the async_session fixture
@pytest.fixture(autouse=True)
def patch_session(async_session, monkeypatch):
    """
    Monkeypatch the Session in backend.src.models and services to use the async_session fixture
    """
    from backend.src import models
    from backend.src.services import chat

    monkeypatch.setattr(models, "Session", async_session)
    monkeypatch.setattr(chat, "Session", async_session)


# Test creating a new chat
@pytest.mark.asyncio
async def test_create_chat(async_session):
    """Test the create_chat function with ORM interactions."""
    # Create a user and a task
    async with async_session() as session:
        user = User(email="testuser@example.com")
        session.add(user)
        await session.commit()

        task = Task(
            description="Test Task",
            user_id=1,
            name="Test",
            initial_system_prompt="Test Prompt",
        )
        session.add(task)
        await session.commit()

    # Call the function under test
    chat = await create_chat(user_id=user.id, task_id=task.id)

    # Assertions
    assert chat.id is not None
    assert chat.user_id == user.id
    assert chat.task_id == task.id

    # Verify that the chat is actually stored in the database
    async with async_session() as session:
        fetched_chat = await session.get(Chat, chat.id)
        assert fetched_chat is not None
        assert fetched_chat.user_id == user.id
        assert fetched_chat.task_id == task.id


# Test getting a chat by ID
@pytest.mark.asyncio
async def test_get_chat_by_id(async_session):
    """Test the get_chat_by_id function with ORM interactions."""
    # Create a user, task, and chat
    async with async_session() as session:
        user = User(email="testuser2@example.com")
        session.add(user)
        await session.commit()

        task = Task(
            id=1,
            user_id=1,
            description="Test Task 2",
            name="Test2",
            initial_system_prompt="Test Prompt",
        )
        session.add(task)
        await session.commit()

        chat = Chat(user_id=user.id, task_id=task.id, id=1)
        session.add(chat)
        await session.commit()

        # Add messages to the chat
        messages = [
            Message(chat_id=chat.id, content="Hello", role=MessageRole.USER),
            Message(chat_id=chat.id, content="Hi there!", role=MessageRole.ASSISTANT),
        ]
        session.add_all(messages)
        await session.commit()

    # Call the function under test
    fetched_chat = await get_chat_by_id(chat_id=chat.id)

    # Assertions
    assert fetched_chat is not None
    assert fetched_chat.id == chat.id
    assert len(fetched_chat.messages) == 2
    assert fetched_chat.messages[0].content == "Hello"
    assert fetched_chat.messages[1].content == "Hi there!"


# Test deleting a chat by ID
@pytest.mark.asyncio
async def test_delete_chat_by_id(async_session):
    """Test the delete_chat_by_id function with ORM interactions."""
    # Create a user, task, and chat
    async with async_session() as session:
        user = User(email="testuser3@example.com")
        session.add(user)
        await session.commit()

        task = Task(
            id=1,
            user_id=1,
            description="Test Task 3",
            name="Test3",
            initial_system_prompt="Test Prompt",
        )
        session.add(task)
        await session.commit()

        chat = Chat(user_id=user.id, task_id=task.id)
        session.add(chat)
        await session.commit()

    # Call the function under test
    await delete_chat_by_id(chat_id=chat.id)

    # Verify that the chat has been deleted
    async with async_session() as session:
        fetched_chat = await session.get(Chat, chat.id)
        assert fetched_chat is None


# Test getting chats by user
@pytest.mark.asyncio
async def test_get_chats_by_user(async_session):
    """Test the get_chats_by_user function with ORM interactions."""
    # Create a user and multiple chats
    async with async_session() as session:
        user = User(email="testuser4@example.com")
        session.add(user)
        await session.commit()

        task = Task(
            id=1,
            user_id=1,
            description="Test Task 4",
            name="Test4",
            initial_system_prompt="Test Prompt",
        )
        session.add(task)
        await session.commit()

        # Create multiple chats
        chats = [Chat(user_id=user.id, task_id=task.id) for _ in range(5)]
        session.add_all(chats)
        await session.commit()

    # Call the function under test
    chats, chat_count = await get_chats_by_user(user_id=user.id, populate_task=True)

    # Assertions
    assert len(chats) == 5
    assert chat_count == 5


# Test adding a message to a chat
@pytest.mark.asyncio
async def test_add_message_to_chat(async_session):
    """Test the add_message_to_chat function with ORM interactions."""
    # Create a user, task, and chat
    async with async_session() as session:
        user = User(email="testuser5@example.com")
        session.add(user)
        await session.commit()

        task = Task(
            id=1,
            user_id=1,
            description="Test Task 5",
            name="Test5",
            initial_system_prompt="Test Prompt",
        )
        session.add(task)
        await session.commit()

        chat = Chat(user_id=user.id, task_id=task.id)
        session.add(chat)
        await session.commit()

    # Call the function under test
    message = await add_message_to_chat(
        chat_id=chat.id, content="Test message content", role=MessageRole.USER
    )

    # Assertions
    assert message.id is not None
    assert message.chat_id == chat.id
    assert message.content == "Test message content"
    assert message.role == MessageRole.USER

    # Verify that the message is stored in the database
    async with async_session() as session:
        fetched_message = await session.get(Message, message.id)
        assert fetched_message is not None
        assert fetched_message.content == "Test message content"


# Test adding reasoning steps to a message
@pytest.mark.asyncio
async def test_add_reasoning_steps_to_message(async_session):
    """Test the add_reasoning_steps_to_message function with ORM interactions."""
    # Create a user, task, chat, and message
    async with async_session() as session:
        user = User(email="testuser6@example.com")
        session.add(user)
        await session.commit()

        task = Task(
            id=1,
            user_id=1,
            description="Test Task 6",
            name="Test6",
            initial_system_prompt="Test Prompt",
        )
        session.add(task)
        await session.commit()

        chat = Chat(user_id=user.id, task_id=task.id)
        session.add(chat)
        await session.commit()

        message = Message(
            chat_id=chat.id, content="Message with reasoning", role=MessageRole.USER
        )
        session.add(message)
        await session.commit()

    # Define reasoning steps
    reasoning_steps = [
        ("Step 1", {"info": "First step info"}),
        ("Step 2", {"info": "Second step info"}),
    ]

    # Call the function under test
    steps = await add_reasoning_steps_to_message(
        message_id=message.id, reasonning_steps=reasoning_steps
    )

    # Assertions
    assert len(steps) == 2
    assert steps[0].name == "Step 1"
    assert json.loads(steps[0].content) == {"info": "First step info"}
    assert steps[1].name == "Step 2"
    assert json.loads(steps[1].content) == {"info": "Second step info"}

    # Verify that the reasoning steps are stored in the database
    async with async_session() as session:
        stmt = select(ReasoningStep).where(ReasoningStep.message_id == message.id)
        result = await session.scalars(stmt)
        stored_steps = result.all()
        assert len(stored_steps) == 2


# Test getting reasoning steps by message
@pytest.mark.asyncio
async def test_get_reasoning_steps_by_message(async_session):
    """Test the get_reasoning_steps_by_message function with ORM interactions."""
    # Create a user, task, chat, message, and reasoning steps
    async with async_session() as session:
        user = User(email="testuser7@example.com")
        session.add(user)
        await session.commit()

        task = Task(
            id=1,
            user_id=1,
            description="Test Task 7",
            name="Test7",
            initial_system_prompt="Test Prompt",
        )
        session.add(task)
        await session.commit()

        chat = Chat(user_id=user.id, task_id=task.id)
        session.add(chat)
        await session.commit()

        message = Message(
            chat_id=chat.id,
            content="Message for reasoning steps",
            role=MessageRole.USER,
        )
        session.add(message)
        await session.commit()

        # Add reasoning steps
        reasoning_steps = [
            ReasoningStep(
                message_id=message.id,
                name=f"Step {i}",
                content=json.dumps({"info": f"Step {i} info"}),
                created_at=datetime.utcnow(),
            )
            for i in range(5)
        ]
        session.add_all(reasoning_steps)
        await session.commit()

    # Call the function under test
    steps = await get_reasoning_steps_by_message(message_id=message.id)

    # Assertions
    assert len(steps) == 5
    for i, step in enumerate(steps):
        assert step.name == f"Step {i}"
        assert json.loads(step.content) == {"info": f"Step {i} info"}


# Test deleting chats by task ID
@pytest.mark.asyncio
async def test_delete_chats_by_task_id(async_session):
    """Test the delete_chats_by_task_id function with ORM interactions."""
    # Create a user, task, and chats
    async with async_session() as session:
        user = User(email="testuser8@example.com")
        session.add(user)
        await session.commit()

        task = Task(
            id=1,
            user_id=1,
            description="Test Task 8",
            name="Test8",
            initial_system_prompt="Test Prompt",
        )
        session.add(task)
        await session.commit()

        # Create multiple chats associated with the task
        chats = [Chat(user_id=user.id, task_id=task.id) for _ in range(3)]
        session.add_all(chats)
        await session.commit()

    # Call the function under test
    await delete_chats_by_task_id(task_id=task.id)

    # Verify that the chats have been deleted
    async with async_session() as session:
        stmt = select(Chat).where(Chat.task_id == task.id)
        result = await session.scalars(stmt)
        remaining_chats = result.all()
        assert len(remaining_chats) == 0


# # Helper function to create a user and a task
async def create_user_and_task(session, email, task_description):
    """Create a user and a task."""
    user = User(email=email)
    session.add(user)
    await session.commit()

    task = Task(
        user_id=user.id,
        description=task_description,
        name="Test Task",
        initial_system_prompt="Test Prompt",
    )
    session.add(task)
    await session.commit()
    return user, task


# Test add_reasoning_step_to_message
@pytest.mark.asyncio
async def test_add_reasoning_step_to_message(async_session):
    """Test the add_reasoning_step_to_message function."""
    # Create a user, task, chat, and message
    async with async_session() as session:
        user, task = await create_user_and_task(
            session, "testuser_add_reasoning_step@example.com", "Test Task"
        )
        chat = Chat(user_id=user.id, task_id=task.id)
        session.add(chat)
        await session.commit()

        message = Message(
            chat_id=chat.id, content="Message with reasoning", role=MessageRole.USER
        )
        session.add(message)
        await session.commit()

    # Define a reasoning step
    reasoning_step = ("Single Step", {"info": "Single step info"})

    # Call the function under test
    steps = await add_reasoning_step_to_message(
        message_id=message.id, reasoning_step=reasoning_step
    )

    # Assertions
    assert len(steps) == 1
    step = steps[0]
    assert step.name == "Single Step"
    assert json.loads(step.content) == {"info": "Single step info"}
    async with async_session() as session:
        # Verify that the reasoning step is stored in the database
        fetched_steps = await get_reasoning_steps_by_message(message_id=message.id)
        assert len(fetched_steps) == 1
        fetched_step = fetched_steps[0]
        assert fetched_step.name == "Single Step"
        assert json.loads(fetched_step.content) == {"info": "Single step info"}


# Test get_reasoning_steps_by_message when there are no reasoning steps
@pytest.mark.asyncio
async def test_get_reasoning_steps_by_message_no_steps(async_session):
    """Test the get_reasoning_steps_by_message function when there are no reasoning steps."""
    # Create a user, task, chat, and message
    async with async_session() as session:
        user, task = await create_user_and_task(
            session, "testuser_no_reasoning_steps@example.com", "Test Task"
        )
        chat = Chat(user_id=user.id, task_id=task.id)
        session.add(chat)
        await session.commit()

        message = Message(
            chat_id=chat.id,
            content="Message with no reasoning steps",
            role=MessageRole.USER,
        )
        session.add(message)
        await session.commit()

    # Call the function under test
    steps = await get_reasoning_steps_by_message(message_id=message.id)

    # Assertions
    assert len(steps) == 0


# Test get_reasoning_steps_by_message with invalid message_id
@pytest.mark.asyncio
async def test_get_reasoning_steps_by_message_invalid_message_id():
    """Test getting reasoning steps for a non-existent message."""
    message_id = 9999  # Assuming this ID does not exist

    # Call the function under test
    steps = await get_reasoning_steps_by_message(message_id=message_id)

    # Assertions
    assert len(steps) == 0


# Test deleting chats by task ID when there are no chats
@pytest.mark.asyncio
async def test_delete_chats_by_task_id_no_chats(async_session):
    """Test deleting chats by task ID when there are no chats associated with the task."""
    # Create a user and task
    async with async_session() as session:
        user, task = await create_user_and_task(
            session, "testuser_no_chats_for_task@example.com", "Test Task"
        )

    # Call the function under test
    await delete_chats_by_task_id(task_id=task.id)

    # Verify that there are no chats associated with the task
    chats, count = await get_chats_by_user(user_id=user.id)
    assert len(chats) == 0
    assert count == 0
