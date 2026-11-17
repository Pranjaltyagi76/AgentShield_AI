"""Store immutable comparisons of two retained runs."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0006"
down_revision = "0005"
branch_labels = depends_on = None


def upgrade():
    op.create_table(
        "benchmark_comparisons",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "baseline_run_id",
            sa.Uuid(),
            sa.ForeignKey("test_runs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "candidate_run_id",
            sa.Uuid(),
            sa.ForeignKey("test_runs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("comparison_json", JSONB(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("baseline_run_id", "candidate_run_id"),
        sa.CheckConstraint("baseline_run_id <> candidate_run_id", name="different_comparison_runs"),
    )
    op.create_index(
        "ix_benchmark_comparisons_candidate_run_id", "benchmark_comparisons", ["candidate_run_id"]
    )


def downgrade():
    op.drop_table("benchmark_comparisons")
