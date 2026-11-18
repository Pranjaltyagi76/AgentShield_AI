"""Guest-owned immutable custom scenarios and private run-oracle snapshots."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0008"
down_revision = "0007"
branch_labels = depends_on = None


def upgrade():
    op.create_table(
        "custom_scenarios",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column(
            "owner_id",
            sa.Uuid(),
            sa.ForeignKey("guest_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index("ix_custom_scenarios_owner_id", "custom_scenarios", ["owner_id"])
    op.create_table(
        "custom_scenario_versions",
        sa.Column(
            "scenario_id",
            sa.String(),
            sa.ForeignKey("custom_scenarios.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("version", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("definition", postgresql.JSONB(), nullable=False),
        sa.Column("definition_hash", sa.String(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.add_column(
        "test_runs",
        sa.Column(
            "custom_oracles",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )


def downgrade():
    op.drop_column("test_runs", "custom_oracles")
    op.drop_table("custom_scenario_versions")
    op.drop_table("custom_scenarios")
