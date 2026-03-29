# pylint: disable=redefined-outer-name, import-outside-toplevel, R0801
from datetime import datetime

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from backend.src.models import Base, Feedback, Message, MessageRole, User
from backend.src.services.feedback import (
    create_feedback,
    get_feedback_by_id,
    get_feedbacks_by_user,
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
    """Patch the Session in backend.src.models and services to use the async_session fixture."""
    from backend.src import models
    from backend.src.services import feedback

    monkeypatch.setattr(models, "Session", async_session)
    monkeypatch.setattr(feedback, "Session", async_session)


# Test creating a new feedback entry
@pytest.mark.asyncio
async def test_create_feedback(async_session):
    """Test the create_feedback function with ORM interactions."""
    # Create a user and message
    async with async_session() as session:
        # Create a user
        user = User(email="testuser@example.com")
        session.add(user)
        await session.commit()

        # Create a message
        message = Message(
            content="Test message", id=1, chat_id=1, role=MessageRole.USER
        )
        session.add(message)
        await session.commit()

    # Call the function under test
    feedback = await create_feedback(
        message_id=message.id, user_id=user.id, text_feedback="Great job!", rating=5
    )

    # Assertions
    assert feedback.id is not None
    assert feedback.text_feedback == "Great job!"
    assert feedback.rating == 5

    # Verify that the feedback is actually stored in the database
    async with async_session() as session:
        fetched_feedback = await session.get(Feedback, feedback.id)
        assert fetched_feedback is not None
        assert fetched_feedback.text_feedback == "Great job!"
        assert fetched_feedback.rating == 5


# # Test retrieving feedback by ID
@pytest.mark.asyncio
async def test_get_feedback_by_id(async_session):
    """Test the get_feedback_by_id function with ORM interactions."""
    async with async_session() as session:
        # Create a user
        user = User(email="testuser2@example.com")
        session.add(user)
        await session.commit()

        # Create a message
        message = Message(
            content="Another test message", id=1, chat_id=1, role=MessageRole.USER
        )
        session.add(message)
        await session.commit()

        # Create a feedback entry
        feedback = Feedback(
            message_id=message.id,
            user_id=user.id,
            text_feedback="Needs improvement",
            rating=3,
            created_at=datetime.utcnow(),
        )
        session.add(feedback)
        await session.commit()

    # Call the function under test
    fetched_feedback = await get_feedback_by_id(feedback_id=feedback.id)

    # Assertions
    assert fetched_feedback is not None
    assert fetched_feedback.id == feedback.id
    assert fetched_feedback.text_feedback == "Needs improvement"
    assert fetched_feedback.rating == 3


# # Test retrieving feedbacks by user
@pytest.mark.asyncio
async def test_get_feedbacks_by_user(async_session):
    """Test the get_feedbacks_by_user function with ORM interactions."""
    async with async_session() as session:
        # Create a user
        user = User(email="testuser3@example.com")
        session.add(user)
        await session.commit()

        # Create a message
        message = Message(
            content="Message for feedbacks", id=1, chat_id=1, role=MessageRole.USER
        )
        session.add(message)
        await session.commit()

        # Create multiple feedback entries
        for i in range(5):
            feedback = Feedback(
                message_id=message.id,
                user_id=user.id,
                text_feedback=f"Feedback {i}",
                rating=5 - i,
                created_at=datetime.utcnow(),
            )
            session.add(feedback)
        await session.commit()

    # Call the function under test
    feedbacks = await get_feedbacks_by_user(user_id=user.id)

    # Assertions
    assert len(feedbacks) == 5

    # Verify that feedbacks are ordered by created_at descending
    created_at_list = [feedback.created_at for feedback in feedbacks]
    assert created_at_list == sorted(created_at_list, reverse=True)


# Test pagination in retrieving feedbacks
@pytest.mark.asyncio
async def test_get_feedbacks_by_user_pagination(async_session):
    """Test pagination in get_feedbacks_by_user function with ORM interactions."""
    async with async_session() as session:
        # Create a user
        user = User(email="testuser4@example.com")
        session.add(user)
        await session.commit()

        # Create a message
        message = Message(
            content="Pagination test message", id=1, chat_id=1, role=MessageRole.USER
        )
        session.add(message)
        await session.commit()

        # Create multiple feedback entries
        for i in range(10):
            feedback = Feedback(
                message_id=message.id,
                user_id=user.id,
                text_feedback=f"Feedback {i}",
                rating=5 - (i % 5),
                created_at=datetime.utcnow(),
            )
            session.add(feedback)
        await session.commit()

    # Retrieve the first page
    feedbacks_page1 = await get_feedbacks_by_user(user_id=user.id, page=0, limit=3)

    # Retrieve the second page
    feedbacks_page2 = await get_feedbacks_by_user(user_id=user.id, page=1, limit=3)

    # Assertions for page 1
    assert len(feedbacks_page1) == 3

    # Assertions for page 2
    assert len(feedbacks_page2) == 3

    # Ensure that the feedback entries are different
    ids_page1 = {feedback.id for feedback in feedbacks_page1}
    ids_page2 = {feedback.id for feedback in feedbacks_page2}
    assert ids_page1.isdisjoint(ids_page2)

    # Optional: Verify the order across pages
    all_feedbacks = feedbacks_page1 + feedbacks_page2
    created_at_list = [feedback.created_at for feedback in all_feedbacks]
    assert created_at_list == sorted(created_at_list, reverse=True)
