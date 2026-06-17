from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
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

from utils.llm_setup import setup_crewai_environment

# Set dynamic environment setup before CrewAI routing and imports
setup_crewai_environment()

from api.routes import router

# Create FastAPI app
app = FastAPI(
    title="LinkedIn Post Writer API",
    description="AI-powered LinkedIn post creation using CrewAI",
    version="1.0.0"
)

# Add CORS middleware with restricted origins for production safety
allowed_origins_str = os.getenv("ALLOWED_ORIGINS", "")
if allowed_origins_str:
    allowed_origins = [origin.strip() for origin in allowed_origins_str.split(",") if origin.strip()]
else:
    # Safe fallback: allow all if DEBUG=True, otherwise restrict to standard local ports
    is_debug = os.getenv("DEBUG", "false").lower() == "true"
    allowed_origins = ["*"] if is_debug else ["http://localhost:3000", "http://localhost:8010"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router)

# Mount frontend static files (CSS, JS, assets)
app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")


@app.get("/", include_in_schema=False)
async def root():
    """Serve the HTMX dashboard frontend"""
    return FileResponse("frontend/index.html")


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