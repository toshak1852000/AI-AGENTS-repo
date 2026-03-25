"""Report database models."""
import uuid
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.sql import func
from src.core.database import Base


def _uuid():
    return str(uuid.uuid4())


class Report(Base):
    __tablename__ = "reports"

    id = Column(String, primary_key=True, default=_uuid)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    format = Column(String, nullable=False)
    portfolio_id = Column(String, ForeignKey("portfolios.id"), nullable=True)
    scenario_id = Column(String, ForeignKey("scenarios.id"), nullable=True)
    run_id = Column(String, nullable=True)
    file_path = Column(String, nullable=True)
    summary = Column(JSON, nullable=True)
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
