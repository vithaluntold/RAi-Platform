"""add compliance cache, progress, learning, chat tables

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2025-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "e5f6a7b8c9d0"
down_revision = "4cff2332f79f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # -- cached_analysis_results --
    op.create_table(
        "cached_analysis_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("document_hash", sa.String(64), nullable=False),
        sa.Column("framework", sa.String(50), nullable=False),
        sa.Column("questions_hash", sa.String(64), nullable=False),
        sa.Column("results", sa.JSON(), nullable=False),
        sa.Column("result_metadata", sa.JSON(), nullable=True),
        sa.Column("access_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("last_accessed_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index(
        "idx_cached_results_lookup",
        "cached_analysis_results",
        ["document_hash", "framework", "questions_hash"],
        unique=True,
    )
    op.create_index(
        "ix_cached_analysis_results_document_hash",
        "cached_analysis_results",
        ["document_hash"],
    )

    # -- analysis_progress --
    analysisprogressstatus = postgresql.ENUM(
        "pending", "in_progress", "completed", "failed",
        name="analysisprogressstatus",
        create_type=True,
    )
    analysisprogressstatus.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "analysis_progress",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("job_id", sa.String(50), nullable=False),
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("compliance_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("question_id", sa.String(100), nullable=False),
        sa.Column(
            "status",
            analysisprogressstatus,
            nullable=False,
            server_default="pending",
        ),
        sa.Column("result", sa.JSON(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_analysis_progress_job_id", "analysis_progress", ["job_id"])
    op.create_index("idx_analysis_progress_session", "analysis_progress", ["session_id"])
    op.create_index(
        "idx_analysis_progress_job_question",
        "analysis_progress",
        ["job_id", "question_id"],
        unique=True,
    )

    # -- question_learning_data --
    op.create_table(
        "question_learning_data",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("document_hash", sa.String(64), nullable=False),
        sa.Column("framework", sa.String(50), nullable=False),
        sa.Column("question_id", sa.String(100), nullable=False),
        sa.Column("original_result", sa.JSON(), nullable=False),
        sa.Column("corrected_result", sa.JSON(), nullable=False),
        sa.Column("user_comments", sa.Text(), nullable=True),
        sa.Column("corrected_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index(
        "ix_question_learning_data_document_hash",
        "question_learning_data",
        ["document_hash"],
    )
    op.create_index(
        "idx_learning_data_lookup",
        "question_learning_data",
        ["document_hash", "framework", "question_id"],
    )

    # -- compliance_conversations --
    op.create_table(
        "compliance_conversations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("compliance_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(255), nullable=True),
        sa.Column("context_question_id", sa.String(100), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index(
        "idx_conversations_session",
        "compliance_conversations",
        ["session_id"],
    )

    # -- compliance_messages --
    chatmessagerole = postgresql.ENUM(
        "user", "assistant", "system",
        name="chatmessagerole",
        create_type=True,
    )
    chatmessagerole.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "compliance_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "conversation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("compliance_conversations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("role", chatmessagerole, nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("citations", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index(
        "idx_messages_conversation",
        "compliance_messages",
        ["conversation_id"],
    )


def downgrade() -> None:
    op.drop_table("compliance_messages")
    op.drop_table("compliance_conversations")
    op.drop_table("question_learning_data")
    op.drop_table("analysis_progress")
    op.drop_table("cached_analysis_results")

    # Drop enum types
    postgresql.ENUM(name="chatmessagerole").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="analysisprogressstatus").drop(op.get_bind(), checkfirst=True)
