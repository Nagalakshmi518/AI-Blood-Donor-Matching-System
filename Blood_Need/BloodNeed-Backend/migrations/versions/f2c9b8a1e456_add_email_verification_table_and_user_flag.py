"""add email_verifications table and users.is_email_verified column

Revision ID: f2c9b8a1e456
Revises: e9b8a6c4f123
Create Date: 2026-08-14 23:13:00.091

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'f2c9b8a1e456'
down_revision = 'e9b8a6c4f123'
branch_labels = None
depends_on = None


def upgrade():
    # Add is_email_verified column to users table
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_email_verified', sa.Boolean(), nullable=True, server_default=sa.text('0')))

    # Create email_verifications table
    op.create_table(
        'email_verifications',
        sa.Column('verification_id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.user_id'), nullable=True),
        sa.Column('email', sa.String(length=150), nullable=False, index=True),
        sa.Column('otp_hash', sa.String(length=255), nullable=False),
        sa.Column('purpose', sa.Enum('verify', 'reset'), nullable=False, server_default='verify'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('used', sa.Boolean(), nullable=True, server_default=sa.text('0')),
        sa.Column('used_at', sa.DateTime(), nullable=True),
    )


def downgrade():
    # drop email_verifications
    op.drop_table('email_verifications')

    # drop is_email_verified column
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('is_email_verified')
