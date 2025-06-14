"""add color column to budget table

Revision ID: 55f450bf8295
Revises: 78493e2f0c86
Create Date: 2025-06-13 13:35:50.719223+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '55f450bf8295'
down_revision: Union[str, None] = '78493e2f0c86'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add color column to budgets table
    op.add_column('budgets', sa.Column('color', sa.String(length=50), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Drop color column from budgets table
    op.drop_column('budgets', 'color')
