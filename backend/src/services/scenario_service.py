"""In-memory scenario service. Replace with DB-backed service when database is available."""
from datetime import datetime, timezone
import uuid
from typing import Optional

from src.schemas.scenario import (
    Scenario,
    ScenarioCreate,
    ScenarioUpdate,
    ScenarioRun,
    ScenarioFromTemplate,
)
from src.workflows import run_workflow
from src.services import portfolio_service
from src.config.constants import SCENARIO_TEMPLATES


def _now() -> datetime:
    return datetime.now(timezone.utc)


# In-memory store (keyed by id)
_scenarios: dict[str, dict] = {}
_scenario_runs: dict[str, dict] = {}


def list_scenarios(
    skip: int = 0,
    limit: int = 20,
    type_filter: Optional[str] = None,
    status_filter: Optional[str] = None,
) -> tuple[list[Scenario], int]:
    """Return (scenarios slice, total count). Applies type/status filters if provided."""
    items = list(_scenarios.values())
    if type_filter:
        type_lower = type_filter.strip().lower()
        items = [s for s in items if s.get("type") == type_lower]
        
    if status_filter:
        status_lower = status_filter.strip().lower()
        items = [s for s in items if s.get("status") == status_lower]
    
    total = len(items)
    # Sort by created_at desc for stable pagination
    items.sort(key=lambda s: s["created_at"], reverse=True)
    slice_items = items[skip : skip + limit]
    
    scenarios = [
        Scenario(
            id=s["id"],
            name=s["name"],
            description=s.get("description"),
            type=s["type"],
            parameters=s["parameters"],
            status=s["status"],
            created_at=s["created_at"],
            updated_at=s.get("updated_at"),
        )
        for s in slice_items
    ]
    return scenarios, total


def get_scenario(scenario_id: str) -> Optional[Scenario]:
    """Get a scenario by ID or None if not found."""
    s = _scenarios.get(scenario_id)
    if not s:
        return None
    return Scenario(
        id=s["id"],
        name=s["name"],
        description=s.get("description"),
        type=s["type"],
        parameters=s["parameters"],
        status=s["status"],
        created_at=s["created_at"],
        updated_at=s.get("updated_at"),
    )


def create_scenario(payload: ScenarioCreate) -> Scenario:
    """Create a new scenario."""
    sid = str(uuid.uuid4())
    now = _now()
    _scenarios[sid] = {
        "id": sid,
        "name": payload.name,
        "description": payload.description,
        "type": payload.type.value,
        "parameters": payload.parameters,
        "status": payload.status.value if payload.status else "draft",
        "created_at": now,
        "updated_at": None,
    }
    return get_scenario(sid)  # type: ignore


def create_scenario_from_template(payload: ScenarioFromTemplate) -> Scenario:
    """Create a new scenario from a pre-built template, applying overrides."""
    template = None
    for t in SCENARIO_TEMPLATES:
        if t.get("id") == payload.template_id:
            template = t
            break
            
    if not template:
        raise ValueError(f"Template not found: {payload.template_id}")
        
    # Deep copy parameters to avoid mutating the original template
    import copy
    merged_parameters = copy.deepcopy(template.get("parameters", {}))
    if payload.parameters:
        merged_parameters.update(payload.parameters)
        
    create_payload = ScenarioCreate(
        name=payload.name if payload.name else template.get("name", "New Scenario"),
        description=payload.description if payload.description else template.get("description", ""),
        type=template.get("type"),  # type: ignore
        parameters=merged_parameters
    )
    
    return create_scenario(create_payload)


def update_scenario(scenario_id: str, payload: ScenarioUpdate) -> Optional[Scenario]:
    """Update a scenario. Returns updated scenario or None if not found."""
    s = _scenarios.get(scenario_id)
    if not s:
        return None
    
    if payload.name is not None:
        s["name"] = payload.name
    if payload.description is not None:
        s["description"] = payload.description
    if payload.parameters is not None:
        s["parameters"] = payload.parameters
    if payload.status is not None:
        s["status"] = payload.status.value
        
    s["updated_at"] = _now()
    return get_scenario(scenario_id)


def delete_scenario(scenario_id: str) -> bool:
    """Delete a scenario. Returns True if deleted, False if not found."""
    if scenario_id not in _scenarios:
        return False
    del _scenarios[scenario_id]
    return True


def clear_all() -> None:
    """Clear all in-memory data. For testing only."""
    _scenarios.clear()
    _scenario_runs.clear()


def execute_scenario(portfolio_ids: list[str], scenario_id: str) -> Optional[ScenarioRun]:
    """Execute a scenario for the given portfolios. 
       Returns the ScenarioRun or None if scenario doesn't exist."""
    scenario = get_scenario(scenario_id)
    if not scenario:
        return None
        
    for pid in portfolio_ids:
        if not portfolio_service.get_portfolio(pid):
            raise ValueError(f"Portfolio not found: {pid}")
        
    run_id = str(uuid.uuid4())
    started_at = _now()
    
    # Initialize run record
    _scenario_runs[run_id] = {
        "id": run_id,
        "scenario_id": scenario_id,
        "portfolio_ids": portfolio_ids,
        "status": "running",
        "results": None,
        "started_at": started_at,
        "completed_at": None,
    }
    
    # Trigger LangGraph Workflow
    try:
        final_state = run_workflow(run_id=run_id, scenario_id=scenario_id, portfolio_ids=portfolio_ids)
        
        # Update run record with results
        _scenario_runs[run_id]["status"] = final_state.get("status", "completed")
        _scenario_runs[run_id]["completed_at"] = _now()
        
        if final_state.get("error"):
            _scenario_runs[run_id]["results"] = {"error": final_state.get("error")}
        else:
            _scenario_runs[run_id]["results"] = {
                "report_id": final_state.get("report_id"),
                "exposure_result": final_state.get("exposure_result"),
                "risk_result": final_state.get("risk_result")
            }
            
    except Exception as e:
        _scenario_runs[run_id]["status"] = "failed"
        _scenario_runs[run_id]["completed_at"] = _now()
        _scenario_runs[run_id]["results"] = {"error": str(e)}

    return get_scenario_run(run_id)


def get_scenario_run(run_id: str) -> Optional[ScenarioRun]:
    """Retrieves a scenario run by its run ID."""
    r = _scenario_runs.get(run_id)
    if not r:
        return None
        
    return ScenarioRun(
        id=r["id"],
        scenario_id=r["scenario_id"],
        portfolio_ids=r["portfolio_ids"],
        status=r["status"],
        results=r["results"],
        started_at=r["started_at"],
        completed_at=r["completed_at"]
    )


def list_scenario_runs(scenario_id: str) -> list[ScenarioRun]:
    """Retrieves all scenario runs for a given scenario, ordered by latest first."""
    rums = [
        ScenarioRun(
            id=r["id"],
            scenario_id=r["scenario_id"],
            portfolio_ids=r["portfolio_ids"],
            status=r["status"],
            results=r["results"],
            started_at=r["started_at"],
            completed_at=r["completed_at"]
        )
        for r in _scenario_runs.values()
        if r["scenario_id"] == scenario_id
    ]
    # Sort descending by start time
    rums.sort(key=lambda x: x.started_at, reverse=True)
    return rums


def list_scenario_templates() -> list[dict]:
    """Retrieves all pre-built scenario templates from configuration constants."""
    return SCENARIO_TEMPLATES
