"""Scenario Pydantic schemas."""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from src.config.constants import ScenarioType


class ScenarioBase(BaseModel):
    """Base scenario schema."""
    name: str = Field(..., description="Scenario name")
    description: Optional[str] = Field(None, description="Scenario description")
    type: ScenarioType = Field(..., description="Scenario type")
    parameters: Dict[str, Any] = Field(..., description="Scenario parameters")


class ScenarioCreate(ScenarioBase):
    """Schema for creating a scenario."""
    pass


class ScenarioUpdate(BaseModel):
    """Schema for updating a scenario."""
    name: Optional[str] = None
    description: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None


class Scenario(ScenarioBase):
    """Scenario schema."""
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
