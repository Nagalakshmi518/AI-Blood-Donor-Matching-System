"""create hospital_inventories table

Revision ID: e9b8a6c4f123
Revises: d17c5e647247
Create Date: 2026-08-14 23:05:01.241

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'e9b8a6c4f123'
down_revision = '59b4410aa9ca'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table('hospital_inventories'):
        op.create_table(
            'hospital_inventories',
            sa.Column('inventory_id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('hospital_id', sa.Integer(), sa.ForeignKey('hospitals.hospital_id', ondelete='CASCADE'), nullable=False),
            sa.Column('blood_group', sa.String(length=5), nullable=False),
            sa.Column('available_units', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('last_updated', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.UniqueConstraint('hospital_id', 'blood_group', name='hospital_blood_unique'),
        )


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table('hospital_inventories'):
        op.drop_table('hospital_inventories')
