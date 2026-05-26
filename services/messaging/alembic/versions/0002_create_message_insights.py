"""create message_insights table

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-26

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if "message_insights" not in existing_tables:
        op.create_table(
            "message_insights",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("message_id", sa.String(36), nullable=False),
            sa.Column("wamid", sa.String(255), nullable=False),
            sa.Column("platform", sa.String(20), nullable=False),
            sa.Column("sender_id", sa.String(100), nullable=False),
            sa.Column("sender_role", sa.String(20), nullable=False),
            sa.Column("sentiment", sa.String(20), nullable=False),
            sa.Column("main_emotion", sa.String(30), nullable=False),
            sa.Column("intent", sa.String(30), nullable=False),
            sa.Column("urgency", sa.String(10), nullable=False),
            sa.Column("commercial_risk", sa.String(10), nullable=False),
            sa.Column("summary", sa.String(1024), nullable=False),
            sa.Column("recommended_action", sa.String(1024), nullable=False),
            sa.Column("insights", sa.JSON(), nullable=False),
            sa.Column("raw_model_response", sa.JSON(), nullable=False),
            sa.Column("model_name", sa.String(100), nullable=False),
            sa.Column("prompt_version", sa.String(20), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index("ix_message_insights_message_id", "message_insights", ["message_id"])
        op.create_index("ix_message_insights_wamid", "message_insights", ["wamid"])
        op.create_index("ix_message_insights_sentiment", "message_insights", ["sentiment"])
        op.create_index("ix_message_insights_intent", "message_insights", ["intent"])
        op.create_index(
            "ix_message_insights_commercial_risk", "message_insights", ["commercial_risk"]
        )
        op.create_index("ix_message_insights_created_at", "message_insights", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_message_insights_created_at", table_name="message_insights")
    op.drop_index("ix_message_insights_commercial_risk", table_name="message_insights")
    op.drop_index("ix_message_insights_intent", table_name="message_insights")
    op.drop_index("ix_message_insights_sentiment", table_name="message_insights")
    op.drop_index("ix_message_insights_wamid", table_name="message_insights")
    op.drop_index("ix_message_insights_message_id", table_name="message_insights")
    op.drop_table("message_insights")
