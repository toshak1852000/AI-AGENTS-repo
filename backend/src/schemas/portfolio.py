"""Portfolio Pydantic schemas."""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class PortfolioBase(BaseModel):
    """Base portfolio schema."""
    name: str = Field(..., description="Portfolio name")
    description: Optional[str] = Field(None, description="Portfolio description")


class PortfolioCreate(PortfolioBase):
    """Schema for creating a portfolio."""
    pass


class PortfolioUpdate(BaseModel):
    """Schema for updating a portfolio."""
    name: Optional[str] = None
    description: Optional[str] = None


class Portfolio(PortfolioBase):
    """Portfolio schema."""
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class HoldingBase(BaseModel):
    """Base holding schema."""
    symbol: str = Field(..., description="Stock symbol")
    company_name: str = Field(..., description="Company name")
    quantity: float = Field(..., gt=0, description="Number of shares")
    average_price: float = Field(..., gt=0, description="Average purchase price")
    sector: Optional[str] = Field(None, description="Sector")


class HoldingCreate(HoldingBase):
    """Schema for creating a holding."""
    pass


class HoldingUpdate(BaseModel):
    """Schema for updating a holding."""
    quantity: Optional[float] = None
    average_price: Optional[float] = None
    current_price: Optional[float] = None


class Holding(HoldingBase):
    """Holding schema."""
    id: str
    portfolio_id: str
    current_price: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True


class PortfolioWithHoldings(Portfolio):
    """Portfolio schema with holdings."""
    holdings: List[Holding] = []
