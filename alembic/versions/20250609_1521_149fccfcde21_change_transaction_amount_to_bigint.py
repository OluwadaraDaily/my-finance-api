"""change_transaction_amount_to_bigint

Revision ID: 149fccfcde21
Revises: b4413d847047
Create Date: 2025-06-09 15:21:42.438145+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '149fccfcde21'
down_revision: Union[str, None] = 'b4413d847047'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Convert amount column from INTEGER to BIGINT
    op.alter_column('transactions', 'amount',
                    existing_type=sa.INTEGER(),
                    type_=sa.BigInteger(),
                    existing_nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Convert amount column back to INTEGER
    op.alter_column('transactions', 'amount',
                    existing_type=sa.BigInteger(),
                    type_=sa.INTEGER(),
                    existing_nullable=False)
