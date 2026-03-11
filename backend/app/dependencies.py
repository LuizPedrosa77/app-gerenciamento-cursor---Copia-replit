from typing import Annotated

from fastapi import Depends
from sqlalchemy import Session

from app.core.database import get_db


# Type alias for database session dependency
DbSession = Annotated[Session, Depends(get_db)]
