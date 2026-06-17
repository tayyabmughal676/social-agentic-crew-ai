from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class TopicRequest(BaseModel):
    topic: str = Field(..., description="The topic for the LinkedIn post", min_length=1, max_length=200)
    urgency: Optional[str] = Field("normal", description="Urgency level: normal, high, low", max_length=20)
    target_audience: Optional[str] = Field(None, description="Target audience description", max_length=200)
    tone: Optional[str] = Field("professional", description="Tone: professional, casual, inspirational, educational", max_length=100)
    include_hashtags: Optional[bool] = Field(True, description="Whether to include hashtags")
    post_length: Optional[str] = Field("medium", description="Post length: short, medium, long", max_length=50)


class WorkflowResponse(BaseModel):
    workflow_id: Optional[str] = Field(None, description="The workflow ID")
    status: str = Field(..., description="Status of the workflow: success, error, in_progress")
    topic: str = Field(..., description="The original topic")
    result: Optional[str] = Field(None, description="The generated LinkedIn post content")
    error: Optional[str] = Field(None, description="Error message if workflow failed")
    message: str = Field(..., description="General message about the workflow")
    timestamp: datetime = Field(default_factory=datetime.now)


class PostContent(BaseModel):
    content: str = Field(..., description="The main content of the LinkedIn post")
    hashtags: List[str] = Field(default_factory=list, description="List of hashtags")
    mentions: List[str] = Field(default_factory=list, description="List of @mentions")
    media_urls: List[str] = Field(default_factory=list, description="List of media URLs")
    scheduled_time: Optional[datetime] = Field(None, description="Scheduled posting time")
    status: str = Field("draft", description="Post status: draft, reviewed, approved, published")


class WorkflowStatus(BaseModel):
    workflow_id: str = Field(..., description="Unique identifier for the workflow")
    status: str = Field(..., description="Current status of the workflow")
    current_step: str = Field(..., description="Current step being executed")
    completed_steps: List[str] = Field(default_factory=list, description="List of completed steps")
    estimated_completion: Optional[datetime] = Field(None, description="Estimated completion time")
    progress_percentage: float = Field(0.0, description="Progress percentage (0-100)")
    error_details: Optional[Dict[str, Any]] = Field(None, description="Detailed error information if workflow failed")
    result: Optional[str] = Field(None, description="The generated LinkedIn post content / strategy results")
    
    class Config:
        extra = "allow"  # Allow extra fields for flexibility


class ApprovalRequest(BaseModel):
    workflow_id: str = Field(..., description="Workflow ID to approve")
    action: str = Field(..., description="Action: approve, modify, reject")
    feedback: Optional[str] = Field(None, description="Feedback for modifications")
