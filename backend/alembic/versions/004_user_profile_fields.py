from alembic import op
import sqlalchemy as sa

revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None

def upgrade():
    op.execute("""
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS phone VARCHAR(20),
        ADD COLUMN IF NOT EXISTS birth_date DATE,
        ADD COLUMN IF NOT EXISTS country VARCHAR(100),
        ADD COLUMN IF NOT EXISTS address TEXT,
        ADD COLUMN IF NOT EXISTS city VARCHAR(100);
    """)

def downgrade():
    op.execute("""
        ALTER TABLE users
        DROP COLUMN IF EXISTS phone,
        DROP COLUMN IF EXISTS birth_date,
        DROP COLUMN IF EXISTS country,
        DROP COLUMN IF EXISTS address,
        DROP COLUMN IF EXISTS city;
    """)
