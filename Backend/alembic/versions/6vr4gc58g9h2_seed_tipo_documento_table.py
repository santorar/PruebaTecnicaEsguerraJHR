"""seed tipo documento table

Revision ID: 6vr4gc58g9h2
Revises: b05c1ee690b8
Create Date: 2026-08-30 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '6vr4gc58g9h2'
down_revision: Union[str, Sequence[str], None] = 'b05c1ee690b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Seed estado table with initial data."""
    op.execute("""
        INSERT INTO tipo_documento(nombre) VALUES
        ('Cedula de ciudadania')
    """)


def downgrade() -> None:
    """Remove seeded data."""
    op.execute("""
        DELETE FROM tipo_documento WHERE nombre IN ('Cedula de ciudadania')
    """)
