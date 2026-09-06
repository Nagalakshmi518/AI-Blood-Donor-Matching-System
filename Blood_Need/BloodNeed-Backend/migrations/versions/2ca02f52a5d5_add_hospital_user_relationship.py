"""Add hospital user relationship

Revision ID: 2ca02f52a5d5
Revises: ba5ead764205
Create Date: 2026-08-31 23:22:29.840469
"""

from alembic import op
from sqlalchemy.dialects import mysql


# revision identifiers
revision = "2ca02f52a5d5"
down_revision = "ba5ead764205"
branch_labels = None
depends_on = None


def upgrade():

    # ==================================================
    # IMPORTANT:
    # hospital_id already exists in blood_requests
    # user_id already exists in hospitals
    # So DO NOT add those columns again.
    # ==================================================


    # ==================================================
    # ADD HOSPITAL ROLE TO users ENUM
    # ==================================================

    with op.batch_alter_table(
        "users",
        schema=None
    ) as batch_op:

        batch_op.alter_column(
            "role",

            existing_type=mysql.ENUM(
                "ADMIN",
                "DONOR",
                "PATIENT"
            ),

            type_=mysql.ENUM(
                "ADMIN",
                "DONOR",
                "PATIENT",
                "HOSPITAL"
            ),

            existing_nullable=False
        )


def downgrade():

    # ==================================================
    # REMOVE HOSPITAL ROLE
    # ==================================================

    with op.batch_alter_table(
        "users",
        schema=None
    ) as batch_op:

        batch_op.alter_column(
            "role",

            existing_type=mysql.ENUM(
                "ADMIN",
                "DONOR",
                "PATIENT",
                "HOSPITAL"
            ),

            type_=mysql.ENUM(
                "ADMIN",
                "DONOR",
                "PATIENT"
            ),

            existing_nullable=False
        )