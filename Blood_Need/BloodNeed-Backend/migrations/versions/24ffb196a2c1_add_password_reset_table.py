"""Add password reset table

Revision ID: 24ffb196a2c1
Revises: 2ca02f52a5d5
Create Date: 2026-09-01 17:06:43.330971
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = '24ffb196a2c1'
down_revision = '2ca02f52a5d5'
branch_labels = None
depends_on = None


def upgrade():
    # Create only password_reset table
    op.create_table(
        'password_reset',

        sa.Column(
            'reset_id',
            sa.Integer(),
            primary_key=True,
            autoincrement=True,
            nullable=False
        ),

        sa.Column(
            'email',
            sa.String(length=100),
            nullable=False
        ),

        sa.Column(
            'otp',
            sa.String(length=6),
            nullable=False
        ),

        sa.Column(
            'verified',
            sa.Boolean(),
            nullable=True,
            server_default=sa.text('0')
        )
    )


def downgrade():
    # Remove only password_reset table
    op.drop_table('password_reset')