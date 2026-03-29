# pylint: disable=unsubscriptable-object # pylint issue unsubscriptable-object
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, ForeignKeyConstraint, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .chat import Chat


class File(Base):
    """
    File model
    """

    __tablename__ = "file"
    __table_args__ = (
        ForeignKeyConstraint(["chat_id"], ["chat.id"], ondelete="CASCADE"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    chat_id: Mapped[int] = mapped_column(ForeignKey("chat.id"))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    chat: Mapped["Chat"] = relationship(back_populates="files")

    def __repr__(self) -> str:
        return f"<File(id={self.id!r}, chat_id={self.chat_id!r}, name='{self.name!r}')>"
