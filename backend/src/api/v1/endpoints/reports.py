"""Report endpoints."""
from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_reports():
    """List all reports."""
    # TODO: Implement report listing
    return {"reports": []}


@router.get("/{report_id}")
async def get_report(report_id: str):
    """Get a report by ID."""
    # TODO: Implement report retrieval
    return {"id": report_id}


@router.post("/generate")
async def generate_report():
    """Generate a report."""
    # TODO: Implement report generation
    return {"message": "Report generation not yet implemented"}


@router.get("/{report_id}/download")
async def download_report(report_id: str):
    """Download a report."""
    # TODO: Implement report download
    return {"message": "Report download not yet implemented"}
