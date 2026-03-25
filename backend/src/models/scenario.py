"""Scenario database models."""
import uuid
from sqlalchemy import Column, String, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.core.database import Base


def _uuid():
    return str(uuid.uuid4())


class Scenario(Base):
    __tablename__ = "scenarios"

    id = Column(String, primary_key=True, default=_uuid)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    type = Column(String, nullable=False)
    parameters = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    runs = relationship("ScenarioRun", back_populates="scenario", cascade="all, delete-orphan")


class ScenarioRun(Base):
    __tablename__ = "scenario_runs"

    id = Column(String, primary_key=True, default=_uuid)
    scenario_id = Column(String, ForeignKey("scenarios.id"), nullable=False)
    portfolio_ids = Column(JSON, nullable=False, default=list)
    status = Column(String, nullable=False, default="pending")
    current_node = Column(String, nullable=True)
    market_data = Column(JSON, nullable=True)
    exposure_result = Column(JSON, nullable=True)
    risk_result = Column(JSON, nullable=True)
    report_id = Column(String, nullable=True)
    error = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    scenario = relationship("Scenario", back_populates="runs")
