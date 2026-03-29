import pytest
from sqlalchemy.exc import IntegrityError

from backend.src.models.tests.init_db import init_db

from ...models import Feedback, Message, MessageRole, User


def test_feedback_creation():
    """Test creating a Feedback instance."""
    session = init_db()
    user = User(email="Test User")
    message = Message(content="Test Message", chat_id=1, role=MessageRole.USER)
    # check the enum for the role from whatever

    session.add(user)
    session.add(message)
    session.commit()

    feedback = Feedback(
        message_id=message.id, user_id=user.id, text_feedback="Great job!", rating=5
    )

    session.add(feedback)
    session.commit()

    assert feedback.id is not None
    assert feedback.text_feedback == "Great job!"
    assert feedback.rating == 5


def test_feedback_relationships():
    """Test the relationships between Feedback, User, and Message."""
    session = init_db()
    user = User(email="Test User")
    message = Message(content="Test Message", chat_id=1, role=MessageRole.USER)

    session.add(user)
    session.add(message)
    session.commit()

    feedback = Feedback(
        message_id=message.id,
        user_id=user.id,
        text_feedback="Needs improvement.",
        rating=2,
    )

    session.add(feedback)
    session.commit()

    # Test relationships
    assert feedback.user == user
    assert feedback.message == message
    assert user.feedbacks[0] == feedback
    assert message.feedback == feedback


def test_feedback_null_text():
    """Test that text_feedback cannot be null."""
    session = init_db()
    user = User(email="Test User")
    message = Message(content="Test Message", chat_id=1, role=MessageRole.USER)

    session.add(user)
    session.add(message)
    session.commit()

    feedback = Feedback(message_id=1, user_id=user.id, text_feedback=None, rating=4)

    session.add(feedback)
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


def test_feedback_null_rating():
    """Test that rating cannot be null."""
    session = init_db()
    user = User(email="Test User")
    message = Message(content="Test Message", chat_id=1, role=MessageRole.USER)

    session.add(user)
    session.add(message)
    session.commit()

    feedback = Feedback(
        message_id=message.id, user_id=user.id, text_feedback="Average", rating=None
    )

    session.add(feedback)
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


# def test_feedback_cascade_delete():
#     """Test that deleting a Message cascades to delete associated Feedback."""
#     session = init_db()
#     user = User(email="Test User")
#     message = Message(content="Test Message", chat_id=1, role=MessageRole.USER)

#     session.add(user)
#     session.add(message)
#     session.commit()

#     feedback = Feedback(
#         message_id=1,
#         user_id=user.id,
#         text_feedback="Good",
#         rating=4
#     )

#     session.add(feedback)
#     session.commit()

#     session.delete(message)
#     session.commit()

#     deleted_feedback = session.query(Feedback).filter_by(id=feedback.id).first()
#     assert deleted_feedback is None


def test_feedback_repr():
    """Test the __repr__ method of Feedback."""
    feedback = Feedback(
        id=1, message_id=2, user_id=3, text_feedback="Excellent!", rating=5
    )

    expected_repr = "<Feedback(id=1, message_id=2, user_id=3, rating=5>"
    assert repr(feedback) == expected_repr
