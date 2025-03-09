# models/policy.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON
from sqlalchemy.sql import func
import enum
from typing import List, Dict, Any, Optional
from datetime import datetime

from models.db import Base

class PolicyModel(Base):
    """SQLAlchemy model for compliance policies"""
    __tablename__ = "policies"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    active = Column(Boolean, default=True)
    required_tags = Column(JSON, nullable=False)  # List of required tags with validation rules
    resource_types = Column(JSON, nullable=True)  # Optional list of applicable resource types
    cloud_providers = Column(JSON, nullable=True)  # Optional list of applicable cloud providers
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Policy:
    """Business model for compliance policies"""
    
    def __init__(
        self,
        id: int,
        name: str,
        description: Optional[str],
        active: bool,
        required_tags: List[Dict[str, Any]],
        resource_types: Optional[List[str]] = None,
        cloud_providers: Optional[List[str]] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        self.id = id
        self.name = name
        self.description = description
        self.active = active
        self.required_tags = required_tags
        self.resource_types = resource_types
        self.cloud_providers = cloud_providers
        self.created_at = created_at
        self.updated_at = updated_at
    
    @classmethod
    def from_model(cls, model: PolicyModel) -> 'Policy':
        """Convert SQLAlchemy model to business model"""
        return cls(
            id=model.id,
            name=model.name,
            description=model.description,
            active=model.active,
            required_tags=model.required_tags,
            resource_types=model.resource_types,
            cloud_providers=model.cloud_providers,
            created_at=model.created_at,
            updated_at=model.updated_at
        )