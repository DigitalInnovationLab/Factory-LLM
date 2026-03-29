# pylint: disable=unsubscriptable-object # pylint issue unsubscriptable-object
from typing import TYPE_CHECKING, List

from sqlalchemy import Enum, ForeignKey, ForeignKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.src.constants import RagTechnique
from common import File

from .base import Base
from .message import Message

if TYPE_CHECKING:
    from .task import Task


class Chat(Base):
    """
    Chat model
    """

    __tablename__ = "chat"
    __table_args__ = (
        ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        ForeignKeyConstraint(["task_id"], ["task.id"]),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    task_id: Mapped[int] = mapped_column(ForeignKey("task.id"))
    rag_technique: Mapped[str] = mapped_column(
        Enum(RagTechnique), default=RagTechnique.VECTOR
    )
    vector_top_k: Mapped[int] = mapped_column(default=3)
    messages: Mapped[List["Message"]] = relationship(
        cascade="all, delete-orphan",
        back_populates="chat",
        order_by=Message.created_at.asc(),
    )
    files: Mapped[List["File"]] = relationship(
        cascade="all, delete-orphan", back_populates="chat"
    )
    task: Mapped["Task"] = relationship("Task")

    def __repr__(self) -> str:
        return f"<Chat(id={self.id!r}, user_id={self.user_id!r}, task_id={self.task_id!r})>"
