"""create incoming_messages table

Revision ID: 0001
Revises:
Create Date: 2026-05-26

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "incoming_messages",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("wamid", sa.String(255), nullable=False),
        sa.Column("platform", sa.String(20), nullable=False),
        sa.Column("sender_id", sa.String(100), nullable=False),
        sa.Column("sender_name", sa.String(255), nullable=True),
        sa.Column("recipient_id", sa.String(100), nullable=False),
        sa.Column("message_type", sa.String(30), nullable=False),
        sa.Column("raw_text", sa.String(4096), nullable=True),
        sa.Column("raw_payload", sa.JSON(), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_unique_constraint("uq_incoming_messages_wamid", "incoming_messages", ["wamid"])
    op.create_index("ix_incoming_messages_platform", "incoming_messages", ["platform"])
    op.create_index("ix_incoming_messages_sender_id", "incoming_messages", ["sender_id"])
    op.create_index("ix_incoming_messages_received_at", "incoming_messages", ["received_at"])


def downgrade() -> None:
    op.drop_index("ix_incoming_messages_received_at", table_name="incoming_messages")
    op.drop_index("ix_incoming_messages_sender_id", table_name="incoming_messages")
    op.drop_index("ix_incoming_messages_platform", table_name="incoming_messages")
    op.drop_constraint("uq_incoming_messages_wamid", "incoming_messages", type_="unique")
    op.drop_table("incoming_messages")
