import pytest
from sqlalchemy.exc import IntegrityError

from backend.src.models import Chat, Feedback, Message, MessageRole, Task
from backend.src.models.tests.init_db import init_db


def test_message_creation():
    """Test creating a Message instance."""
    session = init_db()

    task = Task(
        description="Test Task",
        user_id=1,
        id=1,
        name="Test",
        initial_system_prompt="Test Prompt",
    )
    chat = Chat(user_id=1, task_id=task.id, id=1)
    session.add(chat)
    session.commit()

    message = Message(chat_id=chat.id, role=MessageRole.USER, content="Hello, world!")
    session.add(message)
    session.commit()

    assert message.id is not None
    assert message.chat_id == chat.id
    assert message.role == MessageRole.USER
    assert message.content == "Hello, world!"


def test_message_relationships():
    """Test the relationships between Message, Chat, and Feedback."""
    session = init_db()

    task = Task(
        description="Test Task",
        user_id=1,
        id=1,
        name="Test",
        initial_system_prompt="Test Prompt",
    )
    chat = Chat(user_id=1, task_id=task.id, id=1)
    session.add(chat)
    session.commit()

    message = Message(
        chat=chat, role=MessageRole.ASSISTANT, content="How can I assist you today?"
    )
    feedback = Feedback(
        message=message, user_id=1, text_feedback="Very helpful!", rating=5
    )

    session.add(message)
    session.add(feedback)
    session.commit()

    # Test relationships
    assert message.chat == chat
    assert chat.messages[0] == message
    assert message.feedback == feedback
    assert feedback.message == message


def test_message_null_role():
    """Test that the role field cannot be null."""
    session = init_db()

    task = Task(
        description="Test Task",
        user_id=1,
        id=1,
        name="Test",
        initial_system_prompt="Test Prompt",
    )
    chat = Chat(user_id=1, task_id=task.id, id=1)
    session.add(chat)
    session.commit()

    message = Message(chat_id=chat.id, role=None, content="This message has no role.")
    session.add(message)
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


def test_message_null_content():
    """Test that the content field cannot be null."""
    session = init_db()

    task = Task(
        description="Test Task",
        user_id=1,
        id=1,
        name="Test",
        initial_system_prompt="Test Prompt",
    )
    chat = Chat(user_id=1, task_id=task.id, id=1)
    session.add(chat)
    session.commit()

    message = Message(chat_id=chat.id, role=MessageRole.USER, content=None)
    session.add(message)
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


def test_message_invalid_role():
    """Test that assigning an invalid role raises an error."""
    session = init_db()

    task = Task(
        description="Test Task",
        user_id=1,
        id=1,
        name="Test",
        initial_system_prompt="Test Prompt",
    )
    chat = Chat(user_id=1, task_id=task.id, id=1)
    session.add(chat)
    session.commit()

    message = Message(chat_id=chat.id, role="INVALID_ROLE", content="This should fail.")
    session.add(message)
    session.commit()

    # The commit wont raise an error, but
    # the exception will be raised when we try to retrieve the object
    with pytest.raises(LookupError):
        print(message)


def test_message_repr():
    """Test the __repr__ method of Message."""
    message = Message(
        id=1, chat_id=2, role=MessageRole.USER, content="This is a test message."
    )
    expected_repr = (
        f"<Message(id=1, chat_id=2, role={MessageRole.USER!r}, "
        f"content='{'This is a test messa'!r}')>"
    )
    assert repr(message) == expected_repr
