"""change_account_balance_to_bigint

Revision ID: 731753821e37
Revises: 149fccfcde21
Create Date: 2025-06-09 15:23:42.123456

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '731753821e37'
down_revision: Union[str, None] = '149fccfcde21'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Convert balance column from INTEGER to BIGINT
    op.alter_column('accounts', 'balance',
                    existing_type=sa.INTEGER(),
                    type_=sa.BigInteger(),
                    existing_nullable=False)


def downgrade() -> None:
    # Convert balance column back to INTEGER
    op.alter_column('accounts', 'balance',
                    existing_type=sa.BigInteger(),
                    type_=sa.INTEGER(),
                    existing_nullable=False)
