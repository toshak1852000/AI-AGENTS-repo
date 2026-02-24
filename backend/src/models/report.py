"""Report database models."""
from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.sql import func

# TODO: Import Base from database when database setup is complete
# from src.core.database import Base


# class Report(Base):
#     """Report model."""
#     __tablename__ = "reports"
# 
#     id = Column(String, primary_key=True)
#     name = Column(String, nullable=False)
#     type = Column(String, nullable=False)  # portfolio_analysis, scenario_analysis, etc.
#     format = Column(String, nullable=False)  # pdf, excel, json, csv
#     portfolio_id = Column(String, ForeignKey("portfolios.id"), nullable=True)
#     scenario_id = Column(String, ForeignKey("scenarios.id"), nullable=True)
#     file_path = Column(String, nullable=True)  # Path to generated report file
#     generated_at = Column(DateTime(timezone=True), server_default=func.now())


# class ReportTemplate(Base):
#     """Report template model."""
#     __tablename__ = "report_templates"
# 
#     id = Column(String, primary_key=True)
#     name = Column(String, nullable=False)
#     type = Column(String, nullable=False)
#     template_content = Column(Text, nullable=False)  # JSON or template string
#     created_at = Column(DateTime(timezone=True), server_default=func.now())
#     updated_at = Column(DateTime(timezone=True), onupdate=func.now())
