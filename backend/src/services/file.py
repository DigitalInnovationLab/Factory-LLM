from typing import List, Optional

from sqlalchemy import delete
from sqlalchemy.future import select

from backend.src.models import File, Session


async def create_files(chat_id: int, files: List[str]) -> List[File]:
    """
    Create new files with the given names and chat_id
    """
    async with Session() as session:
        files = [File(chat_id=chat_id, name=name) for name in files]
        session.add_all(files)
        await session.commit()
        return files


async def get_files_by_names(names: List[str]) -> List[File]:
    """
    Get files by names
    """
    async with Session() as session:
        stmt = select(File).where(File.name.in_(names))
        return (await session.scalars(stmt)).all()


async def create_file(chat_id: int, name: str) -> File:
    """
    Create a new file with the given name and chat_id
    """
    files = await create_files(chat_id, [name])
    return files[0]


async def get_file_by_name(name: str) -> Optional[File]:
    """
    Get a file by name
    """
    files = await get_files_by_names([name])
    return files[0] if files[0] else None


async def get_files_by_chat(chat_id: int, page=0, limit=10) -> List[File]:
    """
    Get files within a chat sorted by name
    """
    async with Session() as session:
        stmt = (
            select(File)
            .where(File.chat_id == chat_id)
            .order_by(File.name)
            .offset(page * limit)
            .limit(limit)
        )
        return (await session.scalars(stmt)).all()


async def delete_file_by_id(file_id: int):
    """
    Delete a file by id
    """
    async with Session.begin() as session:
        stmt = delete(File).where(File.id == file_id)
        await session.execute(stmt)
