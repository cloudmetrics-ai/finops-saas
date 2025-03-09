# cloud/azure/connector.py
import logging
from typing import Dict, List, Any, Optional

from azure.identity import DefaultAzureCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.storage import StorageManagementClient
from azure.core.exceptions import AzureError

from models.resource import Resource, ComplianceStatus

logger = logging.getLogger(__name__)

class AzureConnector:
    """Connector for Azure cloud resources"""
    
    def __init__(self):
        self.credential = DefaultAzureCredential()
        self.subscription_id = self._get_subscription_id()
        self.supported_resource_types = {
            'vm': self._get_virtual_machines,
            'storage-account': self._get_storage_accounts,
        }
        
    def _get_subscription_id(self) -> str:
        """Get the Azure subscription ID from environment variables"""
        import os
        subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID")
        if not subscription_id:
            logger.warning("AZURE_SUBSCRIPTION_ID not set, using default subscription")
            # In a real implementation, you might fetch the default subscription
            # For now, we'll use a placeholder
            subscription_id = "00000000-0000-0000-0000-000000000000"
        return subscription_id
    
    def list_resources(self) -> List[Resource]:
        """
        List all supported Azure resources
        
        Returns:
            List of Resource objects
        """
        resources = []
        
        for resource_type, resource_fetcher in self.supported_resource_types.items():
            try:
                type_resources = resource_fetcher()
                resources.extend(type_resources)
            except Exception as e:
                logger.error(f"Error fetching {resource_type} resources: {str(e)}")
        
        return resources
    
    def _get_virtual_machines(self) -> List[Resource]:
        """Get Azure virtual machines"""
        resources = []
        
        try:
            # Create Azure clients
            compute_client = ComputeManagementClient(self.credential, self.subscription_id)
            resource_client = ResourceManagementClient(self.credential, self.subscription_id)
            
            # Get all resource groups
            resource_groups = resource_client.resource_groups.list()
            
            # Iterate through each resource group
            for resource_group in resource_groups:
                rg_name = resource_group.name
                
                # Get all VMs in the resource group
                vms = compute_client.virtual_machines.list(rg_name)
                
                for vm in vms:
                    vm_id = vm.id
                    vm_name = vm.name
                    vm_location = vm.location
                    
                    # Get VM tags
                    tags = vm.tags or {}
                    
                    resource = Resource(
                        resource_id=vm_id,
                        name=vm_name,
                        resource_type='vm',
                        cloud_provider='azure',
                        region=vm_location,
                        tags=tags,
                        compliance_status=ComplianceStatus.UNKNOWN
                    )
                    resources.append(resource)
        
        except AzureError as e:
            logger.error(f"Azure error getting VMs: {str(e)}")
        except Exception as e:
            logger.error(f"Error getting VMs: {str(e)}")
        
        return resources
    
    def _get_storage_accounts(self) -> List[Resource]:
        """Get Azure storage accounts"""
        resources = []
        
        try:
            # Create Azure clients
            storage_client = StorageManagementClient(self.credential, self.subscription_id)
            
            # Get all storage accounts
            storage_accounts = storage_client.storage_accounts.list()
            
            for storage_account in storage_accounts:
                account_id = storage_account.id
                account_name = storage_account.name
                account_location = storage_account.location
                
                # Get storage account tags
                tags = storage_account.tags or {}
                
                resource = Resource(
                    resource_id=account_id,
                    name=account_name,
                    resource_type='storage-account',
                    cloud_provider='azure',
                    region=account_location,
                    tags=tags,
                    compliance_status=ComplianceStatus.UNKNOWN
                )
                resources.append(resource)
        
        except AzureError as e:
            logger.error(f"Azure error getting storage accounts: {str(e)}")
        except Exception as e:
            logger.error(f"Error getting storage accounts: {str(e)}")
        
        return resources
    
    def update_resource_tags(self, resource_id: str, tags: Dict[str, str]) -> bool:
        """
        Update tags for a specified Azure resource
        
        Args:
            resource_id: Azure resource ID
            tags: Dict of tag keys and values to apply
            
        Returns:
            Boolean indicating success
        """
        try:
            # Create Azure client
            resource_client = ResourceManagementClient(self.credential, self.subscription_id)
            
            # Get current resource
            api_version = "2021-04-01"  # Update with appropriate API version
            resource_info = resource_client.resources.get_by_id(resource_id, api_version)
            
            # Merge existing tags with new tags
            existing_tags = resource_info.tags or {}
            merged_tags = {**existing_tags, **tags}
            
            # Update resource tags
            # Note: This is a generic approach. For specific resource types,
            # using the specific client (like ComputeManagementClient for VMs)
            # might be more appropriate.
            resource_client.resources.begin_update_by_id(
                resource_id=resource_id,
                api_version=api_version,
                parameters={'tags': merged_tags}
            )
            
            return True
            
        except AzureError as e:
            logger.error(f"Azure error updating tags for {resource_id}: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error updating tags for {resource_id}: {str(e)}")
            return False