"""Report endpoints."""
import os
from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import FileResponse

from src.schemas.report import Report, ReportCreate
import src.services.report_service as report_service

router = APIRouter()


@router.get("/", response_model=dict[str, list[Report] | int])
async def list_reports(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    """List all reports."""
    reports, total = report_service.list_reports(skip=skip, limit=limit)
    return {"reports": reports, "total": total}


@router.get("/{report_id}", response_model=Report)
async def get_report(report_id: str):
    """Get a report by ID."""
    report_id = report_id.strip().strip('"')
    report = report_service.get_report(report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Report not found"
        )
    return report


@router.post("/generate", response_model=Report, status_code=status.HTTP_201_CREATED)
async def generate_report(
    payload: ReportCreate,
):
    """Generate a report synchronously. Returns the completed report."""
    report = report_service.generate_report(payload)
    return report


@router.get("/{report_id}/download")
async def download_report(report_id: str):
    """Download a generated report."""
    report_id = report_id.strip().strip('"')
    report = report_service.get_report(report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Report not found"
        )
        
    if report.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"Report is not ready. Current status: {report.status}"
        )
        
    if not report.file_path or not os.path.exists(report.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Report file not found on disk"
        )
        
    # Determine media type based on format
    media_type = "application/octet-stream"
    # ReportFormat might be Enum
    fmt = report.format.value if hasattr(report.format, "value") else report.format
    if fmt == "pdf":
        media_type = "application/pdf"
    elif fmt == "excel":
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    elif fmt == "csv":
        media_type = "text/csv"
    elif fmt == "json":
        media_type = "application/json"
        
    filename = os.path.basename(report.file_path)
    
    return FileResponse(
        path=report.file_path, 
        media_type=media_type, 
        filename=filename
    )
