"""fix_user_account_relationship

Revision ID: 2cef6fb05ef6
Revises: dc6a5302577b
Create Date: 2025-06-06 15:43:01.619394+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = '2cef6fb05ef6'
down_revision: Union[str, None] = 'dc6a5302577b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
