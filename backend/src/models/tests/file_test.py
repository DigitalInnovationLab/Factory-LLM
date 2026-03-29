import pytest

from backend.src.models import Chat, File
from backend.src.models.tests.init_db import init_db


def test_file_creation():
    """Test creating a File instance."""
    session = init_db()

    chat = Chat(id=1, user_id=1, task_id=1)
    session.add(chat)
    session.commit()

    file = File(chat_id=chat.id, name="test_file.txt")
    session.add(file)
    session.commit()

    assert file.id is not None
    assert file.chat_id == chat.id
    assert file.name == "test_file.txt"


def test_file_relationship():
    """Test the relationship between File and Chat."""
    session = init_db()

    chat = Chat(id=1, user_id=1, task_id=1)
    file = File(name="test_file.txt")
    chat.files.append(file)
    session.add(chat)
    session.commit()

    # Test relationships
    assert file.chat == chat
    assert chat.files[0] == file


def test_file_null_name():
    """Test that the name field cannot be null."""
    session = init_db()

    chat = Chat(id=1, user_id=1, task_id=1)
    session.add(chat)
    session.commit()

    file = File(chat_id=chat.id, name=None)
    session.add(file)

    with pytest.raises(Exception) as excinfo:
        session.commit()
    session.rollback()

    assert "NOT NULL constraint failed" in str(excinfo.value)


def test_file_repr():
    """Test the __repr__ method of File."""
    file = File(id=1, chat_id=2, name="test_file.txt")
    expected_repr = "<File(id=1, chat_id=2, name=''test_file.txt'')>"
    assert repr(file) == expected_repr
