"""migrate timestamps to timestamptz

Revision ID: 352470471702
Revises: 10de829fd609
Create Date: 2026-10-02 09:16:23.930016

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '352470471702'
down_revision: Union[str, Sequence[str], None] = '10de829fd609'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column("users", "created_at",
                    existing_type=sa.DateTime(),
                    type_=sa.DateTime(timezone=True),
                    existing_server_default=sa.text("(CURRENT_TIMESTAMP)"),
                    server_default=sa.text("now()"))
    
    op.alter_column("expenses", "created_at",
                    existing_type=sa.DateTime(),
                    type_=sa.DateTime(timezone=True),
                    existing_server_default=sa.text("(CURRENT_TIMESTAMP)"),
                    server_default=sa.text("now()"))


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column("users", "created_at",
                    existing_type=sa.DateTime(timezone=True),
                    type_=sa.DateTime(),
                    existing_server_default=sa.text("now()"),
                    server_default=sa.text("(CURRENT_TIMESTAMP)"))  
    
    op.alter_column("expenses", "created_at",
                    existing_type=sa.DateTime(timezone=True),
                    type_=sa.DateTime(),
                    existing_server_default=sa.text("now()"),
                    server_default=sa.text("(CURRENT_TIMESTAMP)"))  
