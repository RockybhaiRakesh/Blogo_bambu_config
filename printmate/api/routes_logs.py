"""
API Router for Log Management and Inspection.
Allows users to list and view .txt execution logs directly from the UI.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse
from typing import List, Dict, Any

from printmate.core.logger import ActionLogger

router = APIRouter(prefix="/api/logs", tags=["Logs"])


@router.get("", response_model=List[Dict[str, Any]])
def list_logs():
    """List all saved .txt logs sorted newest first."""
    return ActionLogger.list_logs()


@router.get("/{filename}", response_class=PlainTextResponse)
def get_log_content(filename: str):
    """Retrieve raw text content of a specific .txt log file."""
    content = ActionLogger.read_log(filename)
    if content is None:
        raise HTTPException(status_code=404, detail=f"Log file '{filename}' not found.")
    return content
