import enum
from typing import TYPE_CHECKING, List

from sqlalchemy import Enum, ForeignKey, ForeignKeyConstraint, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .reasoning_step import ReasoningStep

if TYPE_CHECKING:
    from .chat import Chat
    from .feedback import Feedback


class MessageRole(enum.Enum):
    """
    Message role enum
    """

    SYSTEM = 0
    USER = 1
    ASSISTANT = 2


class Message(Base):
    """
    Message model
    """

    __tablename__ = "message"
    __table_args__ = (
        ForeignKeyConstraint(["chat_id"], ["chat.id"], ondelete="CASCADE"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    chat_id: Mapped[int] = mapped_column(ForeignKey("chat.id"))
    role: Mapped[MessageRole] = mapped_column(Enum(MessageRole), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    reasoning_steps: Mapped[List["ReasoningStep"]] = relationship(
        cascade="all, delete-orphan"
    )
    chat: Mapped["Chat"] = relationship(back_populates="messages")
    feedback: Mapped["Feedback"] = relationship(back_populates="message")

    def __repr__(self) -> str:
        return (
            f"<Message(id={self.id!r}, chat_id={self.chat_id!r}, "
            + f"role={self.role!r}, content='{self.content[:20]!r}')>"
        )
