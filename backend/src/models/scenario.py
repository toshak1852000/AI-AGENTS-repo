"""Scenario database models."""
from sqlalchemy import Column, String, DateTime, Text, JSON, ForeignKey
from sqlalchemy.sql import func

from src.core.database import Base


class Scenario(Base):
    """Scenario model."""
    __tablename__ = "scenarios"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    type = Column(String, nullable=False)  # ScenarioType enum
    parameters = Column(JSON, nullable=False)
    status = Column(String, nullable=False, default="draft") # ScenarioStatus enum
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class ScenarioRun(Base):
    """Scenario execution run model."""
    __tablename__ = "scenario_runs"

    id = Column(String, primary_key=True)
    scenario_id = Column(String, ForeignKey("scenarios.id"), nullable=False)
    portfolio_ids = Column(JSON, nullable=False) # List of portfolio IDs
    status = Column(String, nullable=False)  # pending, running, completed, failed
    results = Column(JSON, nullable=True)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
