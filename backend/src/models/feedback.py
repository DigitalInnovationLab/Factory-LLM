from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, ForeignKeyConstraint, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .message import Message
    from .user import User


class Feedback(Base):
    """
    Feedback model
    """

    __tablename__ = "feedback"
    __table_args__ = (
        ForeignKeyConstraint(["message_id"], ["message.id"], ondelete="CASCADE"),
        ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    message_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("message.id", ondelete="CASCADE")
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("user.id", ondelete="CASCADE")
    )
    text_feedback: Mapped[str] = mapped_column(Text, nullable=False)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="feedbacks")
    message: Mapped["Message"] = relationship(back_populates="feedback")

    def __repr__(self) -> str:
        return (
            f"<Feedback(id={self.id!r}, message_id={self.message_id!r}, "
            f"user_id={self.user_id!r}, rating={self.rating!r}>"
        )
