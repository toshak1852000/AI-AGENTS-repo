"""Exposure Pydantic schemas."""
from pydantic import BaseModel, Field
from typing import List
from datetime import datetime


class CompanyExposure(BaseModel):
    """Company-level exposure schema."""
    company_id: str
    symbol: str
    exposure: float = Field(..., description="Exposure value")
    impact: float = Field(..., description="Impact percentage")


class SectorExposure(BaseModel):
    """Sector-level exposure schema."""
    sector: str
    exposure: float = Field(..., description="Exposure value")
    impact: float = Field(..., description="Impact percentage")


class ExposureBase(BaseModel):
    """Base exposure schema."""
    portfolio_id: str
    scenario_id: str


class ExposureCreate(ExposureBase):
    """Schema for creating exposure calculation."""
    pass


class Exposure(ExposureBase):
    """Exposure schema."""
    id: str
    company_exposures: List[CompanyExposure] = []
    sector_exposures: List[SectorExposure] = []
    total_exposure: float
    risk_score: float = Field(..., ge=0.0, le=1.0, description="Risk score (0-1)")
    calculated_at: datetime

    class Config:
        from_attributes = True
