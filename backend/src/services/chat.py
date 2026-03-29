import json
from typing import List, Optional

from sqlalchemy import delete, func
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

from backend.src.constants import RagTechnique

from ..models import Chat, Message, MessageRole, ReasoningStep, Session


async def create_chat(
    user_id: int,
    task_id: int,
    rag_technique: RagTechnique = RagTechnique.VECTOR,
    vector_top_k: int = 3,
) -> Chat:
    """
    Create a new chat with the given name
    """
    async with Session() as session:
        chat = Chat(
            user_id=user_id,
            task_id=task_id,
            rag_technique=rag_technique,
            vector_top_k=vector_top_k,
        )
        session.add(chat)
        await session.commit()
        return chat


async def get_chat_by_id(chat_id: int) -> Optional[Chat]:
    """
    Get a chat by id with messages included
    """
    async with Session() as session:
        return await session.get(Chat, chat_id, options=[joinedload(Chat.messages)])


async def delete_chat_by_id(chat_id: int) -> None:
    """
    Delete a chat by id
    """
    async with Session() as session:
        chat = await session.get(Chat, chat_id)
        if chat:
            await session.delete(chat)
            await session.commit()


async def get_chats_by_user(
    user_id: int, page=0, limit=10, populate_task=False
) -> tuple[List[Chat], int]:
    """
    Get chats by user
    """
    async with Session() as session:
        count = (
            await session.execute(
                # pylint: disable-next=not-callable # false positive
                select(func.count())
                .select_from(Chat)
                .where(Chat.user_id == user_id)
            )
        ).scalar()
        stmt = (
            select(Chat)
            .where(Chat.user_id == user_id)
            .offset(page * limit)
            .limit(limit)
            .order_by(Chat.updated_at.desc())
        )
        if populate_task:
            stmt = stmt.options(joinedload(Chat.task))
        chats = (await session.scalars(stmt)).unique().all()
        return chats, count


async def add_message_to_chat(
    chat_id: int,
    content: str,
    role: MessageRole = MessageRole.USER,
) -> Message:
    """
    Add a message to a chat
    """
    async with Session.begin() as session:
        message = Message(chat_id=chat_id, content=content, role=role)
        session.add(message)
        await session.commit()
        return message


async def add_reasoning_steps_to_message(
    message_id: int, reasonning_steps: list[tuple[str, dict]]
) -> list[ReasoningStep]:
    """
    Add reasoning steps to a message
    """
    async with Session() as session:
        reasoning_steps = [
            ReasoningStep(message_id=message_id, name=name, content=json.dumps(content))
            for name, content in reasonning_steps
        ]
        session.add_all(reasoning_steps)
        await session.commit()

        return reasoning_steps


async def add_reasoning_step_to_message(
    message_id: int, reasoning_step: tuple[str, dict]
) -> ReasoningStep:
    """
    Add a reasoning step to a message
    """
    return await add_reasoning_steps_to_message(message_id, [reasoning_step])


async def get_reasoning_steps_by_message(
    message_id: int, page=0, limit=10
) -> Optional[List[ReasoningStep]]:
    """
    Get reasoning steps by message
    """
    async with Session() as session:
        stmt = (
            select(ReasoningStep)
            .where(ReasoningStep.message_id == message_id)
            .offset(page * limit)
            .limit(limit)
            .order_by(ReasoningStep.created_at.asc())
        )
        reasoning_steps = (await session.scalars(stmt)).all()
        return reasoning_steps


async def delete_chats_by_task_id(task_id: int):
    """
    Delete all chats associated with task id
    """
    async with Session.begin() as session:
        stmt = delete(Chat).where(Chat.task_id == task_id)
        await session.execute(stmt)
        await session.commit()
