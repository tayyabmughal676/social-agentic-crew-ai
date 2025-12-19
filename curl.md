# LinkedIn Post Writer API - Curl Examples

This guide provides `curl` commands to interact with the API endpoints.

**Base URL**: `http://localhost:8010`

## 1. Create a LinkedIn Post

Start a new workflow to generate a LinkedIn post.

```bash
curl -X POST "http://localhost:8010/api/v1/create-post" \
     -H "Content-Type: application/json" \
     -d '{
           "topic": "The Impact of AI Agents on Software Development",
           "urgency": "normal",
           "target_audience": "Tech Leads and CTOs",
           "tone": "thought-leadership",
           "include_hashtags": true,
           "post_length": "medium"
         }'
```

**Response**:
```json
{
  "workflow_id": "9ad6f5a5-a589-434b-9fa6-351be6a7080f",
  "status": "in_progress",
  "topic": "The Impact of AI Agents on Software Development",
  ...
}
```

## 2. Check Workflow Status

Poll the status of a specific workflow using the `workflow_id` returned from the previous step.

```bash
# Replace <WORKFLOW_ID> with your actual ID
curl "http://localhost:8010/api/v1/workflow/<WORKFLOW_ID>"
```

**Response**:
```json
{
  "workflow_id": "...",
  "status": "in_progress",
  "current_step": "research",
  "progress_percentage": 15,
  ...
}
```

## 3. Approve a Workflow

When the workflow status is `awaiting_approval` (usually after the review step), you can approve it to proceed.

```bash
curl -X POST "http://localhost:8010/api/v1/workflow/<WORKFLOW_ID>/approve" \
     -H "Content-Type: application/json" \
     -d '{
           "action": "approve",
           "feedback": "Looks good, proceed!"
         }'
```

## 4. List All Workflows

Get a history of all workflows.

```bash
curl "http://localhost:8010/api/v1/workflows"
```

## 5. Health Check

Verify the API is running.

```bash
curl "http://localhost:8010/"
```
