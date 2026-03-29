import pytest
from sqlalchemy.exc import IntegrityError

from backend.src.constants import LlmModel, Technique
from backend.src.models import Chat, Task, User
from backend.src.models.tests.init_db import init_db


def test_task_creation():
    """Test creating a Task instance."""
    session = init_db()

    user = User(email="test@example.com")

    session.add(user)
    session.commit()

    task = Task(
        user_id=user.id,
        name="Test Task",
        description="This is a test task.",
        initial_system_prompt="You are a helpful assistant.",
    )
    session.add(task)
    session.commit()

    assert task.id is not None
    assert task.user_id == user.id
    assert task.name == "Test Task"
    assert task.description == "This is a test task."
    assert task.initial_system_prompt == "You are a helpful assistant."
    assert task.llm_model == LlmModel.GPT4O
    assert task.prompting_technique == Technique.NONE


def test_task_null_fields():
    """Test that name, description, and initial_system_prompt cannot be null."""
    session = init_db()
    user = User(email="test@example.com")
    session.add(user)
    session.commit()

    # Test name cannot be null
    task = Task(
        user_id=user.id,
        name=None,
        description="This is a test task.",
        initial_system_prompt="You are a helpful assistant.",
    )
    session.add(task)
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()

    # Test description cannot be null
    task = Task(
        user_id=user.id,
        name="Test Task",
        description=None,
        initial_system_prompt="You are a helpful assistant.",
    )
    session.add(task)
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()

    # Test initial_system_prompt cannot be null
    task = Task(
        user_id=user.id,
        name="Test Task",
        description="This is a test task.",
        initial_system_prompt=None,
    )
    session.add(task)
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


def test_task_relationship():
    """Test the relationship between Task and User."""
    session = init_db()
    user = User(email="test@example.com")
    chat = Chat(user_id=1, task_id=1, id=1)
    session.add(user)
    session.add(chat)
    session.commit()

    task = Task(
        user_id=user.id,
        id=1,
        name="Test Task",
        description="This is a test task.",
        initial_system_prompt="You are a helpful assistant.",
    )
    session.add(task)
    session.commit()

    assert task.user_id == user.id
    assert chat.task_id == task.id


def test_task_enum_fields():
    """Test that llm_model and prompting_technique accept only valid enum values."""
    session = init_db()
    user = User(email="test@example.com")
    session.add(user)
    session.commit()

    # Valid values
    task = Task(
        user_id=user.id,
        name="Test Task",
        description="This is a test task.",
        initial_system_prompt="You are a helpful assistant.",
        llm_model=LlmModel.GPT35,
        prompting_technique=Technique.COT,
    )
    session.add(task)
    session.commit()

    assert task.llm_model == LlmModel.GPT35
    assert task.prompting_technique == Technique.COT

    # Invalid llm_model
    task = Task(
        user_id=user.id,
        name="Test Task",
        description="This is a test task.",
        initial_system_prompt="You are a helpful assistant.",
        llm_model="INVALID_MODEL",
    )
    session.add(task)
    session.commit()
    with pytest.raises(LookupError):
        print(task)

    # Invalid prompting_technique
    task = Task(
        user_id=user.id,
        name="Test Task",
        description="This is a test task.",
        initial_system_prompt="You are a helpful assistant.",
        prompting_technique="INVALID_TECHNIQUE",
    )
    session.add(task)
    session.commit()
    with pytest.raises(LookupError):
        print(task)


def test_task_repr():
    """Test the __repr__ method of Task."""
    task = Task(
        id=1,
        name="Test Task",
    )
    expected_repr = "<Task(id=1, name=''Test Task'')>"
    assert repr(task) == expected_repr
