from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings

# Create engine with pool configuration
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=300,
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()

# Type alias for database session
DbSession = Session

def get_db() -> Session:
    """
    Dependency function to get database session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
EOFcat > /tmp/gpfx/backend/app/core/database.py << 'EOF'
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings

# Create engine with pool configuration
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=300,
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()

# Type alias for database session
DbSession = Session

def get_db() -> Session:
    """
    Dependency function to get database session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
