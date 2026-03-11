"""Exposure database models."""

# TODO: Import Base from database when database setup is complete
# from src.core.database import Base


# class Exposure(Base):
#     """Exposure calculation model."""
#     __tablename__ = "exposures"
# 
#     id = Column(String, primary_key=True)
#     portfolio_id = Column(String, ForeignKey("portfolios.id"), nullable=False)
#     scenario_id = Column(String, ForeignKey("scenarios.id"), nullable=False)
#     total_exposure = Column(Numeric, nullable=False)
#     risk_score = Column(Numeric, nullable=False)
#     company_exposures = Column(JSON, nullable=True)  # List of company-level exposures
#     sector_exposures = Column(JSON, nullable=True)  # List of sector-level exposures
#     calculated_at = Column(DateTime(timezone=True), server_default=func.now())
# 
# 
# class RiskScore(Base):
#     """Risk score model."""
#     __tablename__ = "risk_scores"
# 
#     id = Column(String, primary_key=True)
#     portfolio_id = Column(String, ForeignKey("portfolios.id"), nullable=False)
#     scenario_id = Column(String, ForeignKey("scenarios.id"), nullable=True)
#     risk_level = Column(String, nullable=False)  # low, medium, high, critical
#     score = Column(Numeric, nullable=False)
#     factors = Column(JSON, nullable=True)  # Risk factors contributing to score
#     calculated_at = Column(DateTime(timezone=True), server_default=func.now())
