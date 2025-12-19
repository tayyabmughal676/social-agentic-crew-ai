from fastapi import APIRouter, HTTPException, BackgroundTasks
from models.schemas import TopicRequest, WorkflowResponse, WorkflowStatus, ApprovalRequest
from models.database import db
from workflows.linkedin_workflow import LinkedInPostWorkflow
from typing import Dict, Any, List
import uuid
from datetime import datetime
import logging

router = APIRouter(prefix="/api/v1", tags=["linkedin"])
logger = logging.getLogger(__name__)


@router.post("/create-post", response_model=WorkflowResponse)
async def create_linkedin_post(request: TopicRequest, background_tasks: BackgroundTasks):
    """Create a LinkedIn post using the CrewAI workflow"""
    try:
        workflow_id = str(uuid.uuid4())

        # Create workflow in database
        db.create_workflow(workflow_id, request.topic)
        
        # Initialize workflow status
        db.update_workflow(
            workflow_id,
            status="in_progress",
            current_step="initializing",
            progress_percentage=0.0
        )

        # Run workflow in background
        background_tasks.add_task(run_linkedin_workflow, workflow_id, request)

        return WorkflowResponse(
            workflow_id=workflow_id,
            status="in_progress",
            topic=request.topic,
            message=f"LinkedIn post creation started for topic: {request.topic}",
            timestamp=datetime.now()
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start workflow: {str(e)}")


@router.get("/workflow/{workflow_id}", response_model=WorkflowStatus)
async def get_workflow_status(workflow_id: str):
    """Get the status of a running workflow"""
    workflow = db.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    return WorkflowStatus(**workflow)


@router.post("/workflow/{workflow_id}/approve", response_model=Dict[str, Any])
async def approve_workflow(workflow_id: str, approval: ApprovalRequest):
    """Approve, modify, or reject a workflow result"""
    workflow = db.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    if workflow["status"] != "awaiting_approval":
        raise HTTPException(status_code=400, detail="Workflow is not awaiting approval")

    # Handle approval logic
    if approval.action == "approve":
        db.update_workflow(workflow_id, status="approved")
        return {"message": "Workflow approved successfully", "next_step": "publishing"}
    elif approval.action == "modify":
        db.update_workflow(workflow_id, status="modification_requested")
        return {"message": "Modification requested", "feedback": approval.feedback}
    elif approval.action == "reject":
        db.update_workflow(workflow_id, status="rejected")
        return {"message": "Workflow rejected"}
    else:
        raise HTTPException(status_code=400, detail="Invalid action")


@router.get("/workflows", response_model=List[WorkflowStatus])
async def list_workflows():
    """List all workflows"""
    workflows = db.list_workflows()
    return [WorkflowStatus(**workflow) for workflow in workflows]


@router.delete("/workflow/{workflow_id}")
async def delete_workflow(workflow_id: str):
    """Delete a workflow"""
    if not db.delete_workflow(workflow_id):
        raise HTTPException(status_code=404, detail="Workflow not found")

    return {"message": "Workflow deleted successfully"}


async def run_linkedin_workflow(workflow_id: str, request: TopicRequest):
    """Run the LinkedIn post creation workflow in background"""
    try:
        # Update status immediately
        db.update_workflow(
            workflow_id,
            current_step="initializing_workflow",
            progress_percentage=5.0
        )

        workflow = LinkedInPostWorkflow()

        # Progress tracking state
        steps_info = [
            ("research_strategy", 33.3),
            ("content_production", 66.6),
            ("finalization", 100.0)
        ]
        current_step_idx = 0

        db.update_workflow(
            workflow_id,
            current_step="research",
            progress_percentage=10.0
        )

        def on_task_completed(task_output):
            nonlocal current_step_idx
            logger.info(f"Task completed: {current_step_idx + 1}/{len(steps_info)}")
            
            if current_step_idx < len(steps_info):
                # The step that just finished
                finished_step = steps_info[current_step_idx][0]
                logger.info(f"Finished step: {finished_step}")
                
                # Prepare update for the NEXT step
                next_idx = current_step_idx + 1
                update_data = {}
                
                if next_idx < len(steps_info):
                    next_step, next_progress = steps_info[next_idx]
                    update_data["current_step"] = next_step
                    update_data["progress_percentage"] = next_progress
                    logger.info(f"Moving to next step: {next_step} ({next_progress}%)")
                
                # Update completed steps list
                workflow_data = db.get_workflow(workflow_id)
                if workflow_data:
                    completed = workflow_data.get("completed_steps", [])
                    if finished_step not in completed:
                        completed.append(finished_step)
                    update_data["completed_steps"] = completed
                
                db.update_workflow(workflow_id, **update_data)
                current_step_idx += 1

        # Run the workflow with target audience
        result = await workflow.run_workflow(
            request.topic, 
            audience=request.target_audience or "Professionals",
            task_callback=on_task_completed
        )

        # Update final status
        if result["status"] == "success":
            db.update_workflow(
                workflow_id,
                status="awaiting_approval",
                current_step="completed",
                progress_percentage=100.0,
                completed_steps=[
                    "research_strategy", "content_production", "finalization"
                ]
            )
        else:
            db.update_workflow(
                workflow_id,
                status="error",
                current_step=f"error: {result.get('error', 'Unknown error')}"
            )

    except Exception as e:
        error_str = str(e)
        
        # Check if it's a rate limit error
        if "rate limit" in error_str.lower() or "tpm" in error_str.lower() or "rate_limit" in error_str.lower():
            db.update_workflow(
                workflow_id,
                status="error",
                current_step=f"error: Rate limit exceeded. Please wait 60 seconds and try again.",
                error_details={
                    "type": "rate_limit",
                    "message": error_str,
                    "retry_after": 60
                }
            )
        else:
            db.update_workflow(
                workflow_id,
                status="error",
                current_step=f"error: {error_str}",
                error_details={
                    "type": "general",
                    "message": error_str
                }
            )
        
        import traceback
        logger.error(f"Workflow {workflow_id} failed with error: {error_str}")
        traceback.print_exc()
