# models/workflow.py
from sqlalchemy import Column, Integer, String, DateTime, JSON, Enum, ForeignKey
from sqlalchemy.sql import func
import enum
from typing import Dict, Optional, Any
from datetime import datetime

from models.db import Base

class WorkflowType(enum.Enum):
    """Enumeration of workflow types"""
    REMEDIATION = "remediation"
    EXEMPTION = "exemption"

class WorkflowStatus(enum.Enum):
    """Enumeration of workflow statuses"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class WorkflowModel(Base):
    """SQLAlchemy model for compliance workflows"""
    __tablename__ = "workflows"
    
    id = Column(Integer, primary_key=True, index=True)
    resource_id = Column(String, nullable=False, index=True)
    workflow_type = Column(Enum(WorkflowType), nullable=False)
    status = Column(Enum(WorkflowStatus), default=WorkflowStatus.PENDING)
    details = Column(JSON, nullable=True)
    created_by = Column(String, nullable=True)
    approved_by = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

class Workflow:
    """Business model for compliance workflows"""
    
    def __init__(
        self,
        id: Optional[int],
        resource_id: str,
        workflow_type: WorkflowType,
        status: WorkflowStatus,
        details: Optional[Dict[str, Any]] = None,
        created_by: Optional[str] = None,
        approved_by: Optional[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None
    ):
        self.id = id
        self.resource_id = resource_id
        self.workflow_type = workflow_type
        self.status = status
        self.details = details or {}
        self.created_by = created_by
        self.approved_by = approved_by
        self.created_at = created_at
        self.updated_at = updated_at
        self.completed_at = completed_at
    
    @classmethod
    def from_model(cls, model: WorkflowModel) -> 'Workflow':
        """Convert SQLAlchemy model to business model"""
        return cls(
            id=model.id,
            resource_id=model.resource_id,
            workflow_type=model.workflow_type,
            status=model.status,
            details=model.details,
            created_by=model.created_by,
            approved_by=model.approved_by,
            created_at=model.created_at,
            updated_at=model.updated_at,
            completed_at=model.completed_at
        )