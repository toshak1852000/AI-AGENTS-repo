"""Alert database models."""

# TODO: Import Base from database when database setup is complete
# from src.core.database import Base


# class Alert(Base):
#     """Alert model."""
#     __tablename__ = "alerts"
# 
#     id = Column(String, primary_key=True)
#     severity = Column(String, nullable=False)  # info, warning, critical
#     title = Column(String, nullable=False)
#     message = Column(Text, nullable=False)
#     portfolio_id = Column(String, ForeignKey("portfolios.id"), nullable=True)
#     scenario_id = Column(String, ForeignKey("scenarios.id"), nullable=True)
#     read = Column(Boolean, default=False, nullable=False)
#     created_at = Column(DateTime(timezone=True), server_default=func.now())
