"""migration message

Revision ID: 885d152f4859
Revises: 67d81e56ce48
Create Date: 2025-02-27 14:40:21.801517

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '885d152f4859'
down_revision: Union[str, None] = '67d81e56ce48'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
