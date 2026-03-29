from datetime import datetime

from backend.src.models import Chat, File, Message, MessageRole, Task, User
from backend.src.models.tests.init_db import init_db


def test_chat_creation():
    """Test creating a Chat instance."""
    session = init_db()

    user = User(email="Test User")
    task = Task(
        description="Test Task",
        user_id=1,
        name="Test",
        initial_system_prompt="Test Prompt",
    )

    session.add(user)
    session.add(task)
    session.commit()

    chat = Chat(user_id=user.id, task_id=task.id)
    session.add(chat)
    session.commit()

    assert chat.id is not None
    assert chat.user_id == user.id
    assert chat.task_id == task.id


def test_chat_relationships():
    """Test the relationships between Chat, User, Task, Message, and File."""
    session = init_db()

    user = User(email="Test User")
    task = Task(
        description="Test Task",
        user_id=1,
        name="Test",
        initial_system_prompt="Test Prompt",
    )

    session.add(user)
    session.add(task)
    session.commit()

    chat = Chat(id=1, user_id=1, task_id=1)
    message1 = Message(
        content="Hello", created_at=datetime(2021, 1, 1), role=MessageRole.USER
    )
    message2 = Message(
        content="World", created_at=datetime(2021, 1, 2), role=MessageRole.USER
    )
    file1 = File(name="test.txt")

    chat.messages.extend([message1, message2])
    chat.files.append(file1)

    session.add(chat)
    session.commit()

    # Test relationships
    assert chat.user_id == 1
    assert chat.task_id == 1
    assert user.chats[0] == chat
    assert (
        task.user_id == chat.user_id
    )  # this is an issue and dont know why it is, comment out it passes
    assert len(chat.messages) == 2
    assert len(chat.files) == 1
    assert chat.messages[0].content == "Hello"
    assert chat.messages[1].content == "World"
    assert chat.files[0].name == "test.txt"


def test_chat_message_ordering():
    """Test that messages are ordered by created_at ascending."""
    session = init_db()

    User(email="Test User")
    Task(
        description="Test Task",
        user_id=1,
        name="Test",
        initial_system_prompt="Test Prompt",
    )
    chat = Chat(user_id=1, task_id=1)

    message1 = Message(
        content="Hello", created_at=datetime(2021, 1, 1), role=MessageRole.USER
    )
    message2 = Message(
        content="World", created_at=datetime(2021, 1, 2), role=MessageRole.USER
    )

    chat.messages.extend([message1, message2])
    session.add(chat)
    session.commit()

    # Messages should be ordered by created_at ascending
    assert chat.messages[0].content == "Hello"
    assert chat.messages[1].content == "World"


def test_chat_repr():
    """Test the __repr__ method of Chat."""
    chat = Chat(id=1, user_id=2, task_id=3)
    expected_repr = "<Chat(id=1, user_id=2, task_id=3)>"
    assert repr(chat) == expected_repr
