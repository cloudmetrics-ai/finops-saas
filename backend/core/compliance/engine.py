# core/compliance/engine.py
"""
Core compliance engine for evaluating and enforcing tag compliance across cloud providers.
"""
from typing import Dict, List, Optional, Tuple, Any
import logging
from datetime import datetime

from models.db import get_db
from models.policy import Policy, PolicyModel
from models.resource import Resource, ResourceModel, ComplianceStatus
from models.workflow import Workflow, WorkflowModel, WorkflowStatus, WorkflowType
from cloud.aws.connector import AWSConnector
from cloud.azure.connector import AzureConnector
from cloud.gcp.connector import GCPConnector

logger = logging.getLogger(__name__)

class ComplianceEngine:
    """Core engine for evaluating and enforcing tag compliance across cloud providers"""
    
    def __init__(self):
        self.aws_connector = AWSConnector()
        self.azure_connector = AzureConnector()
        self.gcp_connector = GCPConnector()
        
    def get_connector_for_provider(self, cloud_provider: str):
        """Returns the appropriate cloud connector based on provider name"""
        if cloud_provider.lower() == "aws":
            return self.aws_connector
        elif cloud_provider.lower() == "azure":
            return self.azure_connector
        elif cloud_provider.lower() == "gcp":
            return self.gcp_connector
        else:
            raise ValueError(f"Unsupported cloud provider: {cloud_provider}")
    
    def scan_resources(self, cloud_provider: str = None) -> List[Resource]:
        """
        Scan resources across specified cloud provider or all providers
        
        Args:
            cloud_provider: Optional provider to scan (aws, azure, gcp). If None, scan all.
            
        Returns:
            List of Resource objects representing cloud resources
        """
        resources = []
        
        if cloud_provider:
            # Scan specific provider
            connector = self.get_connector_for_provider(cloud_provider)
            provider_resources = connector.list_resources()
            resources.extend(provider_resources)
        else:
            # Scan all providers
            for provider in ["aws", "azure", "gcp"]:
                try:
                    connector = self.get_connector_for_provider(provider)
                    provider_resources = connector.list_resources()
                    resources.extend(provider_resources)
                except Exception as e:
                    logger.error(f"Error scanning {provider}: {str(e)}")
        
        # Save resources to database
        db = next(get_db())
        for resource in resources:
            db_resource = ResourceModel(
                resource_id=resource.resource_id,
                name=resource.name,
                resource_type=resource.resource_type,
                cloud_provider=resource.cloud_provider,
                region=resource.region,
                tags=resource.tags,
                compliance_status=resource.compliance_status,
                last_checked=datetime.utcnow()
            )
            db.merge(db_resource)
        db.commit()
        
        return resources
    
    def evaluate_compliance(self, resource: Resource, policies: List[Policy]) -> Tuple[bool, Dict[str, Any]]:
        """
        Evaluate if a resource complies with the given policies
        
        Args:
            resource: Resource to evaluate
            policies: List of policies to check against
            
        Returns:
            Tuple of (is_compliant: bool, issues: Dict)
        """
        is_compliant = True
        issues = {}
        
        for policy in policies:
            # Skip policies that don't apply to this resource type or provider
            if (policy.resource_types and resource.resource_type not in policy.resource_types) or \
               (policy.cloud_providers and resource.cloud_provider not in policy.cloud_providers):
                continue
                
            # Check required tags
            for required_tag in policy.required_tags:
                tag_name = required_tag["name"]
                if tag_name not in resource.tags:
                    is_compliant = False
                    if "missing_tags" not in issues:
                        issues["missing_tags"] = []
                    issues["missing_tags"].append({
                        "tag_name": tag_name,
                        "policy_id": policy.id,
                        "policy_name": policy.name
                    })
                elif "allowed_values" in required_tag and resource.tags[tag_name] not in required_tag["allowed_values"]:
                    is_compliant = False
                    if "invalid_tag_values" not in issues:
                        issues["invalid_tag_values"] = []
                    issues["invalid_tag_values"].append({
                        "tag_name": tag_name,
                        "current_value": resource.tags[tag_name],
                        "allowed_values": required_tag["allowed_values"],
                        "policy_id": policy.id,
                        "policy_name": policy.name
                    })
        
        return is_compliant, issues
    
    def evaluate_all_resources(self) -> Dict[str, int]:
        """
        Evaluate compliance for all resources against all policies
        
        Returns:
            Dict with compliance statistics
        """
        db = next(get_db())
        resources = db.query(ResourceModel).all()
        policies = db.query(PolicyModel).filter(PolicyModel.active == True).all()
        
        compliant_count = 0
        non_compliant_count = 0
        
        for resource_model in resources:
            resource = Resource(
                resource_id=resource_model.resource_id,
                name=resource_model.name,
                resource_type=resource_model.resource_type,
                cloud_provider=resource_model.cloud_provider,
                region=resource_model.region,
                tags=resource_model.tags,
                compliance_status=resource_model.compliance_status
            )
            
            is_compliant, issues = self.evaluate_compliance(resource, policies)
            
            # Update resource compliance status
            resource_model.compliance_status = ComplianceStatus.COMPLIANT if is_compliant else ComplianceStatus.NON_COMPLIANT
            resource_model.compliance_details = issues if not is_compliant else {}
            resource_model.last_checked = datetime.utcnow()
            
            if is_compliant:
                compliant_count += 1
            else:
                non_compliant_count += 1
                
                # Create remediation workflow if non-compliant
                if issues:
                    workflow = WorkflowModel(
                        resource_id=resource.resource_id,
                        workflow_type=WorkflowType.REMEDIATION,
                        status=WorkflowStatus.PENDING,
                        details={
                            "issues": issues,
                            "suggested_tags": self._generate_suggested_tags(resource, issues)
                        },
                        created_at=datetime.utcnow()
                    )
                    db.add(workflow)
        
        db.commit()
        
        return {
            "total": len(resources),
            "compliant": compliant_count,
            "non_compliant": non_compliant_count,
            "compliance_rate": (compliant_count / len(resources)) * 100 if resources else 0
        }
    
    def approve_remediation(self, workflow_id: int, approved_tags: Dict[str, str]) -> bool:
        """
        Apply approved remediation tags to a resource
        
        Args:
            workflow_id: ID of the remediation workflow
            approved_tags: Dict of tag names and values to apply
            
        Returns:
            Boolean indicating success
        """
        db = next(get_db())
        workflow = db.query(WorkflowModel).filter(WorkflowModel.id == workflow_id).first()
        
        if not workflow or workflow.workflow_type != WorkflowType.REMEDIATION:
            raise ValueError(f"Invalid remediation workflow ID: {workflow_id}")
        
        resource = db.query(ResourceModel).filter(ResourceModel.resource_id == workflow.resource_id).first()
        
        if not resource:
            raise ValueError(f"Resource not found for workflow: {workflow_id}")
        
        # Get the appropriate connector
        connector = self.get_connector_for_provider(resource.cloud_provider)
        
        # Apply the tags
        success = connector.update_resource_tags(resource.resource_id, approved_tags)
        
        if success:
            # Update the resource tags in our database
            resource.tags.update(approved_tags)
            
            # Update workflow status
            workflow.status = WorkflowStatus.COMPLETED
            workflow.completed_at = datetime.utcnow()
            workflow.details["applied_tags"] = approved_tags
            
            # Re-evaluate compliance
            policies = db.query(PolicyModel).filter(PolicyModel.active == True).all()
            resource_obj = Resource(
                resource_id=resource.resource_id,
                name=resource.name,
                resource_type=resource.resource_type,
                cloud_provider=resource.cloud_provider,
                region=resource.region,
                tags=resource.tags,
                compliance_status=resource.compliance_status
            )
            
            is_compliant, issues = self.evaluate_compliance(resource_obj, policies)
            resource.compliance_status = ComplianceStatus.COMPLIANT if is_compliant else ComplianceStatus.NON_COMPLIANT
            resource.compliance_details = issues if not is_compliant else {}
            
            db.commit()
        
        return success
    
    def reject_remediation(self, workflow_id: int, reason: str) -> bool:
        """
        Reject a remediation workflow
        
        Args:
            workflow_id: ID of the remediation workflow
            reason: Reason for rejection
            
        Returns:
            Boolean indicating success
        """
        db = next(get_db())
        workflow = db.query(WorkflowModel).filter(WorkflowModel.id == workflow_id).first()
        
        if not workflow or workflow.workflow_type != WorkflowType.REMEDIATION:
            raise ValueError(f"Invalid remediation workflow ID: {workflow_id}")
        
        # Update workflow status
        workflow.status = WorkflowStatus.REJECTED
        workflow.completed_at = datetime.utcnow()
        workflow.details["rejection_reason"] = reason
        
        db.commit()
        return True
    
    def _generate_suggested_tags(self, resource: Resource, issues: Dict) -> Dict[str, str]:
        """Generate suggested tag values for remediation"""
        suggested_tags = {}
        
        if "missing_tags" in issues:
            for missing_tag in issues["missing_tags"]:
                # Get the policy to check for default values
                db = next(get_db())
                policy = db.query(PolicyModel).filter(PolicyModel.id == missing_tag["policy_id"]).first()
                
                for required_tag in policy.required_tags:
                    if required_tag["name"] == missing_tag["tag_name"]:
                        if "default_value" in required_tag:
                            suggested_tags[missing_tag["tag_name"]] = required_tag["default_value"]
                        elif "allowed_values" in required_tag and required_tag["allowed_values"]:
                            # Suggest the first allowed value
                            suggested_tags[missing_tag["tag_name"]] = required_tag["allowed_values"][0]
                        else:
                            suggested_tags[missing_tag["tag_name"]] = ""