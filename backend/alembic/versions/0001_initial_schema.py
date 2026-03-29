"""Initial full schema — squash of all prior migrations

Revision ID: 0001_initial_schema
Revises: None
Create Date: 2026-03-29

This is a squash migration that consolidates all previous incremental migrations
into a single baseline representing the complete current database schema.

For FRESH INSTALLS:
    alembic upgrade head

For EXISTING DATABASES (already migrated via the old chain):
    alembic stamp 0001_initial_schema
"""
# pylint: disable=no-member, invalid-name
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

# revision identifiers used by Alembic
revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# ---------------------------------------------------------------------------
# Enum definitions — mirrors backend/src/constants exactly
# ---------------------------------------------------------------------------
LLM_MODEL_ENUM = sa.Enum(
    "GPT35",
    "GPT4",
    "GPT4O_MINI",
    "GPT4O",
    "GEMINI15_PRO",
    "GEMINI15_FLASH",
    "GEMINI20_FLASH",
    "QUASARALPHA",
    "GEMINI23_PRO_EXP",
    "DEEPSEEKV3",
    "DEEPSEEKR1",
    "DEEPSEEKR1_ZERO",
    "LLAMA4_MAVERICK",
    "LLAMA4_SCOUT",
    "QWEN3_235B_INSTRUCT",
    "GEMMA3_27B",
    "GEMINI31_PRO",
    name="llmmodel",
)

TECHNIQUE_ENUM = sa.Enum("NONE", "COT", "TOT", "GOT", name="technique")

RAG_TECHNIQUE_ENUM = sa.Enum("NONE", "VECTOR", "GRAPH", name="ragtechnique")

MESSAGE_ROLE_ENUM = sa.Enum("SYSTEM", "USER", "ASSISTANT", name="messagerole")


def upgrade() -> None:
    """Create full database schema from scratch."""

    # ------------------------------------------------------------------
    # user
    # ------------------------------------------------------------------
    op.create_table(
        "user",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_user"),
        sa.UniqueConstraint("email", name="uq_user_email"),
    )

    # ------------------------------------------------------------------
    # task
    # ------------------------------------------------------------------
    op.create_table(
        "task",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("initial_system_prompt", sa.Text(), nullable=False),
        sa.Column("llm_model", LLM_MODEL_ENUM, nullable=False),
        sa.Column("prompting_technique", TECHNIQUE_ENUM, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user.id"],
            name="fk_task_user_id_user",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_task"),
    )

    # ------------------------------------------------------------------
    # chat
    # ------------------------------------------------------------------
    op.create_table(
        "chat",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("task_id", sa.Integer(), nullable=False),
        sa.Column("rag_technique", RAG_TECHNIQUE_ENUM, nullable=False),
        sa.Column(
            "vector_top_k", sa.Integer(), nullable=False, server_default="3"
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user.id"],
            name="fk_chat_user_id_user",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["task_id"],
            ["task.id"],
            name="fk_chat_task_id_task",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_chat"),
    )

    # ------------------------------------------------------------------
    # message
    # ------------------------------------------------------------------
    op.create_table(
        "message",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("chat_id", sa.Integer(), nullable=False),
        sa.Column("role", MESSAGE_ROLE_ENUM, nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["chat_id"],
            ["chat.id"],
            name="fk_message_chat_id_chat",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_message"),
    )

    # ------------------------------------------------------------------
    # reasoning_step  (MEDIUMTEXT for large LLM reasoning chains)
    # ------------------------------------------------------------------
    op.create_table(
        "reasoning_step",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("message_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("content", mysql.MEDIUMTEXT(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["message_id"],
            ["message.id"],
            name="fk_reasoning_step_message_id_message",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_reasoning_step"),
    )

    # ------------------------------------------------------------------
    # feedback
    # ------------------------------------------------------------------
    op.create_table(
        "feedback",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("message_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("text_feedback", sa.Text(), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["message_id"],
            ["message.id"],
            name="fk_feedback_message_id_message",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user.id"],
            name="fk_feedback_user_id_user",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_feedback"),
    )

    # ------------------------------------------------------------------
    # file
    # ------------------------------------------------------------------
    op.create_table(
        "file",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("chat_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["chat_id"],
            ["chat.id"],
            name="fk_file_chat_id_chat",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_file"),
    )


def downgrade() -> None:
    """Drop all tables in reverse dependency order."""
    op.drop_table("file")
    op.drop_table("feedback")
    op.drop_table("reasoning_step")
    op.drop_table("message")
    op.drop_table("chat")
    op.drop_table("task")
    op.drop_table("user")
    # Drop named enum types (MySQL ignores these; kept for portability)
    LLM_MODEL_ENUM.drop(op.get_bind(), checkfirst=True)
    TECHNIQUE_ENUM.drop(op.get_bind(), checkfirst=True)
    RAG_TECHNIQUE_ENUM.drop(op.get_bind(), checkfirst=True)
    MESSAGE_ROLE_ENUM.drop(op.get_bind(), checkfirst=True)
