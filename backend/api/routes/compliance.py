# api/routes/compliance.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, List, Optional
from datetime import datetime

from models.db import get_db
from models.resource import ResourceModel, ComplianceStatus
from core.compliance.engine import ComplianceEngine

router = APIRouter()
compliance_engine = ComplianceEngine()

@router.get("/scan")
async def scan_resources(
    cloud_provider: Optional[str] = None, 
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """
    Scan cloud resources for compliance
    
    Args:
        cloud_provider: Optional cloud provider to scan (aws, azure, gcp)
        background_tasks: FastAPI background tasks
        db: Database session
        
    Returns:
        Dict with scan status
    """
    if background_tasks:
        # Run scan in background
        background_tasks.add_task(compliance_engine.scan_resources, cloud_provider)
        return {"status": "success", "message": "Scan started in background"}
    else:
        # Run scan immediately
        resources = compliance_engine.scan_resources(cloud_provider)
        return {
            "status": "success", 
            "message": f"Scanned {len(resources)} resources"
        }

@router.get("/evaluate")
async def evaluate_compliance(
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """
    Evaluate compliance for all resources
    
    Args:
        background_tasks: FastAPI background tasks
        db: Database session
        
    Returns:
        Dict with evaluation status
    """
    if background_tasks:
        # Run evaluation in background
        background_tasks.add_task(compliance_engine.evaluate_all_resources)
        return {"status": "success", "message": "Evaluation started in background"}
    else:
        # Run evaluation immediately
        results = compliance_engine.evaluate_all_resources()
        return {
            "status": "success",
            "results": results
        }

@router.get("/status")
async def get_compliance_status(db: Session = Depends(get_db)):
    """
    Get overall compliance status
    
    Args:
        db: Database session
        
    Returns:
        Dict with compliance statistics
    """
    total = db.query(ResourceModel).count()
    compliant = db.query(ResourceModel).filter(ResourceModel.compliance_status == ComplianceStatus.COMPLIANT).count()
    non_compliant = db.query(ResourceModel).filter(ResourceModel.compliance_status == ComplianceStatus.NON_COMPLIANT).count()
    unknown = db.query(ResourceModel).filter(ResourceModel.compliance_status == ComplianceStatus.UNKNOWN).count()
    exempt = db.query(ResourceModel).filter(ResourceModel.compliance_status == ComplianceStatus.EXEMPT).count()
    
    return {
        "total_resources": total,
        "compliant": compliant,
        "non_compliant": non_compliant,
        "unknown": unknown,
        "exempt": exempt,
        "compliance_rate": (compliant / total) * 100 if total > 0 else 0
    }