from datetime import datetime

from sqlalchemy import DateTime, MetaData
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    """
    Base class for all models
    """

    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        }
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        # pylint: disable-next=not-callable # pylint issue https://github.com/sqlalchemy/sqlalchemy/issues/9189
        server_default=func.now(),
        # pylint: disable-next=not-callable # pylint issue https://github.com/sqlalchemy/sqlalchemy/issues/9189
        insert_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        # pylint: disable-next=not-callable # pylint issue
        server_default=func.now(),
        # pylint: disable-next=not-callable # pylint issue
        insert_default=func.now(),
        # pylint: disable-next=not-callable # pylint issue
        onupdate=func.now(),
    )
