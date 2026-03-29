from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, ForeignKeyConstraint, String
from sqlalchemy.dialects.mysql import MEDIUMTEXT
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Text, TypeDecorator

from .base import Base

if TYPE_CHECKING:
    from .message import Message

# pylint: disable=abstract-method, too-many-ancestors
class CustomText(TypeDecorator):
    """Define data type for content attribute"""

    impl = Text

    def load_dialect_impl(self, dialect):
        if dialect.name == "mysql":
            return dialect.type_descriptor(MEDIUMTEXT())
        return dialect.type_descriptor(Text())


class ReasoningStep(Base):
    """
    Reasoning step model
    """

    __tablename__ = "reasoning_step"
    __table_args__ = (
        ForeignKeyConstraint(["message_id"], ["message.id"], ondelete="CASCADE"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    message_id: Mapped[int] = mapped_column(ForeignKey("message.id"))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    # A JSON string with the details of the reasoning steps
    # since there is no need to query on the reasoning steps
    # This make it easier to store flexible data
    content: Mapped[str] = mapped_column(CustomText, nullable=False)
    message: Mapped["Message"] = relationship(back_populates="reasoning_steps")

    def __repr__(self) -> str:
        return (
            f"<ReasoningStep(id={self.id!r}, "
            + f"message_id={self.message_id!r}, name='{self.name!r}')>"
        )
