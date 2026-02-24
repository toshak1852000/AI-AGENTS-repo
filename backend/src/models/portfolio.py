"""Portfolio database models."""
from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional

# TODO: Import Base from database when database setup is complete
# from src.core.database import Base


# class Portfolio(Base):
#     """Portfolio model."""
#     __tablename__ = "portfolios"
# 
#     id = Column(String, primary_key=True)
#     name = Column(String, nullable=False)
#     description = Column(Text, nullable=True)
#     created_at = Column(DateTime(timezone=True), server_default=func.now())
#     updated_at = Column(DateTime(timezone=True), onupdate=func.now())
# 
#     # Relationships
#     holdings = relationship("Holding", back_populates="portfolio", cascade="all, delete-orphan")
# 
# 
# class Holding(Base):
#     """Holding model."""
#     __tablename__ = "holdings"
# 
#     id = Column(String, primary_key=True)
#     portfolio_id = Column(String, ForeignKey("portfolios.id"), nullable=False)
#     symbol = Column(String, nullable=False)
#     company_name = Column(String, nullable=False)
#     quantity = Column(Numeric, nullable=False)
#     average_price = Column(Numeric, nullable=False)
#     current_price = Column(Numeric, nullable=True)
#     sector = Column(String, nullable=True)
#     created_at = Column(DateTime(timezone=True), server_default=func.now())
# 
#     # Relationships
#     portfolio = relationship("Portfolio", back_populates="holdings")
