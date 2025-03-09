# api/routes/workflows.py
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import Dict, List, Optional
from pydantic import BaseModel
from datetime import datetime

from models.db import get_db
from models.workflow import WorkflowModel, Workflow, WorkflowStatus, WorkflowType
from core.compliance.engine import ComplianceEngine

router = APIRouter()
compliance_engine = ComplianceEngine()

class WorkflowCreate(BaseModel):
    resource_id: str
    workflow_type: str
    details: Optional[Dict] = None
    created_by: Optional[str] = None

class WorkflowUpdate(BaseModel):
    status: Optional[str] = None
    approved_by: Optional[str] = None
    details: Optional[Dict] = None

class RemediationApproval(BaseModel):
    approved_tags: Dict[str, str]
    approved_by: Optional[str] = None

class RemediationRejection(BaseModel):
    reason: str
    rejected_by: Optional[str] = None

@router.post("/")
async def create_workflow(workflow: WorkflowCreate, db: Session = Depends(get_db)):
    """
    Create a new workflow
    
    Args:
        workflow: Workflow data
        db: Database session
        
    Returns:
        Created workflow
    """
    try:
        workflow_type = WorkflowType(workflow.workflow_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid workflow type: {workflow.workflow_type}")
    
    db_workflow = WorkflowModel(
        resource_id=workflow.resource_id,
        workflow_type=workflow_type,
        status=WorkflowStatus.PENDING,
        details=workflow.details,
        created_by=workflow.created_by
    )
    
    db.add(db_workflow)
    db.commit()
    db.refresh(db_workflow)
    
    return Workflow.from_model(db_workflow)

@router.get("/")
async def list_workflows(
    status: Optional[str] = None,
    workflow_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    List workflows with filtering options
    
    Args:
        status: Filter by workflow status
        workflow_type: Filter by workflow type
        resource_id: Filter by resource ID
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        db: Database session
        
    Returns:
        List of workflows
    """
    query = db.query(WorkflowModel)
    
    # Apply filters
    if status:
        try:
            status_enum = WorkflowStatus(status)
            query = query.filter(WorkflowModel.status == status_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid workflow status: {status}")
    
    if workflow_type:
        try:
            type_enum = WorkflowType(workflow_type)
            query = query.filter(WorkflowModel.workflow_type == type_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid workflow type: {workflow_type}")
    
    if resource_id:
        query = query.filter(WorkflowModel.resource_id == resource_id)
    
    workflows = query.offset(skip).limit(limit).all()
    return [Workflow.from_model(w) for w in workflows]

@router.get("/{workflow_id}")
async def get_workflow(workflow_id: int, db: Session = Depends(get_db)):
    """
    Get a specific workflow
    
    Args:
        workflow_id: Workflow ID
        db: Database session
        
    Returns:
        Workflow details
    """
    workflow = db.query(WorkflowModel).filter(WorkflowModel.id == workflow_id).first()
    
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    return Workflow.from_model(workflow)

@router.put("/{workflow_id}")
async def update_workflow(
    workflow_id: int,
    workflow_update: WorkflowUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a workflow
    
    Args:
        workflow_id: Workflow ID
        workflow_update: Workflow update data
        db: Database session
        
    Returns:
        Updated workflow
    """
    db_workflow = db.query(WorkflowModel).filter(WorkflowModel.id == workflow_id).first()
    
    if not db_workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # Handle status update
    if workflow_update.status:
        try:
            status_enum = WorkflowStatus(workflow_update.status)
            db_workflow.status = status_enum
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid workflow status: {workflow_update.status}")
    
    # Update other fields if provided
    if workflow_update.approved_by:
        db_workflow.approved_by = workflow_update.approved_by
    
    if workflow_update.details:
        # Update details, preserving existing keys
        updated_details = db_workflow.details or {}
        updated_details.update(workflow_update.details)
        db_workflow.details = updated_details
    
    db.commit()
    db.refresh(db_workflow)
    
    return Workflow.from_model(db_workflow)

@router.post("/{workflow_id}/approve")
async def approve_remediation(
    workflow_id: int,
    approval: RemediationApproval,
    db: Session = Depends(get_db)
):
    """
    Approve and execute a remediation workflow
    
    Args:
        workflow_id: Workflow ID
        approval: Approval data with tags
        db: Database session
        
    Returns:
        Approval status
    """
    db_workflow = db.query(WorkflowModel).filter(WorkflowModel.id == workflow_id).first()
    
    if not db_workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    if db_workflow.workflow_type != WorkflowType.REMEDIATION:
        raise HTTPException(status_code=400, detail="Workflow is not a remediation workflow")
    
    if db_workflow.status != WorkflowStatus.PENDING:
        raise HTTPException(status_code=400, detail="Workflow is not in pending status")
    
    # Apply the remediation
    try:
        success = compliance_engine.approve_remediation(workflow_id, approval.approved_tags)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to apply remediation")
        
        return {
            "status": "success",
            "message": "Remediation approved and applied",
            "workflow_id": workflow_id
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{workflow_id}/reject")
async def reject_remediation(
    workflow_id: int,
    rejection: RemediationRejection,
    db: Session = Depends(get_db)
):
    """
    Reject a remediation workflow
    
    Args:
        workflow_id: Workflow ID
        rejection: Rejection data with reason
        db: Database session
        
    Returns:
        Rejection status
    """
    db_workflow = db.query(WorkflowModel).filter(WorkflowModel.id == workflow_id).first()
    
    if not db_workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    if db_workflow.workflow_type != WorkflowType.REMEDIATION:
        raise HTTPException(status_code=400, detail="Workflow is not a remediation workflow")
    
    if db_workflow.status != WorkflowStatus.PENDING:
        raise HTTPException(status_code=400, detail="Workflow is not in pending status")
    
    # Reject the remediation
    try:
        success = compliance_engine.reject_remediation(workflow_id, rejection.reason)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to reject remediation")
        
        return {
            "status": "success",
            "message": "Remediation rejected",
            "workflow_id": workflow_id
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/stats")
async def get_workflow_stats(db: Session = Depends(get_db)):
    """
    Get workflow statistics
    
    Args:
        db: Database session
        
    Returns:
        Workflow statistics
    """
    # Count by status
    status_counts = {}
    for status in WorkflowStatus:
        count = db.query(WorkflowModel).filter(WorkflowModel.status == status).count()
        status_counts[status.value] = count
    
    # Count by type
    type_counts = {}
    for w_type in WorkflowType:
        count = db.query(WorkflowModel).filter(WorkflowModel.workflow_type == w_type).count()
        type_counts[w_type.value] = count
    
    # Recent workflows
    recent_limit = 5
    recent_workflows = (
        db.query(WorkflowModel)
        .order_by(WorkflowModel.created_at.desc())
        .limit(recent_limit)
        .all()
    )
    
    return {
        "total_workflows": db.query(WorkflowModel).count(),
        "by_status": status_counts,
        "by_type": type_counts,
        "recent_workflows": [Workflow.from_model(w) for w in recent_workflows]
    }