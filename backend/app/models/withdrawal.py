import uuid
from datetime import datetime, date
from sqlalchemy import Column, Numeric, DateTime, Text, ForeignKey, Date, UUID
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Withdrawal(Base):
    __tablename__ = "withdrawals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"))
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id"))
    amount = Column(Numeric(15, 2))
    date = Column(Date)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    account = relationship("Account", back_populates="withdrawals")
    workspace = relationship("Workspace", back_populates="withdrawals")
