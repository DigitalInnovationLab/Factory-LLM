from sqlalchemy import (
    Enum,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.src.constants import LlmModel, Technique

from .base import Base


class Task(Base):
    """
    Task model
    """

    __tablename__ = "task"
    __table_args__ = (
        ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    initial_system_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    llm_model: Mapped[str] = mapped_column(Enum(LlmModel), default=LlmModel.GPT4O)
    prompting_technique: Mapped[str] = mapped_column(
        Enum(Technique), default=Technique.NONE
    )

    def __repr__(self) -> str:
        return f"<Task(id={self.id!r}, name='{self.name!r}')>"
