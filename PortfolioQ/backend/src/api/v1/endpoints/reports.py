"""Report endpoints."""
import os
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.models.report import Report

router = APIRouter()


@router.get("/")
def list_reports(
    portfolio_id: Optional[str] = None,
    scenario_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(Report)
    if portfolio_id:
        q = q.filter(Report.portfolio_id == portfolio_id)
    if scenario_id:
        q = q.filter(Report.scenario_id == scenario_id)
    rows = q.order_by(Report.generated_at.desc()).limit(50).all()
    return [
        {
            "id": r.id, "name": r.name, "type": r.type, "format": r.format,
            "portfolio_id": r.portfolio_id, "scenario_id": r.scenario_id,
            "run_id": r.run_id, "generated_at": r.generated_at,
            "summary": r.summary,
        }
        for r in rows
    ]


@router.get("/{report_id}")
def get_report(report_id: str, db: Session = Depends(get_db)):
    r = db.query(Report).filter(Report.id == report_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Report not found")
    return {
        "id": r.id, "name": r.name, "type": r.type, "format": r.format,
        "portfolio_id": r.portfolio_id, "scenario_id": r.scenario_id,
        "run_id": r.run_id, "file_path": r.file_path,
        "generated_at": r.generated_at, "summary": r.summary,
    }


@router.get("/{report_id}/download")
def download_report(report_id: str, db: Session = Depends(get_db)):
    r = db.query(Report).filter(Report.id == report_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Report not found")
    if not r.file_path or not os.path.exists(r.file_path):
        raise HTTPException(status_code=404, detail="Report file not found")
    media_type = {
        "pdf": "application/pdf",
        "excel": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "json": "application/json",
    }.get(r.format, "application/octet-stream")
    return FileResponse(r.file_path, media_type=media_type, filename=f"report_{report_id}.{r.format}")


class ReportGenerateRequest(BaseModel):
    scenario_id: str
    portfolio_id: str
    run_id: Optional[str] = None
    format: str = "json"


@router.post("/generate")
def generate_report_endpoint(body: ReportGenerateRequest, db: Session = Depends(get_db)):
    """Manually generate a report from existing scenario run data."""
    from src.models.scenario import Scenario, ScenarioRun
    from src.models.portfolio import Portfolio
    from src.services.report_service import generate_report

    sc = db.query(Scenario).filter(Scenario.id == body.scenario_id).first()
    if not sc:
        raise HTTPException(status_code=404, detail="Scenario not found")
    port = db.query(Portfolio).filter(Portfolio.id == body.portfolio_id).first()
    if not port:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    run = None
    if body.run_id:
        run = db.query(ScenarioRun).filter(ScenarioRun.id == body.run_id).first()

    scenario_dict = {"id": sc.id, "name": sc.name, "type": sc.type, "parameters": sc.parameters}
    portfolio_dict = {"id": port.id, "name": port.name}
    exposure_result = (run.exposure_result if run else {}) or {}
    risk_result = (run.risk_result if run else {}) or {}
    run_id = body.run_id or "manual"

    summary = generate_report(db, scenario_dict, portfolio_dict, exposure_result, risk_result, run_id, body.format)
    return summary
