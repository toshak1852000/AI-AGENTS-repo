"""Exposure database models."""
import uuid
from sqlalchemy import Column, String, DateTime, Numeric, JSON, ForeignKey
from sqlalchemy.sql import func
from src.core.database import Base


def _uuid():
    return str(uuid.uuid4())


class Exposure(Base):
    __tablename__ = "exposures"

    id = Column(String, primary_key=True, default=_uuid)
    portfolio_id = Column(String, ForeignKey("portfolios.id"), nullable=False)
    scenario_id = Column(String, ForeignKey("scenarios.id"), nullable=True)
    run_id = Column(String, nullable=True)
    total_exposure = Column(Numeric, nullable=False, default=0)
    risk_score = Column(Numeric, nullable=False, default=0)
    company_exposures = Column(JSON, nullable=True)
    sector_exposures = Column(JSON, nullable=True)
    factor_exposures = Column(JSON, nullable=True)
    sensitivity_scores = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class RiskScore(Base):
    __tablename__ = "risk_scores"

    id = Column(String, primary_key=True, default=_uuid)
    portfolio_id = Column(String, ForeignKey("portfolios.id"), nullable=False)
    scenario_id = Column(String, ForeignKey("scenarios.id"), nullable=True)
    run_id = Column(String, nullable=True)
    score = Column(Numeric, nullable=False)
    risk_level = Column(String, nullable=False)
    pl_impact = Column(Numeric, nullable=True)
    factors = Column(JSON, nullable=True)
    model_version = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
