# pylint: disable=redefined-outer-name, import-outside-toplevel, R0801
import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from backend.src.models import Base
from backend.src.services.user import (
    create_user,
    delete_user_by_id,
    get_user_by_email,
    get_user_by_id,
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


# Monkeypatch the Session in backend.src.models to use the async_session fixture
@pytest.fixture(autouse=True)
def patch_session(async_session, monkeypatch):
    """Patch the Session in backend.src.models to use the async_session fixture."""
    from backend.src import models
    from backend.src.services import user

    monkeypatch.setattr(models, "Session", async_session)
    monkeypatch.setattr(user, "Session", async_session)


# Test creating a new user
@pytest.mark.asyncio
async def test_create_user():
    """Test the create_user function."""
    email = "test@example.com"

    # Call the function under test
    user = await create_user(email=email)

    # Assertions
    assert user.id is not None
    assert user.email == email

    # Verify that the user is actually stored in the database
    fetched_user = await get_user_by_id(user.id)
    assert fetched_user is not None
    assert fetched_user.email == email


# Test retrieving a user by email
@pytest.mark.asyncio
async def test_get_user_by_email():
    """Test the get_user_by_email function."""
    email = "user_by_email@example.com"

    # Create a user to retrieve
    user = await create_user(email=email)

    # Call the function under test
    fetched_user = await get_user_by_email(email)

    # Assertions
    assert fetched_user is not None
    assert fetched_user.id == user.id
    assert fetched_user.email == email


# Test retrieving a user by ID
@pytest.mark.asyncio
async def test_get_user_by_id():
    """Test the get_user_by_id function."""
    email = "user_by_id@example.com"

    # Create a user to retrieve
    user = await create_user(email=email)

    # Call the function under test
    fetched_user = await get_user_by_id(user.id)

    # Assertions
    assert fetched_user is not None
    assert fetched_user.id == user.id
    assert fetched_user.email == email


# Test retrieving a non-existent user by email
@pytest.mark.asyncio
async def test_get_user_by_email_not_found():
    """Test get_user_by_email with an email that doesn't exist."""
    email = "nonexistent@example.com"

    # Call the function under test
    fetched_user = await get_user_by_email(email)

    # Assertions
    assert fetched_user is None


# Test retrieving a non-existent user by ID
@pytest.mark.asyncio
async def test_get_user_by_id_not_found():
    """Test get_user_by_id with an ID that doesn't exist."""
    user_id = 9999  # Assuming this ID doesn't exist

    # Call the function under test
    fetched_user = await get_user_by_id(user_id)

    # Assertions
    assert fetched_user is None


# Test creating a user with a duplicate email
@pytest.mark.asyncio
async def test_create_user_duplicate_email():
    """Test that creating a user with a duplicate email raises an exception."""
    email = "duplicate@example.com"

    # Create the first user
    await create_user(email=email)

    # Attempt to create a second user with the same email
    with pytest.raises(IntegrityError) as exc_info:
        await create_user(email=email)

    # Check that the exception is due to the unique constraint
    assert "UNIQUE constraint failed" in str(exc_info.value) or "IntegrityError" in str(
        exc_info.value
    )


# Test deleting a user by ID
@pytest.mark.asyncio
async def test_delete_user_by_id():
    """Test that a user can be deleted by ID."""
    email = "user_to_delete@example.com"

    # Create a user to delete
    user = await create_user(email=email)

    # Verify that the user exists
    fetched_user = await get_user_by_id(user.id)
    assert fetched_user is not None

    # Delete the user
    await delete_user_by_id(user.id)

    # Verify that the user no longer exists
    fetched_user = await get_user_by_id(user.id)
    assert fetched_user is None


# Test deleting a non-existent user by ID
@pytest.mark.asyncio
async def test_delete_user_by_id_not_found():
    """Test that deleting a non-existent user does not raise an exception."""
    user_id = 9999  # Assuming this ID doesn't exist

    # Attempt to delete the user
    await delete_user_by_id(user_id)

    # No exception should be raised


# Test creating a user with invalid email (None)
@pytest.mark.asyncio
async def test_create_user_invalid_email():
    """Test that creating a user with invalid email raises an exception."""
    email = None

    with pytest.raises(IntegrityError) as exc_info:
        await create_user(email=email)

    # Check that the exception is due to the NOT NULL constraint
    assert "NOT NULL constraint failed" in str(
        exc_info.value
    ) or "IntegrityError" in str(exc_info.value)
