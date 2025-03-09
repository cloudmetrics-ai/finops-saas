# models/resource.py
from sqlalchemy import Column, Integer, String, DateTime, JSON, Enum
from sqlalchemy.sql import func
import enum
from typing import Dict, Optional
from datetime import datetime

from models.db import Base

class ComplianceStatus(enum.Enum):
    """Enumeration of possible compliance statuses"""
    UNKNOWN = "unknown"
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    EXEMPT = "exempt"

class ResourceModel(Base):
    """SQLAlchemy model for cloud resources"""
    __tablename__ = "resources"
    
    id = Column(Integer, primary_key=True, index=True)
    resource_id = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    resource_type = Column(String, nullable=False)
    cloud_provider = Column(String, nullable=False)
    region = Column(String, nullable=False)
    tags = Column(JSON, nullable=False, default={})
    compliance_status = Column(Enum(ComplianceStatus), default=ComplianceStatus.UNKNOWN)
    compliance_details = Column(JSON, nullable=True)
    last_checked = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Resource:
    """Business model for cloud resources"""
    
    def __init__(
        self,
        resource_id: str,
        name: str,
        resource_type: str,
        cloud_provider: str,
        region: str,
        tags: Dict[str, str],
        compliance_status: ComplianceStatus = ComplianceStatus.UNKNOWN,
        compliance_details: Optional[Dict] = None,
        last_checked: Optional[datetime] = None,
        id: Optional[int] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        self.id = id
        self.resource_id = resource_id
        self.name = name
        self.resource_type = resource_type
        self.cloud_provider = cloud_provider
        self.region = region
        self.tags = tags or {}
        self.compliance_status = compliance_status
        self.compliance_details = compliance_details or {}
        self.last_checked = last_checked
        self.created_at = created_at
        self.updated_at = updated_at
    
    @classmethod
    def from_model(cls, model: ResourceModel) -> 'Resource':
        """Convert SQLAlchemy model to business model"""
        return cls(
            id=model.id,
            resource_id=model.resource_id,
            name=model.name,
            resource_type=model.resource_type,
            cloud_provider=model.cloud_provider,
            region=model.region,
            tags=model.tags,
            compliance_status=model.compliance_status,
            compliance_details=model.compliance_details,
            last_checked=model.last_checked,
            created_at=model.created_at,
            updated_at=model.updated_at
        )