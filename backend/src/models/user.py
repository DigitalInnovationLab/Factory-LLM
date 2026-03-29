from typing import TYPE_CHECKING, List

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .chat import Chat
    from .feedback import Feedback


class User(Base):
    """
    User model
    """

    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    chats: Mapped[List["Chat"]] = relationship()
    feedbacks: Mapped[List["Feedback"]] = relationship(back_populates="user")

    def __repr__(self) -> str:
        return f"<User(id={self.id!r}, email='{self.email!r}')>"
