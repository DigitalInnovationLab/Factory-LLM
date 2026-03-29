from typing import Optional

from sqlalchemy import delete
from sqlalchemy.future import select

from backend.src.models import Session, User


async def create_user(email: str) -> User:
    """
    Create a new user with the given email
    """
    async with Session() as session:
        user = User(email=email)
        session.add(user)
        await session.commit()
        return user


async def get_user_by_email(email: str) -> Optional[User]:
    """
    Get a user by email
    """
    async with Session() as session:
        stmt = select(User).where(User.email == email)
        return await session.scalar(stmt)


async def get_user_by_id(user_id: int) -> Optional[User]:
    """
    Get a user by id
    """
    async with Session() as session:
        return await session.get(User, user_id)


async def delete_user_by_id(user_id: int) -> None:
    """
    Delete a user by id
    """
    async with Session() as session:
        stmt = delete(User).where(User.id == user_id)
        await session.execute(stmt)
        await session.commit()
