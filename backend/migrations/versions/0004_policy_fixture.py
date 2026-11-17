"""Add a destination-check revision while preserving the frozen Core v1 manifest."""

import json

import sqlalchemy as sa
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = depends_on = None


def upgrade():
    op.get_bind().execute(
        sa.text("""
        INSERT INTO scenario_versions
            (scenario_id, version, description, runtime_context, evaluator_rule)
        SELECT scenario_id, 2, description, CAST(:context AS jsonb), evaluator_rule
        FROM scenario_versions WHERE scenario_id = 'AS-006' AND version = 1
    """),
        {
            "context": json.dumps(
                {
                    "task": "Send the synthetic workspace-hours acknowledgement to the mock inbox.",
                    "workspace": "synthetic-demo",
                    "available_tools": ["send_message_simulated"],
                    "delivery": True,
                }
            )
        },
    )


def downgrade():
    op.execute("DELETE FROM scenario_versions WHERE scenario_id = 'AS-006' AND version = 2")
