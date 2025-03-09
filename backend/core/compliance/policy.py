# core/compliance/policy.py
"""
Policy management module for handling tagging compliance policies.
"""
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime

from models.db import get_db
from models.policy import Policy, PolicyModel

logger = logging.getLogger(__name__)

class PolicyManager:
    """Manager for compliance policies"""
    
    def get_policies(self, active_only: bool = False) -> List[Policy]:
        """
        Get all policies
        
        Args:
            active_only: Only return active policies
            
        Returns:
            List of Policy objects
        """
        db = next(get_db())
        query = db.query(PolicyModel)
        
        if active_only:
            query = query.filter(PolicyModel.active == True)
        
        policy_models = query.all()
        return [Policy.from_model(p) for p in policy_models]
    
    def get_policy(self, policy_id: int) -> Optional[Policy]:
        """
        Get a specific policy by ID
        
        Args:
            policy_id: Policy ID
            
        Returns:
            Policy object or None if not found
        """
        db = next(get_db())
        policy_model = db.query(PolicyModel).filter(PolicyModel.id == policy_id).first()
        
        if not policy_model:
            return None
        
        return Policy.from_model(policy_model)
    
    def create_policy(self, policy_data: Dict[str, Any]) -> Policy:
        """
        Create a new policy
        
        Args:
            policy_data: Dict with policy data
            
        Returns:
            Created Policy object
        """
        db = next(get_db())
        
        # Validate required tags format
        self._validate_required_tags(policy_data.get("required_tags", []))
        
        # Create policy model
        policy_model = PolicyModel(
            name=policy_data["name"],
            description=policy_data.get("description"),
            active=policy_data.get("active", True),
            required_tags=policy_data["required_tags"],
            resource_types=policy_data.get("resource_types"),
            cloud_providers=policy_data.get("cloud_providers")
        )
        
        db.add(policy_model)
        db.commit()
        db.refresh(policy_model)
        
        return Policy.from_model(policy_model)
    
    def update_policy(self, policy_id: int, policy_data: Dict[str, Any]) -> Optional[Policy]:
        """
        Update an existing policy
        
        Args:
            policy_id: Policy ID
            policy_data: Dict with updated policy data
            
        Returns:
            Updated Policy object or None if not found
        """
        db = next(get_db())
        policy_model = db.query(PolicyModel).filter(PolicyModel.id == policy_id).first()
        
        if not policy_model:
            return None
        
        # Validate required tags if provided
        if "required_tags" in policy_data:
            self._validate_required_tags(policy_data["required_tags"])
        
        # Update fields
        for key, value in policy_data.items():
            if hasattr(policy_model, key):
                setattr(policy_model, key, value)
        
        db.commit()
        db.refresh(policy_model)
        
        return Policy.from_model(policy_model)
    
    def delete_policy(self, policy_id: int) -> bool:
        """
        Delete a policy
        
        Args:
            policy_id: Policy ID
            
        Returns:
            Boolean indicating success
        """
        db = next(get_db())
        policy_model = db.query(PolicyModel).filter(PolicyModel.id == policy_id).first()
        
        if not policy_model:
            return False
        
        db.delete(policy_model)
        db.commit()
        
        return True
    
    def _validate_required_tags(self, required_tags: List[Dict[str, Any]]) -> None:
        """
        Validate the required tags format
        
        Args:
            required_tags: List of required tag dictionaries
            
        Raises:
            ValueError: If the required tags format is invalid
        """
        if not isinstance(required_tags, list):
            raise ValueError("required_tags must be a list")
        
        for tag in required_tags:
            if not isinstance(tag, dict):
                raise ValueError("Each required tag must be a dictionary")
            
            if "name" not in tag:
                raise ValueError("Each required tag must have a 'name' field")
            
            if "allowed_values" in tag and tag["allowed_values"] is not None:
                if not isinstance(tag["allowed_values"], list):
                    raise ValueError("allowed_values must be a list")