"""Add cascade delete to budget and pot transactions

Revision ID: e6fbd43c7d42
Revises: 55f450bf8295
Create Date: 2025-06-15 21:01:16.743516+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = 'e6fbd43c7d42'
down_revision: Union[str, None] = '55f450bf8295'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add ON DELETE CASCADE to the foreign key constraints
    op.drop_constraint('transactions_ibfk_3', 'transactions', type_='foreignkey')
    op.drop_constraint('transactions_ibfk_4', 'transactions', type_='foreignkey')
    
    op.create_foreign_key(
        'transactions_ibfk_3', 'transactions', 'budgets',
        ['budget_id'], ['id'], ondelete='CASCADE'
    )
    op.create_foreign_key(
        'transactions_ibfk_4', 'transactions', 'pots',
        ['pot_id'], ['id'], ondelete='CASCADE'
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Remove ON DELETE CASCADE from the foreign key constraints
    op.drop_constraint('transactions_ibfk_3', 'transactions', type_='foreignkey')
    op.drop_constraint('transactions_ibfk_4', 'transactions', type_='foreignkey')
    
    op.create_foreign_key(
        'transactions_ibfk_3', 'transactions', 'budgets',
        ['budget_id'], ['id']
    )
    op.create_foreign_key(
        'transactions_ibfk_4', 'transactions', 'pots',
        ['pot_id'], ['id']
    )
