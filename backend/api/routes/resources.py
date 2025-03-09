# api/routes/resources.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, List, Optional
from datetime import datetime

from models.db import get_db
from models.resource import ResourceModel, Resource, ComplianceStatus

router = APIRouter()

@router.get("/")
async def list_resources(
    cloud_provider: Optional[str] = None,
    resource_type: Optional[str] = None,
    compliance_status: Optional[str] = None,
    region: Optional[str] = None,
    has_tag: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    List cloud resources with filtering options
    
    Args:
        cloud_provider: Filter by cloud provider
        resource_type: Filter by resource type
        compliance_status: Filter by compliance status
        region: Filter by region
        has_tag: Filter for resources having a specific tag
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        db: Database session
        
    Returns:
        List of resources
    """
    query = db.query(ResourceModel)
    
    # Apply filters
    if cloud_provider:
        query = query.filter(ResourceModel.cloud_provider == cloud_provider)
    
    if resource_type:
        query = query.filter(ResourceModel.resource_type == resource_type)
    
    if compliance_status:
        try:
            status = ComplianceStatus(compliance_status)
            query = query.filter(ResourceModel.compliance_status == status)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid compliance status: {compliance_status}")
    
    if region:
        query = query.filter(ResourceModel.region == region)
    
    # Handle tag filtering (more complex)
    if has_tag:
        # This requires PostgreSQL JSON operators, adjust if using a different database
        query = query.filter(ResourceModel.tags.has_key(has_tag))
    
    resources = query.offset(skip).limit(limit).all()
    return [Resource.from_model(r) for r in resources]

@router.get("/{resource_id}")
async def get_resource(resource_id: str, db: Session = Depends(get_db)):
    """
    Get a specific resource by ID
    
    Args:
        resource_id: Resource ID
        db: Database session
        
    Returns:
        Resource details
    """
    resource = db.query(ResourceModel).filter(ResourceModel.resource_id == resource_id).first()
    
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    
    return Resource.from_model(resource)

@router.get("/stats")
async def get_resource_stats(db: Session = Depends(get_db)):
    """
    Get resource statistics
    
    Args:
        db: Database session
        
    Returns:
        Resource statistics
    """
    # Count by cloud provider
    provider_counts = {}
    for provider in ["aws", "azure", "gcp"]:
        count = db.query(ResourceModel).filter(ResourceModel.cloud_provider == provider).count()
        provider_counts[provider] = count
    
    # Count by resource type
    resource_type_counts = {}
    resource_types = db.query(ResourceModel.resource_type).distinct().all()
    for r_type in resource_types:
        count = db.query(ResourceModel).filter(ResourceModel.resource_type == r_type[0]).count()
        resource_type_counts[r_type[0]] = count
    
    # Count by compliance status
    status_counts = {}
    for status in ComplianceStatus:
        count = db.query(ResourceModel).filter(ResourceModel.compliance_status == status).count()
        status_counts[status.value] = count
    
    # Most common missing tags
    missing_tags_stats = {}
    # This would require custom SQL or complex ORM queries with JSON functions
    # Simplified approach for demonstration:
    non_compliant = db.query(ResourceModel).filter(ResourceModel.compliance_status == ComplianceStatus.NON_COMPLIANT).all()
    tag_issues = {}
    
    for resource in non_compliant:
        if resource.compliance_details and "missing_tags" in resource.compliance_details:
            for missing_tag in resource.compliance_details["missing_tags"]:
                tag_name = missing_tag["tag_name"]
                if tag_name not in tag_issues:
                    tag_issues[tag_name] = 0
                tag_issues[tag_name] += 1
    
    return {
        "total_resources": db.query(ResourceModel).count(),
        "by_provider": provider_counts,
        "by_resource_type": resource_type_counts,
        "by_compliance_status": status_counts,
        "common_tag_issues": tag_issues
    }

@router.get("/types")
async def get_resource_types(db: Session = Depends(get_db)):
    """
    Get list of available resource types
    
    Args:
        db: Database session
        
    Returns:
        List of resource types
    """
    resource_types = db.query(ResourceModel.resource_type).distinct().all()
    return [r_type[0] for r_type in resource_types]

@router.get("/regions")
async def get_regions(
    cloud_provider: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get list of available regions
    
    Args:
        cloud_provider: Optional cloud provider filter
        db: Database session
        
    Returns:
        List of regions
    """
    query = db.query(ResourceModel.region).distinct()
    
    if cloud_provider:
        query = query.filter(ResourceModel.cloud_provider == cloud_provider)
        
    regions = query.all()
    return [region[0] for region in regions]