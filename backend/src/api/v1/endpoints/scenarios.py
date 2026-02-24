"""Scenario endpoints."""
import uuid
from fastapi import APIRouter
from pydantic import BaseModel

from src.workflows import run_workflow

router = APIRouter()


class ScenarioRunRequest(BaseModel):
    """Request body for running a scenario."""

    portfolio_ids: list[str] = []


@router.get("/")
async def list_scenarios():
    """List all scenarios."""
    # TODO: Implement scenario listing
    return {"scenarios": []}


@router.get("/{scenario_id}")
async def get_scenario(scenario_id: str):
    """Get a scenario by ID."""
    # TODO: Implement scenario retrieval
    return {"id": scenario_id}


@router.post("/")
async def create_scenario():
    """Create a new scenario."""
    # TODO: Implement scenario creation
    return {"message": "Scenario creation not yet implemented"}


@router.post("/{scenario_id}/run")
async def run_scenario(scenario_id: str, body: ScenarioRunRequest | None = None):
    """Run a scenario analysis (workflow: data_collection → exposure → risk → report)."""
    portfolio_ids = list((body.portfolio_ids if body else []) or [])
    run_id = str(uuid.uuid4())
    final_state = run_workflow(run_id=run_id, scenario_id=scenario_id, portfolio_ids=portfolio_ids)
    return {
        "run_id": run_id,
        "scenario_id": scenario_id,
        "portfolio_ids": portfolio_ids,
        "status": final_state.get("status", "unknown"),
        "report_id": final_state.get("report_id"),
        "error": final_state.get("error"),
        "started_at": final_state.get("started_at"),
        "completed_at": final_state.get("completed_at"),
    }
