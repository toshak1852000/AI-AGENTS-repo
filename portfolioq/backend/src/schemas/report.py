"""Report Pydantic schemas."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from src.config.constants import ReportFormat


class ReportBase(BaseModel):
    """Base report schema."""
    name: str = Field(..., description="Report name")
    type: str = Field(..., description="Report type")
    format: ReportFormat = Field(..., description="Report format")


class ReportCreate(ReportBase):
    """Schema for creating a report."""
    portfolio_id: Optional[str] = None
    scenario_id: Optional[str] = None


class Report(ReportBase):
    """Report schema."""
    id: str
    portfolio_id: Optional[str] = None
    scenario_id: Optional[str] = None
    file_path: Optional[str] = None
    download_url: Optional[str] = None
    generated_at: datetime

    class Config:
        from_attributes = True
