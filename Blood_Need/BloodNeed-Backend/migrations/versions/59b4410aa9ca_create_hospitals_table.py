"""create hospitals table

Revision ID: 59b4410aa9ca
Revises: ba5ead764205
Create Date: 2026-08-14 23:26:14.977432
"""

from alembic import op
import sqlalchemy as sa


revision = '59b4410aa9ca'
down_revision = 'd17c5e647247'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table('hospitals'):
        op.create_table(
            'hospitals',
            sa.Column('hospital_id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('hospital_name', sa.String(length=200), nullable=False),
            sa.Column('address', sa.Text(), nullable=False),
            sa.Column('latitude', sa.Float(), nullable=False),
            sa.Column('longitude', sa.Float(), nullable=False),
            sa.Column('phone', sa.String(length=15), nullable=True),
            sa.Column('email', sa.String(length=100), nullable=True),
            sa.Column('city', sa.String(length=100), nullable=True),
            sa.Column('state', sa.String(length=100), nullable=True),
            sa.Column('pincode', sa.String(length=10), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=True, server_default='1'),
            sa.Column('created_at', sa.DateTime(), nullable=True,
                      server_default=sa.text('CURRENT_TIMESTAMP'))
        )


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table('hospitals'):
        op.drop_table('hospitals')