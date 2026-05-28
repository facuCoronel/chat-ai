"""add business_accounts table and conversation fields to incoming_messages

Revision ID: 0004
Revises: 0003
Create Date: 2026-05-28

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if "business_accounts" not in existing_tables:
        op.create_table(
            "business_accounts",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("external_id", sa.String(100), nullable=False),
            sa.Column("display_name", sa.String(255), nullable=False),
            sa.Column("is_active", sa.Boolean, nullable=False, server_default="1"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index(
            "ix_business_accounts_external_id", "business_accounts", ["external_id"], unique=True
        )

    messages_cols = {c["name"] for c in inspector.get_columns("incoming_messages")}

    if "conversation_id" not in messages_cols:
        op.add_column(
            "incoming_messages",
            sa.Column("conversation_id", sa.String(255), nullable=True),
        )
        op.create_index(
            "ix_incoming_messages_conversation_id", "incoming_messages", ["conversation_id"]
        )

    if "business_account_id" not in messages_cols:
        op.add_column(
            "incoming_messages",
            sa.Column("business_account_id", sa.String(100), nullable=True),
        )

    if "customer_external_id" not in messages_cols:
        op.add_column(
            "incoming_messages",
            sa.Column("customer_external_id", sa.String(100), nullable=True),
        )
        op.create_index(
            "ix_incoming_messages_customer_external_id",
            "incoming_messages",
            ["customer_external_id"],
        )


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    messages_cols = {c["name"] for c in inspector.get_columns("incoming_messages")}

    if "customer_external_id" in messages_cols:
        op.drop_index("ix_incoming_messages_customer_external_id", table_name="incoming_messages")
        op.drop_column("incoming_messages", "customer_external_id")

    if "business_account_id" in messages_cols:
        op.drop_column("incoming_messages", "business_account_id")

    if "conversation_id" in messages_cols:
        op.drop_index("ix_incoming_messages_conversation_id", table_name="incoming_messages")
        op.drop_column("incoming_messages", "conversation_id")

    if "business_accounts" in existing_tables:
        op.drop_index("ix_business_accounts_external_id", table_name="business_accounts")
        op.drop_table("business_accounts")
