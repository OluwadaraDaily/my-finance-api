"""add pots id to the transactions table

Revision ID: 78493e2f0c86
Revises: 731753821e37
Create Date: 2025-06-09 19:57:01.596386+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '78493e2f0c86'
down_revision: Union[str, None] = '731753821e37'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add pot_id column to transactions table
    op.add_column('transactions', sa.Column('pot_id', sa.Integer(), nullable=True))
    
    # Add foreign key constraint
    op.create_foreign_key(
        'fk_transactions_pot_id',
        'transactions',
        'pots',
        ['pot_id'],
        ['id']
    )
    
    # Create index on pot_id for better query performance
    op.create_index('ix_transactions_pot_id', 'transactions', ['pot_id'])


def downgrade() -> None:
    """Downgrade schema."""
    # Drop index first
    op.drop_index('ix_transactions_pot_id', table_name='transactions')
    
    # Drop foreign key constraint
    op.drop_constraint('fk_transactions_pot_id', 'transactions', type_='foreignkey')
    
    # Drop column
    op.drop_column('transactions', 'pot_id')
