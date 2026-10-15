"""fix created_at defaults on otp, refresh tokens, social accounts

Revision ID: 2b66133c60cb
Revises: c1fe1bc899c3
Create Date: 2026-10-14 12:25:04.550604

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2b66133c60cb'
down_revision: Union[str, Sequence[str], None] = 'c1fe1bc899c3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 'now()' was stored as a string literal, so Postgres froze it at table
    # creation time. Replace it with a real now() evaluated on every insert.
    for table in ("otp_codes", "refresh_tokens", "social_accounts"):
        op.alter_column(table, "created_at", server_default=sa.text("now()"))

    # Retire reset/signup codes that were never used, so stale ones can't be picked.
    op.execute("UPDATE otp_codes SET consumed_at = now() WHERE consumed_at IS NULL")


def downgrade() -> None:
    """Downgrade schema."""
    pass