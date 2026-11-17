"""Retained report metadata with source-dependent lifecycle."""

import sqlalchemy as sa
from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = depends_on = None


def upgrade():
    op.create_table(
        "reports",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "run_id", sa.Uuid(), sa.ForeignKey("test_runs.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "comparison_id",
            sa.Uuid(),
            sa.ForeignKey("benchmark_comparisons.id", ondelete="CASCADE"),
        ),
        sa.Column("format", sa.String(), nullable=False),
        sa.Column("renderer_version", sa.String(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint(
            "run_id",
            "comparison_id",
            "format",
            "renderer_version",
            postgresql_nulls_not_distinct=True,
        ),
        sa.CheckConstraint("format IN ('html', 'json')", name="report_format"),
    )
    op.create_index("ix_reports_run_id", "reports", ["run_id"])
    op.create_index("ix_reports_comparison_id", "reports", ["comparison_id"])


def downgrade():
    op.drop_table("reports")
