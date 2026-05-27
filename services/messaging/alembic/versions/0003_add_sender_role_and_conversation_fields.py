"""add sender_role to messages and recipient_id/sender_name to insights

Revision ID: 0003
Revises: 0002
Create Date: 2026-05-26

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    messages_cols = {c["name"] for c in inspector.get_columns("incoming_messages")}
    if "sender_role" not in messages_cols:
        op.add_column(
            "incoming_messages",
            sa.Column("sender_role", sa.String(20), nullable=False, server_default="buyer"),
        )

    insights_cols = {c["name"] for c in inspector.get_columns("message_insights")}
    if "recipient_id" not in insights_cols:
        op.add_column(
            "message_insights",
            sa.Column("recipient_id", sa.String(100), nullable=False, server_default=""),
        )
    if "sender_name" not in insights_cols:
        op.add_column(
            "message_insights",
            sa.Column("sender_name", sa.String(255), nullable=True),
        )


def downgrade() -> None:
    op.drop_column("message_insights", "sender_name")
    op.drop_column("message_insights", "recipient_id")
    op.drop_column("incoming_messages", "sender_role")
