# app.py
"""
Main application entry point for the Cloud Resource Tagging Compliance API.
"""
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
import os

from api.routes import compliance, policies, resources, workflows
from models.db import get_db, init_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Cloud Resource Tagging Compliance API",
    description="API for managing cloud resource tagging compliance across multiple cloud providers.",
    version="1.0.0"
)

# Configure CORS
origins = [
    "http://localhost",
    "http://localhost:3000",  # React development server
    "http://localhost:8080",
]

if os.getenv("CORS_ORIGINS"):
    origins.extend(os.getenv("CORS_ORIGINS").split(","))

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(compliance.router, prefix="/api/compliance", tags=["Compliance"])
app.include_router(policies.router, prefix="/api/policies", tags=["Policies"])
app.include_router(resources.router, prefix="/api/resources", tags=["Resources"])
app.include_router(workflows.router, prefix="/api/workflows", tags=["Workflows"])

@app.on_event("startup")
def startup_event():
    """Initialize database and perform startup tasks"""
    logger.info("Starting application")
    init_db()
    logger.info("Database initialized")

@app.get("/health", tags=["Health"])
def health_check():
    """Check application health"""
    return {"status": "healthy"}

if __name__ == "__main__":
    # Get host and port from environment or use defaults
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    
    # Run application with uvicorn
    uvicorn.run("app:app", host=host, port=port, reload=True)