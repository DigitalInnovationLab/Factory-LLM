# pylint: disable=redefined-outer-name, import-outside-toplevel, R0801
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from backend.src.models import Base, Chat, File
from backend.src.services.file import (
    create_file,
    create_files,
    delete_file_by_id,
    get_file_by_name,
    get_files_by_chat,
    get_files_by_names,
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
    Patch the Session in backend.src.models and services to use the async_session fixture.
    """
    from backend.src import models
    from backend.src.services import file

    monkeypatch.setattr(models, "Session", async_session)
    monkeypatch.setattr(file, "Session", async_session)


# Test creating multiple files
@pytest.mark.asyncio
async def test_create_files(async_session):
    """Test the create_files function."""
    # Create a chat
    async with async_session() as session:
        chat = Chat(user_id=1, task_id=1)
        session.add(chat)
        await session.commit()

    # Create files associated with the chat
    file_names = ["file1.txt", "file2.txt", "file3.txt"]
    files = await create_files(chat_id=chat.id, files=file_names)

    # Assertions
    assert len(files) == 3
    for file_obj, name in zip(files, file_names):
        assert file_obj.name == name
        assert file_obj.chat_id == chat.id

    # Verify that the files are stored in the database
    async with async_session() as session:
        stmt = select(File).where(File.chat_id == chat.id)
        result = await session.scalars(stmt)
        stored_files = result.all()
        assert len(stored_files) == 3
        stored_file_names = [f.name for f in stored_files]
        assert set(stored_file_names) == set(file_names)


# Test getting files by names
@pytest.mark.asyncio
async def test_get_files_by_names(async_session):
    """Test the get_files_by_names function."""
    # Create a chat and files
    async with async_session() as session:
        chat = Chat(user_id=1, task_id=1)
        session.add(chat)
        await session.commit()

        file_names = ["file1.txt", "file2.txt", "file3.txt"]
        files = [File(chat_id=chat.id, name=name) for name in file_names]
        session.add_all(files)
        await session.commit()

    # Test get_files_by_names
    retrieved_files = await get_files_by_names(names=["file1.txt", "file3.txt"])

    # Assertions
    assert len(retrieved_files) == 2
    retrieved_file_names = [file.name for file in retrieved_files]
    assert set(retrieved_file_names) == {"file1.txt", "file3.txt"}


# Test creating a single file
@pytest.mark.asyncio
async def test_create_file(async_session):
    """Test the create_file function."""
    # Create a chat
    async with async_session() as session:
        chat = Chat(user_id=1, task_id=1)
        session.add(chat)
        await session.commit()

    # Create a single file
    file_name = "single_file.txt"
    file_obj = await create_file(chat_id=chat.id, name=file_name)

    # Assertions
    assert file_obj.name == file_name
    assert file_obj.chat_id == chat.id

    # Verify that the file is stored in the database
    async with async_session() as session:
        stored_file = await session.get(File, file_obj.id)
        assert stored_file is not None
        assert stored_file.name == file_name


# Test getting a file by name
@pytest.mark.asyncio
async def test_get_file_by_name(async_session):
    """Test the get_file_by_name function."""
    # Create a chat and a file
    async with async_session() as session:
        chat = Chat(user_id=1, task_id=1)
        session.add(chat)
        await session.commit()

        file_name = "test_file.txt"
        file_obj = File(chat_id=chat.id, name=file_name)
        session.add(file_obj)
        await session.commit()

    # Retrieve the file by name
    retrieved_file = await get_file_by_name(name=file_name)

    # Assertions
    assert retrieved_file is not None
    assert retrieved_file.name == file_name
    assert retrieved_file.chat_id == chat.id


# Test getting files by chat with pagination
@pytest.mark.asyncio
async def test_get_files_by_chat(async_session):
    """Test the get_files_by_chat function."""
    # Create a chat and files
    async with async_session() as session:
        chat = Chat(user_id=1, task_id=1)
        session.add(chat)
        await session.commit()

        file_names = ["file1.txt", "file2.txt", "file3.txt", "file4.txt", "file5.txt"]
        files = [File(chat_id=chat.id, name=name) for name in file_names]
        session.add_all(files)
        await session.commit()

    # Retrieve files by chat_id with pagination
    files_page1 = await get_files_by_chat(chat_id=chat.id, page=0, limit=2)
    files_page2 = await get_files_by_chat(chat_id=chat.id, page=1, limit=2)

    # Assertions
    assert len(files_page1) == 2
    assert len(files_page2) == 2

    # Verify that files are ordered by name
    all_files = files_page1 + files_page2
    file_names_retrieved = [file.name for file in all_files]
    assert file_names_retrieved == sorted(file_names_retrieved)


# Test deleting a file by ID
@pytest.mark.asyncio
async def test_delete_file_by_id(async_session):
    """Test the delete_file_by_id function."""
    # Create a chat and a file
    async with async_session() as session:
        chat = Chat(user_id=1, task_id=1)
        session.add(chat)
        await session.commit()

        file_obj = File(chat_id=chat.id, name="file_to_delete.txt")
        session.add(file_obj)
        await session.commit()
        file_id = file_obj.id

    # Delete the file
    await delete_file_by_id(file_id=file_id)

    # Verify that the file has been deleted
    async with async_session() as session:
        deleted_file = await session.get(File, file_id)
        assert deleted_file is None
