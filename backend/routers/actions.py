from fastapi import APIRouter, Depends, HTTPException
from backend.auth.deps import get_current_user
from backend.services.crew import ZeroInboxCrew
from backend.core.db import users_col
import sys
from io import StringIO

router = APIRouter(prefix="/actions", tags=["Actions"])



@router.post("/run-crew")
async def run_inbox_crew(current_user: dict = Depends(get_current_user)):
    token_data = current_user.get("google_token")

    if not token_data:
        raise HTTPException(status_code=400, detail="Google account not linked or token missing.")

    crew_service = ZeroInboxCrew(token_data)

    
    old_stdout = sys.stdout
    sys.stdout = buffer = StringIO()

    try:
        result = crew_service.run_workflow()
        logs = buffer.getvalue()
    finally:
        sys.stdout = old_stdout

    return {
        "status": "success",
        "logs": logs,
        "output": str(result)
    }