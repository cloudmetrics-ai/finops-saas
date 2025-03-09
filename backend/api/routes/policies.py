# api/routes/policies.py
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import Dict, List, Optional
from pydantic import BaseModel

from models.db import get_db
from models.policy import PolicyModel, Policy
from core.compliance.policy import PolicyManager

router = APIRouter()
policy_manager = PolicyManager()

class TagRule(BaseModel):
    name: str
    required: bool = True
    allowed_values: Optional[List[str]] = None
    default_value: Optional[str] = None

class PolicyCreate(BaseModel):
    name: str
    description: Optional[str] = None
    active: bool = True
    required_tags: List[Dict]
    resource_types: Optional[List[str]] = None
    cloud_providers: Optional[List[str]] = None

class PolicyUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    active: Optional[bool] = None
    required_tags: Optional[List[Dict]] = None
    resource_types: Optional[List[str]] = None
    cloud_providers: Optional[List[str]] = None

@router.post("/")
async def create_policy(policy: PolicyCreate, db: Session = Depends(get_db)):
    """
    Create a new compliance policy
    
    Args:
        policy: Policy data
        db: Database session
        
    Returns:
        Created policy
    """
    try:
        result = policy_manager.create_policy(policy.dict())
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/")
async def list_policies(
    active_only: bool = False,
    skip: int = 0, 
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    List compliance policies
    
    Args:
        active_only: Only return active policies
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        db: Database session
        
    Returns:
        List of policies
    """
    policies = policy_manager.get_policies(active_only)
    
    # Apply pagination
    return policies[skip:skip + limit]

@router.get("/{policy_id}")
async def get_policy(policy_id: int, db: Session = Depends(get_db)):
    """
    Get a specific compliance policy
    
    Args:
        policy_id: Policy ID
        db: Database session
        
    Returns:
        Policy
    """
    policy = policy_manager.get_policy(policy_id)
    
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    return policy

@router.put("/{policy_id}")
async def update_policy(
    policy_id: int,
    policy_update: PolicyUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a compliance policy
    
    Args:
        policy_id: Policy ID
        policy_update: Policy update data
        db: Database session
        
    Returns:
        Updated policy
    """
    try:
        policy = policy_manager.update_policy(policy_id, policy_update.dict(exclude_unset=True))
        
        if not policy:
            raise HTTPException(status_code=404, detail="Policy not found")
        
        return policy
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{policy_id}")
async def delete_policy(policy_id: int, db: Session = Depends(get_db)):
    """
    Delete a compliance policy
    
    Args:
        policy_id: Policy ID
        db: Database session
        
    Returns:
        Deletion status
    """
    success = policy_manager.delete_policy(policy_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    return {"status": "success", "message": f"Policy {policy_id} deleted"}