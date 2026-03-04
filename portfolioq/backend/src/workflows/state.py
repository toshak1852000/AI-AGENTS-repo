"""
Workflow state schema for the scenario analysis pipeline.

Used by the LangGraph workflow: data_collection → exposure_calculation
→ risk_assessment → report_generation. See docs/WORKFLOWS.md for full design.

- ScenarioAnalysisStateTypedDict: used inside the graph (nodes return partial dicts to merge).
- ScenarioAnalysisState: Pydantic model for validating initial state at API boundary.
"""
from typing import Any, Optional, TypedDict
from pydantic import BaseModel, Field


class ScenarioAnalysisStateTypedDict(TypedDict, total=False):
    """State dict for LangGraph; nodes return partial updates to merge."""

    run_id: str
    scenario_id: str
    portfolio_ids: list[str]
    status: str
    current_node: Optional[str]
    market_data: Optional[dict[str, Any]]
    exposure_result: Optional[dict[str, Any]]
    risk_result: Optional[dict[str, Any]]
    report_id: Optional[str]
    error: Optional[str]
    started_at: Optional[str]
    completed_at: Optional[str]


class ScenarioAnalysisState(BaseModel):
    """State passed through the scenario analysis workflow (validation at API boundary)."""

    # Inputs (set at workflow start)
    run_id: str = Field(..., description="Scenario run ID from DB")
    scenario_id: str = Field(..., description="Scenario ID")
    portfolio_ids: list[str] = Field(..., description="Portfolio IDs to analyze")

    # Status and progress
    status: str = Field(
        default="pending",
        description="pending | running | completed | failed",
    )
    current_node: Optional[str] = Field(
        default=None,
        description="Last executed node name (for logging/debug)",
    )

    # Outputs from nodes
    market_data: Optional[dict[str, Any]] = Field(
        default=None,
        description="Output of data_collection: normalized market/commodity data",
    )
    exposure_result: Optional[dict[str, Any]] = Field(
        default=None,
        description="Output of exposure_calculation (company/sector exposure)",
    )
    risk_result: Optional[dict[str, Any]] = Field(
        default=None,
        description="Output of risk_assessment (scores, P&L impact)",
    )
    report_id: Optional[str] = Field(
        default=None,
        description="After report_generation: stored report ID",
    )

    # Error and timestamps
    error: Optional[str] = Field(default=None, description="Error message if status=failed")
    started_at: Optional[str] = Field(default=None, description="ISO datetime when run started")
    completed_at: Optional[str] = Field(default=None, description="ISO datetime when run finished")

    class Config:
        extra = "forbid"

    def to_graph_state(self) -> ScenarioAnalysisStateTypedDict:
        """Convert to dict for LangGraph (required keys only; optional omitted if None)."""
        d: ScenarioAnalysisStateTypedDict = {
            "run_id": self.run_id,
            "scenario_id": self.scenario_id,
            "portfolio_ids": self.portfolio_ids,
            "status": self.status,
        }
        if self.current_node is not None:
            d["current_node"] = self.current_node
        if self.market_data is not None:
            d["market_data"] = self.market_data
        if self.exposure_result is not None:
            d["exposure_result"] = self.exposure_result
        if self.risk_result is not None:
            d["risk_result"] = self.risk_result
        if self.report_id is not None:
            d["report_id"] = self.report_id
        if self.error is not None:
            d["error"] = self.error
        if self.started_at is not None:
            d["started_at"] = self.started_at
        if self.completed_at is not None:
            d["completed_at"] = self.completed_at
        return d
