from alembic import op
import sqlalchemy as sa

revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('accounts', 'metaapi_account_id',
        new_column_name='mt_last_ticket'
    )
    op.add_column('accounts',
        sa.Column('investor_password', sa.String(255), nullable=True)
    )


def downgrade():
    op.alter_column('accounts', 'mt_last_ticket',
        new_column_name='metaapi_account_id'
    )
    op.drop_column('accounts', 'investor_password')
