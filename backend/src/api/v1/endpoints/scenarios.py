"""Scenario endpoints."""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional

from src.schemas.scenario import (
    Scenario, 
    ScenarioCreate, 
    ScenarioUpdate, 
    ScenarioRun,
    ScenarioFromTemplate
)
from src.services import scenario_service as svc

router = APIRouter()


class ScenarioRunRequest(BaseModel):
    """Request body for running a scenario."""

    portfolio_ids: list[str] = []


@router.get("/")
async def list_scenarios(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    type: Optional[str] = None,
    status: Optional[str] = None,
):
    """List all scenarios with pagination and filtering."""
    scenarios, total = svc.list_scenarios(skip=skip, limit=limit, type_filter=type, status_filter=status)
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "scenarios": scenarios,
    }


@router.get("/templates")
async def get_scenario_templates():
    """List all pre-built scenario templates available for use."""
    return svc.list_scenario_templates()


@router.get("/{scenario_id}", response_model=Scenario)
async def get_scenario(scenario_id: str):
    """Get a scenario by ID."""
    scenario = svc.get_scenario(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return scenario


@router.post("/", response_model=Scenario, status_code=201)
async def create_scenario(payload: ScenarioCreate):
    """Create a new scenario."""
    return svc.create_scenario(payload)


@router.post("/from-template", response_model=Scenario, status_code=201)
async def create_scenario_from_template(payload: ScenarioFromTemplate):
    """Create a new scenario from a pre-built template with optional overrides."""
    try:
        scenario = svc.create_scenario_from_template(payload)
        return scenario
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{scenario_id}", response_model=Scenario)
async def update_scenario(scenario_id: str, payload: ScenarioUpdate):
    """Update a scenario."""
    scenario = svc.update_scenario(scenario_id, payload)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return scenario


@router.delete("/{scenario_id}", status_code=204)
async def delete_scenario(scenario_id: str):
    """Delete a scenario."""
    deleted = svc.delete_scenario(scenario_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return None


@router.post("/{scenario_id}/run", response_model=ScenarioRun)
async def run_scenario(scenario_id: str, body: ScenarioRunRequest | None = None):
    """Run a scenario analysis."""
    portfolio_ids = list((body.portfolio_ids if body else []) or [])
    
    try:
        run = svc.execute_scenario(portfolio_ids, scenario_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    if not run:
        raise HTTPException(status_code=404, detail="Scenario not found")
        
    return run


@router.get("/{scenario_id}/runs", response_model=list[ScenarioRun])
async def get_scenario_run_history(scenario_id: str):
    """Get all past runs for a specific scenario."""
    # Ensure scenario actually exists
    scenario = svc.get_scenario(scenario_id)
    if not scenario:
         raise HTTPException(status_code=404, detail="Scenario not found")
         
    return svc.list_scenario_runs(scenario_id)


@router.get("/runs/{run_id}", response_model=ScenarioRun)
async def get_scenario_run(run_id: str):
    """Get status and details of a specific scenario run."""
    run = svc.get_scenario_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Scenario run not found")
    return run
