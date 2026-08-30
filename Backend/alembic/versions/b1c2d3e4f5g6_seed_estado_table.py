"""seed estado table

Revision ID: b1c2d3e4f5g6
Revises: adb182fa86fc
Create Date: 2026-08-30 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'b1c2d3e4f5g6'
down_revision: Union[str, Sequence[str], None] = 'adb182fa86fc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Seed estado table with initial data."""
    op.execute("""
        INSERT INTO estado(nombre) VALUES
        ('borrador'),
        ('contabilizado'),
        ('anulado'),
        ('abierto'),
        ('cerrado')
    """)


def downgrade() -> None:
    """Remove seeded data."""
    op.execute("""
        DELETE FROM estado WHERE nombre IN ('borrador', 'contabilizado', 'abierto', 'cerrado')
    """)
