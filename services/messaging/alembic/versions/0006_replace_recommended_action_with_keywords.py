"""replace recommended_action with keywords in message_insights

Revision ID: 0006
Revises: 0005
Create Date: 2026-05-28

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    cols = {c["name"] for c in inspector.get_columns("message_insights")}

    if "keywords" not in cols:
        op.add_column(
            "message_insights",
            sa.Column("keywords", sa.JSON, nullable=False, server_default="[]"),
        )

    if "recommended_action" in cols:
        op.drop_column("message_insights", "recommended_action")


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    cols = {c["name"] for c in inspector.get_columns("message_insights")}

    if "recommended_action" not in cols:
        op.add_column(
            "message_insights",
            sa.Column("recommended_action", sa.String(1024), nullable=False, server_default=""),
        )

    if "keywords" in cols:
        op.drop_column("message_insights", "keywords")
