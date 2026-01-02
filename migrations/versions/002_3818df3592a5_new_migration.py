"""New migration

Revision ID: 3818df3592a5
Revises: 3aacd9174d1f
Create Date: 2025-12-31 14:16:22.091376

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "3818df3592a5"
down_revision: str | Sequence[str] | None = "3aacd9174d1f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        ---------- Tables ----------
        CREATE TABLE clients (
            id UUID PRIMARY KEY,
            name TEXT NOT NULL,
            scopes TEXT NOT NULL,
            is_active BOOLEAN NOT NULL,
            secret_hash TEXT NOT NULL,
            token_version INT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL,
            updated_at TIMESTAMPTZ NOT NULL
        );
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP TABLE IF EXISTS clients;
        """
    )
