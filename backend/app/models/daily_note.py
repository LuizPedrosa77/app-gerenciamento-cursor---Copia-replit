import uuid
from datetime import datetime, date
from sqlalchemy import Column, DateTime, Text, ForeignKey, Date, UUID
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class DailyNote(Base):
    __tablename__ = "daily_notes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"))
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id"))
    date = Column(Date)
    note = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    account = relationship("Account", back_populates="daily_notes")
    workspace = relationship("Workspace", back_populates="daily_notes")
