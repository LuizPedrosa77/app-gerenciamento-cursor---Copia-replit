"""Add CPF to users table

Revision ID: 007_add_cpf_to_users
Revises: 006_add_profiles_plans_referrals_ai
Create Date: 2026-03-10 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '007_add_cpf_to_users'
down_revision: Union[str, None] = '006_add_profiles_plans_referrals_ai'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add cpf column to users table
    op.add_column('users', sa.Column('cpf', sa.String(length=11), nullable=True))
    
    # Create unique index on cpf
    op.create_index('ix_users_cpf', 'users', ['cpf'], unique=True)


def downgrade() -> None:
    # Drop the index
    op.drop_index('ix_users_cpf', table_name='users')
    
    # Remove cpf column
    op.drop_column('users', 'cpf')
