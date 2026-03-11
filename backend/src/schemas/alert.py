"""Alert schemas."""
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

class AlertSeverity(str, Enum):
    info = "info"
    warning = "warning"
    critical = "critical"

class AlertBase(BaseModel):
    """Base alert attributes."""
    severity: AlertSeverity = Field(..., description="Alert severity level")
    title: str = Field(..., description="Short title of the alert")
    message: str = Field(..., description="Detailed alert message")
    portfolio_id: Optional[str] = Field(None, description="Related portfolio ID")
    scenario_id: Optional[str] = Field(None, description="Related scenario ID")
    channel: str = Field("system", description="Channel this alert belongs to")

class AlertCreate(AlertBase):
    """Schema for creating a new alert."""
    pass

class AlertUpdate(BaseModel):
    """Schema for updating an alert (e.g., dismissing/reading)."""
    read: Optional[bool] = Field(None, description="Whether the alert has been read/dismissed")

class Alert(AlertBase):
    """Full alert schema returned by the API."""
    id: str = Field(..., description="Unique alert ID")
    read: bool = Field(False, description="Whether the alert has been read/dismissed")
    created_at: datetime = Field(..., description="When the alert was generated")

class AlertListResponse(BaseModel):
    """Response schema for listing alerts with pagination."""
    total: int = Field(..., description="Total number of alerts matching the filter")
    skip: int = Field(..., description="Number of items skipped")
    limit: int = Field(..., description="Page size limit")
    alerts: List[Alert] = Field(..., description="List of alerts")
