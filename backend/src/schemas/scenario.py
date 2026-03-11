"""Scenario Pydantic schemas."""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from src.config.constants import ScenarioType, ScenarioStatus


class ScenarioBase(BaseModel):
    """Base scenario schema."""
    name: str = Field(..., description="Scenario name")
    description: Optional[str] = Field(None, description="Scenario description")
    type: ScenarioType = Field(..., description="Scenario type")
    parameters: Dict[str, Any] = Field(..., description="Scenario parameters")
    status: ScenarioStatus = Field(default=ScenarioStatus.DRAFT, description="Lifecycle status")


class ScenarioCreate(ScenarioBase):
    """Schema for creating a scenario."""
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Severe Market Crash",
                "description": "Simulates a broad equity or fixed-income market decline over a specified horizon.",
                "type": "market_shock",
                "parameters": {
                    "market_decline_percentage": 20.0,
                    "duration_days": 30,
                    "volatility_increase": 2.0
                },
                "status": "draft"
            }
        }
    }


class ScenarioUpdate(BaseModel):
    """Schema for updating a scenario."""
    name: Optional[str] = None
    description: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    status: Optional[ScenarioStatus] = None


class Scenario(ScenarioBase):
    """Scenario schema."""
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ScenarioFromTemplate(BaseModel):
    """Payload for creating a scenario from a template with optional overrides."""
    template_id: str
    name: Optional[str] = None
    description: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None


class ScenarioRunBase(BaseModel):
    """Base schema for scenario run."""
    scenario_id: str = Field(..., description="Scenario ID")
    portfolio_ids: list[str] = Field(..., description="List of portfolio IDs to analyze")
    status: str = Field(..., description="Status of the run (e.g., pending, running, completed, failed)")


class ScenarioRunCreate(ScenarioRunBase):
    """Schema for creating a scenario run."""
    pass


class ScenarioRunUpdate(BaseModel):
    """Schema for updating a scenario run."""
    status: Optional[str] = None
    results: Optional[Dict[str, Any]] = None


class ScenarioRun(ScenarioRunBase):
    """Schema for scenario run response."""
    id: str
    results: Optional[Dict[str, Any]] = None
    started_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True
