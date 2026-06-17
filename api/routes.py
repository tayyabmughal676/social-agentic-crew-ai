from fastapi import APIRouter, HTTPException, BackgroundTasks, Security, Depends, status, Form
from fastapi.security.api_key import APIKeyHeader
from fastapi.responses import HTMLResponse
from models.schemas import TopicRequest, WorkflowResponse, WorkflowStatus, ApprovalRequest
from models.database import db
from workflows.linkedin_workflow import LinkedInPostWorkflow
from typing import Dict, Any, List, Optional
import uuid
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

API_KEY_NAME = "X-API-Key"
api_key_header_scheme = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def get_api_key(api_key: str = Security(api_key_header_scheme)):
    expected_api_key = os.getenv("API_KEY")
    
    # If API_KEY environment variable is not defined
    if not expected_api_key:
        is_debug = os.getenv("DEBUG", "false").lower() == "true"
        if is_debug:
            # Bypass authentication in local debug mode if API_KEY is not defined
            return None
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Security configuration error: API_KEY is not set."
            )
            
    if api_key != expected_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials: Invalid or missing X-API-Key"
        )
    return api_key

router = APIRouter(
    prefix="/api/v1",
    tags=["linkedin"],
    dependencies=[Depends(get_api_key)]
)


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
                ],
                result=result["result"]
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


# ─────────────────────────────────────────────
# HTMX HTML Fragment Routes (used by the Dashboard)
# ─────────────────────────────────────────────

def _status_badge(status: str) -> str:
    classes = {
        "in_progress": "badge-progress",
        "awaiting_approval": "badge-warning",
        "approved": "badge-success",
        "rejected": "badge-error",
        "error": "badge-error",
        "modification_requested": "badge-warning",
    }
    labels = {
        "in_progress": "⚙️ Running",
        "awaiting_approval": "⏳ Awaiting Approval",
        "approved": "✅ Approved",
        "rejected": "❌ Rejected",
        "error": "🔴 Error",
        "modification_requested": "✏️ Needs Changes",
    }
    cls = classes.get(status, "badge-progress")
    lbl = labels.get(status, status.replace("_", " ").title())
    return f'<span class="badge {cls}">{lbl}</span>'


def _step_checklist(completed: list, current: str) -> str:
    steps = [
        ("research_strategy", "📊 Market Research & Strategy"),
        ("content_production", "✍️ Content Production"),
        ("finalization", "📋 Blueprint PDF Generation"),
    ]
    html = '<div class="step-checklist">'
    for key, label in steps:
        if key in completed:
            html += f'<div class="step-item done"><div class="step-bullet"></div>{label}</div>'
        elif current in ("research", "initializing", "initializing_workflow") and key == "research_strategy":
            html += f'<div class="step-item active"><div class="step-bullet"></div>{label}</div>'
        elif current == "content_production" and key == "content_production":
            html += f'<div class="step-item active"><div class="step-bullet"></div>{label}</div>'
        elif current == "finalization" and key == "finalization":
            html += f'<div class="step-item active"><div class="step-bullet"></div>{label}</div>'
        else:
            html += f'<div class="step-item"><div class="step-bullet"></div>{label}</div>'
    html += '</div>'
    return html


@router.post("/html/create-post", response_class=HTMLResponse)
async def html_create_post(
    background_tasks: BackgroundTasks,
    topic: str = Form(...),
    target_audience: Optional[str] = Form(None),
    tone: Optional[str] = Form("professional"),
    post_length: Optional[str] = Form("medium"),
    urgency: Optional[str] = Form("normal"),
):
    """HTMX: Create a workflow and return an in-progress card HTML fragment"""
    workflow_id = str(uuid.uuid4())
    db.create_workflow(workflow_id, topic)
    db.update_workflow(workflow_id, status="in_progress", current_step="initializing", progress_percentage=0.0)

    request = TopicRequest(
        topic=topic,
        target_audience=target_audience,
        tone=tone,
        post_length=post_length,
        urgency=urgency,
    )
    background_tasks.add_task(run_linkedin_workflow, workflow_id, request)

    html = f"""
    <div class="card"
         hx-get="/api/v1/html/workflow/{workflow_id}/card"
         hx-trigger="every 3s"
         hx-swap="outerHTML">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1.5rem;">
            <h2 style="margin:0; font-size:1.1rem;">📡 Assembling Agent Team...</h2>
            {_status_badge("in_progress")}
        </div>
        <p style="color:var(--text-secondary); font-size:0.9rem; margin-bottom:1.5rem;">
            Topic: <strong style="color:#e5e7eb;">{topic}</strong>
        </p>
        <div class="progress-container">
            <div class="progress-track"><div class="progress-bar pulse" style="width: 5%;"></div></div>
        </div>
        {_step_checklist([], "initializing")}
    </div>
    """
    return HTMLResponse(content=html)


@router.get("/html/workflow/{workflow_id}/card", response_class=HTMLResponse)
async def html_workflow_card(workflow_id: str):
    """HTMX: Returns a live-updated workflow status card fragment"""
    workflow = db.get_workflow(workflow_id)
    if not workflow:
        return HTMLResponse(content='<div class="card"><p style="color:var(--error);">Workflow not found.</p></div>')

    wf_status = workflow.get("status", "in_progress")
    current_step = workflow.get("current_step", "")
    progress = workflow.get("progress_percentage", 0.0)
    topic = workflow.get("topic", "")
    completed = workflow.get("completed_steps") or []
    result = workflow.get("result") or ""
    error_details = workflow.get("error_details") or {}

    # Still running — poll every 3s
    if wf_status == "in_progress":
        html = f"""
        <div class="card"
             hx-get="/api/v1/html/workflow/{workflow_id}/card"
             hx-trigger="every 3s"
             hx-swap="outerHTML">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1.5rem;">
                <h2 style="margin:0; font-size:1.1rem;">📡 Agents Working...</h2>
                {_status_badge(wf_status)}
            </div>
            <p style="color:var(--text-secondary); font-size:0.9rem; margin-bottom:1.5rem;">
                Topic: <strong style="color:#e5e7eb;">{topic}</strong>
            </p>
            <div class="progress-container">
                <div class="progress-track">
                    <div class="progress-bar pulse" style="width: {progress}%;"></div>
                </div>
            </div>
            {_step_checklist(completed, current_step)}
        </div>
        """

    # Awaiting approval — show full post with action buttons
    elif wf_status == "awaiting_approval":
        escaped_result = result.replace("<", "&lt;").replace(">", "&gt;")
        html = f"""
        <div class="card">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1.5rem;">
                <h2 style="margin:0; font-size:1.1rem;">🎉 Blueprint Ready!</h2>
                {_status_badge(wf_status)}
            </div>
            <p style="color:var(--text-secondary); font-size:0.85rem; margin-bottom:0.5rem;">
                Topic: <strong style="color:#e5e7eb;">{topic}</strong>
            </p>
            <div class="progress-container">
                <div class="progress-track"><div class="progress-bar" style="width:100%;"></div></div>
            </div>
            {_step_checklist(["research_strategy","content_production","finalization"], "completed")}
            <div class="post-output-box">{escaped_result}</div>
            <div class="action-row" id="action-row-{workflow_id}">
                <button class="btn"
                    hx-post="/api/v1/html/workflow/{workflow_id}/approve"
                    hx-vals='{{"action":"approve"}}'
                    hx-target="#action-row-{workflow_id}"
                    hx-swap="outerHTML">
                    ✅ Approve & Publish
                </button>
                <button class="btn btn-sec"
                    hx-post="/api/v1/html/workflow/{workflow_id}/approve"
                    hx-vals='{{"action":"reject"}}'
                    hx-target="#action-row-{workflow_id}"
                    hx-swap="outerHTML">
                    ❌ Reject
                </button>
            </div>
        </div>
        """

    # Error state
    elif wf_status == "error":
        err_msg = error_details.get("message", current_step) if error_details else current_step
        html = f"""
        <div class="card">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem;">
                <h2 style="margin:0; font-size:1.1rem;">Workflow Failed</h2>
                {_status_badge("error")}
            </div>
            <p style="color:var(--text-secondary); font-size:0.9rem; margin-bottom:1rem;">
                Topic: <strong style="color:#e5e7eb;">{topic}</strong>
            </p>
            <div style="background:rgba(239,68,68,0.08); border:1px solid rgba(239,68,68,0.2); border-radius:8px; padding:1rem; color:#f87171; font-size:0.875rem;">
                {err_msg}
            </div>
        </div>
        """

    # Approved / Rejected / Complete states
    else:
        label_map = {"approved": "✅ Blueprint Approved", "rejected": "❌ Rejected", "modification_requested": "✏️ Modification Requested"}
        label = label_map.get(wf_status, wf_status.replace("_", " ").title())
        escaped_result = result.replace("<", "&lt;").replace(">", "&gt;") if result else ""
        html = f"""
        <div class="card">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1.5rem;">
                <h2 style="margin:0; font-size:1.1rem;">{label}</h2>
                {_status_badge(wf_status)}
            </div>
            <p style="color:var(--text-secondary); font-size:0.85rem; margin-bottom:1rem;">
                Topic: <strong style="color:#e5e7eb;">{topic}</strong>
            </p>
            {"<div class='post-output-box'>" + escaped_result + "</div>" if escaped_result else ""}
        </div>
        """

    return HTMLResponse(content=html)


@router.post("/html/workflow/{workflow_id}/approve", response_class=HTMLResponse)
async def html_approve_workflow(
    workflow_id: str,
    action: str = Form(...),
    feedback: Optional[str] = Form(None),
):
    """HTMX: Approve or reject a workflow and return a success fragment"""
    workflow = db.get_workflow(workflow_id)
    if not workflow:
        return HTMLResponse('<p style="color:var(--error);">Workflow not found.</p>')

    if action == "approve":
        db.update_workflow(workflow_id, status="approved")
        return HTMLResponse(content="""
        <div style="text-align:center; padding:1.5rem 0; color:var(--success);">
            <div style="font-size:2rem; margin-bottom:0.5rem;">✅</div>
            <p style="font-weight:600; font-size:1rem;">Blueprint approved and queued for publishing!</p>
        </div>
        """)
    elif action == "reject":
        db.update_workflow(workflow_id, status="rejected")
        return HTMLResponse(content="""
        <div style="text-align:center; padding:1.5rem 0; color:var(--error);">
            <div style="font-size:2rem; margin-bottom:0.5rem;">❌</div>
            <p style="font-weight:600; font-size:1rem;">Blueprint rejected.</p>
        </div>
        """)
    else:
        db.update_workflow(workflow_id, status="modification_requested")
        return HTMLResponse(content="""
        <div style="text-align:center; padding:1.5rem 0; color:var(--warning);">
            <div style="font-size:2rem; margin-bottom:0.5rem;">✏️</div>
            <p style="font-weight:600; font-size:1rem;">Modification request noted.</p>
        </div>
        """)


@router.get("/html/workflows/list", response_class=HTMLResponse)
async def html_workflows_list():
    """HTMX: Returns the sidebar history list of past workflows"""
    workflows = db.list_workflows()
    if not workflows:
        return HTMLResponse('<div class="empty-state">No blueprints generated yet.</div>')

    items = ""
    for wf in workflows[:20]:  # Show latest 20
        wf_id = wf["workflow_id"]
        topic = wf.get("topic", "Untitled")[:40]
        created = wf.get("created_at", "")[:10]
        wf_status = wf.get("status", "")
        badge = _status_badge(wf_status)
        items += f"""
        <div class="history-item"
             hx-get="/api/v1/html/workflow/{wf_id}/card"
             hx-target="#active-workflow-container"
             hx-swap="innerHTML">
            <div class="history-details">
                <span class="history-topic" title="{topic}">{topic}</span>
                <span class="history-time">🗓️ {created}</span>
            </div>
            {badge}
        </div>
        """

    return HTMLResponse(f'<div class="history-list">{items}</div>')
