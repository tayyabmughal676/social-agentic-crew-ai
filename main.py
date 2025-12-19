from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys
import os
import logging
from datetime import datetime

# Add current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('storage/logs/server.log')
    ]
)

# Set dummy OPENAI_API_KEY before CrewAI imports
if not os.getenv("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = "sk-not-used-using-groq-instead"

from api.routes import router

# Create FastAPI app
app = FastAPI(
    title="LinkedIn Post Writer API",
    description="AI-powered LinkedIn post creation using CrewAI",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "LinkedIn Post Writer API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "create_post": "/api/v1/create-post",
            "workflow_status": "/api/v1/workflow/{workflow_id}",
            "approve_workflow": "/api/v1/workflow/{workflow_id}/approve",
            "list_workflows": "/api/v1/workflows"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8010, reload=True)