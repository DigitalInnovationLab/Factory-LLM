import pytest
from sqlalchemy.exc import IntegrityError

from backend.src.models import Chat, Feedback, User
from backend.src.models.tests.init_db import init_db


def test_user_creation():
    """Test creating a User instance."""
    session = init_db()
    user = User(email="test@example.com")
    session.add(user)
    session.commit()

    assert user.id is not None
    assert user.email == "test@example.com"


def test_user_email_uniqueness():
    """Test that the email field must be unique."""
    session = init_db()
    user1 = User(email="unique@example.com")
    user2 = User(email="unique@example.com")

    session.add(user1)
    session.commit()

    session.add(user2)
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


def test_user_null_email():
    """Test that the email field cannot be null."""
    session = init_db()
    user = User(email=None)
    session.add(user)
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


def test_user_relationships():
    """Test the relationships between User, Chat, and Feedback."""
    session = init_db()

    user = User(email="user@example.com")
    chat2 = Chat(user_id=user.id, task_id=1)
    chat1 = Chat(user_id=user.id, task_id=2)
    feedback1 = Feedback(text_feedback="Great service!", rating=5, message_id=1)
    feedback2 = Feedback(text_feedback="Needs improvement.", rating=2, message_id=2)

    user.chats.extend([chat1, chat2])
    user.feedbacks.extend([feedback1, feedback2])

    session.add(user)
    session.commit()

    # Test relationships
    assert len(user.chats) == 2
    assert len(user.feedbacks) == 2
    assert chat1.user_id == user.id
    assert chat2.user_id == user.id
    assert feedback1.user_id == user.id
    assert feedback2.user_id == user.id


def test_user_repr():
    """Test the __repr__ method of User."""
    user = User(id=1, email="test@example.com")
    expected_repr = "<User(id=1, email=''test@example.com'')>"
    assert repr(user) == expected_repr
