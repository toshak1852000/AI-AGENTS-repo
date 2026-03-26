"""Scenario CRUD and run endpoints."""
import time
import uuid
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.models.scenario import Scenario, ScenarioRun
from src.schemas.scenario import ScenarioCreate, ScenarioUpdate, Scenario as ScenarioSchema
from src.workflows import run_workflow
from src.analytics.metrics import SCENARIO_RUNS_TOTAL, SCENARIO_RUN_DURATION

router = APIRouter()


class ScenarioRunRequest(BaseModel):
    portfolio_ids: List[str] = []
    async_run: bool = False


class ScenarioRunResponse(BaseModel):
    run_id: str
    scenario_id: str
    portfolio_ids: List[str]
    status: str
    report_id: Optional[str] = None
    error: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


@router.get("/", response_model=List[ScenarioSchema])
def list_scenarios(db: Session = Depends(get_db)):
    return db.query(Scenario).order_by(Scenario.created_at.desc()).all()


@router.post("/", response_model=ScenarioSchema, status_code=status.HTTP_201_CREATED)
def create_scenario(body: ScenarioCreate, db: Session = Depends(get_db)):
    sc = Scenario(
        id=str(uuid.uuid4()),
        name=body.name,
        description=body.description,
        type=body.type.value,
        parameters=body.parameters,
    )
    db.add(sc)
    db.commit()
    db.refresh(sc)
    return sc


@router.get("/{scenario_id}", response_model=ScenarioSchema)
def get_scenario(scenario_id: str, db: Session = Depends(get_db)):
    sc = db.query(Scenario).filter(Scenario.id == scenario_id).first()
    if not sc:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return sc


@router.put("/{scenario_id}", response_model=ScenarioSchema)
def update_scenario(scenario_id: str, body: ScenarioUpdate, db: Session = Depends(get_db)):
    sc = db.query(Scenario).filter(Scenario.id == scenario_id).first()
    if not sc:
        raise HTTPException(status_code=404, detail="Scenario not found")
    if body.name is not None:
        sc.name = body.name
    if body.description is not None:
        sc.description = body.description
    if body.parameters is not None:
        sc.parameters = body.parameters
    db.commit()
    db.refresh(sc)
    return sc


@router.delete("/{scenario_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_scenario(scenario_id: str, db: Session = Depends(get_db)):
    sc = db.query(Scenario).filter(Scenario.id == scenario_id).first()
    if not sc:
        raise HTTPException(status_code=404, detail="Scenario not found")
    db.delete(sc)
    db.commit()


@router.post("/{scenario_id}/run", response_model=ScenarioRunResponse)
def run_scenario(
    scenario_id: str,
    body: Optional[ScenarioRunRequest] = None,
    db: Session = Depends(get_db),
):
    """Run a full scenario analysis synchronously."""
    sc = db.query(Scenario).filter(Scenario.id == scenario_id).first()
    if not sc:
        raise HTTPException(status_code=404, detail="Scenario not found")

    portfolio_ids = list((body.portfolio_ids if body else []) or [])
    run_id = str(uuid.uuid4())
    started_at = datetime.now(timezone.utc).isoformat()

    # Create run record
    run_record = ScenarioRun(
        id=run_id,
        scenario_id=scenario_id,
        portfolio_ids=portfolio_ids,
        status="running",
        started_at=datetime.now(timezone.utc),
    )
    db.add(run_record)
    db.commit()

    SCENARIO_RUNS_TOTAL.labels(scenario_type=sc.type, status="started").inc()

    _t_run = time.perf_counter()
    final_state = run_workflow(run_id=run_id, scenario_id=scenario_id, portfolio_ids=portfolio_ids)
    SCENARIO_RUN_DURATION.labels(scenario_type=sc.type).observe(time.perf_counter() - _t_run)

    # Update run record
    run_record.status = final_state.get("status", "unknown")
    run_record.report_id = final_state.get("report_id")
    run_record.error = final_state.get("error")
    run_record.exposure_result = final_state.get("exposure_result")
    run_record.risk_result = final_state.get("risk_result")
    if final_state.get("completed_at"):
        from dateutil import parser as dtparser
        run_record.completed_at = dtparser.parse(final_state["completed_at"])
    db.commit()

    return ScenarioRunResponse(
        run_id=run_id,
        scenario_id=scenario_id,
        portfolio_ids=portfolio_ids,
        status=final_state.get("status", "unknown"),
        report_id=final_state.get("report_id"),
        error=final_state.get("error"),
        started_at=started_at,
        completed_at=final_state.get("completed_at"),
    )


@router.get("/{scenario_id}/runs")
def list_runs(scenario_id: str, db: Session = Depends(get_db)):
    runs = db.query(ScenarioRun).filter(ScenarioRun.scenario_id == scenario_id).order_by(
        ScenarioRun.created_at.desc()
    ).all()
    return [
        {
            "run_id": r.id, "status": r.status, "portfolio_ids": r.portfolio_ids,
            "report_id": r.report_id, "error": r.error,
            "started_at": r.started_at, "completed_at": r.completed_at,
        }
        for r in runs
    ]
