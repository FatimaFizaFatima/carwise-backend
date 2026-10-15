"""add workshop indexes

Revision ID: f051d7618709
Revises: 2b66133c60cb
Create Date: 2026-10-14 15:18:39.969856

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f051d7618709'
down_revision: Union[str, Sequence[str], None] = '2b66133c60cb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index("ix_workshops_status", "workshops", ["status"])
    op.create_index("ix_workshops_lat_lng", "workshops", ["latitude", "longitude"])
    op.create_index("uq_workshop_services_workshop_category", "workshop_services",
                    ["workshop_id", "category_id"], unique=True)
    op.create_index("ix_workshop_services_category_id", "workshop_services", ["category_id"])
    op.create_index("ix_workshop_reviews_workshop_created", "workshop_reviews",
                    ["workshop_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_workshop_reviews_workshop_created", table_name="workshop_reviews")
    op.drop_index("ix_workshop_services_category_id", table_name="workshop_services")
    op.drop_index("uq_workshop_services_workshop_category", table_name="workshop_services")
    op.drop_index("ix_workshops_lat_lng", table_name="workshops")
    op.drop_index("ix_workshops_status", table_name="workshops")