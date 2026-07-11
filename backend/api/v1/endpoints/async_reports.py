from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from tasks.reporting_tasks import generate_scheduled_report
import uuid

router = APIRouter()

class ReportTrigger(BaseModel):
    user_id: str
    email: str
    dataset_id: str

@router.post("/trigger")
async def trigger_async_report(request: ReportTrigger, background_tasks: BackgroundTasks):
    """
    Triggers a heavy ML reporting task asynchronously using FastAPI BackgroundTasks.
    Returns a task ID immediately without blocking the web server.
    """
    try:
        task_id = str(uuid.uuid4())
        # Run report generation in standard background thread
        background_tasks.add_task(
            generate_scheduled_report,
            request.user_id, 
            request.email, 
            request.dataset_id
        )
        
        return {
            "status": "queued",
            "task_id": task_id,
            "message": "Your AI report is generating in the background. You will receive an email shortly."
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to queue task: {e}")
