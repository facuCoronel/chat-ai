"""add media_id to incoming_messages and audio_transcription to message_insights

Revision ID: 0005
Revises: 0004
Create Date: 2026-05-28

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    messages_cols = {c["name"] for c in inspector.get_columns("incoming_messages")}
    if "media_id" not in messages_cols:
        op.add_column(
            "incoming_messages",
            sa.Column("media_id", sa.String(255), nullable=True),
        )

    insights_cols = {c["name"] for c in inspector.get_columns("message_insights")}
    if "audio_transcription" not in insights_cols:
        op.add_column(
            "message_insights",
            sa.Column("audio_transcription", sa.Text, nullable=True),
        )


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    insights_cols = {c["name"] for c in inspector.get_columns("message_insights")}
    if "audio_transcription" in insights_cols:
        op.drop_column("message_insights", "audio_transcription")

    messages_cols = {c["name"] for c in inspector.get_columns("incoming_messages")}
    if "media_id" in messages_cols:
        op.drop_column("incoming_messages", "media_id")
