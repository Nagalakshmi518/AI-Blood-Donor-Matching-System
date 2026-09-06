"""merge donor and verification migration heads

Revision ID: ba5ead764205
Revises: 768015329887, f2c9b8a1e456
Create Date: 2026-08-14 23:21:45.679217

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ba5ead764205'
down_revision = ('768015329887', 'f2c9b8a1e456')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
