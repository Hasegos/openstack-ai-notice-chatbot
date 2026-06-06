"""add_view_count_to_notices

Revision ID: f7e3a1b2c4d5
Revises:
Create Date: 2026-06-06 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "f7e3a1b2c4d5"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # notices 테이블에 view_count 컬럼 추가
    # server_default="0": 기존 행에도 0이 채워짐 (NOT NULL 제약 충족)
    op.add_column(
        "notices",
        sa.Column(
            "view_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )


def downgrade() -> None:
    op.drop_column("notices", "view_count")
