from typing import List, Optional

from sqlalchemy import select

from backend.src.models import Feedback, Session


async def create_feedback(
    message_id: int, user_id: int, text_feedback: str, rating: int
) -> Feedback:
    """
    Create a new feedback entry
    """
    async with Session() as session:
        feedback = Feedback(
            message_id=message_id,
            user_id=user_id,
            text_feedback=text_feedback,
            rating=rating,
        )
        session.add(feedback)
        await session.commit()
        return feedback


async def get_feedback_by_id(feedback_id: int) -> Optional[Feedback]:
    """
    Get feedback by conversation_id and user_id
    """
    async with Session() as session:
        return await session.get(Feedback, feedback_id)


async def get_feedbacks_by_user(
    user_id: int,
    page=0,
    limit=10,
) -> List[Feedback]:
    """
    Get feedback by user_id
    """
    async with Session() as session:
        stmt = (
            select(Feedback)
            .where(Feedback.user_id == user_id)
            .limit(limit)
            .offset(page * limit)
            .order_by(Feedback.created_at.desc())
        )
        return (await session.scalars(stmt)).all()
