# cloud/gcp/connector.py
import logging
from typing import Dict, List, Any, Optional
import json
import os

from google.cloud import resourcemanager_v3
from google.cloud import compute_v1
from google.cloud import storage
from google.api_core.exceptions import GoogleAPIError

from models.resource import Resource, ComplianceStatus

logger = logging.getLogger(__name__)

class GCPConnector:
    """Connector for Google Cloud Platform resources"""
    
    def __init__(self):
        # Load credentials from environment variable
        self._setup_credentials()
        
        self.project_id = self._get_project_id()
        self.supported_resource_types = {
            'compute-instance': self._get_compute_instances,
            'storage-bucket': self._get_storage_buckets,
        }
    
    def _setup_credentials(self):
        """Set up GCP credentials from environment"""
        # GCP authentication is usually handled through Application Default Credentials
        # or by setting GOOGLE_APPLICATION_CREDENTIALS environment variable
        creds_json = os.getenv("GCP_SERVICE_ACCOUNT_JSON")
        if creds_json:
            # If credentials are provided as a JSON string, write to a temp file
            try:
                import tempfile
                with tempfile.NamedTemporaryFile(delete=False, mode='w') as temp:
                    temp.write(creds_json)
                    temp_filename = temp.name
                
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = temp_filename
                logger.info("GCP credentials loaded from environment variable")
            except Exception as e:
                logger.error(f"Error setting up GCP credentials: {str(e)}")
    
    def _get_project_id(self) -> str:
        """Get the GCP project ID from environment variables"""
        project_id = os.getenv("GCP_PROJECT_ID")
        if not project_id:
            # Try to get from credentials file
            creds_file = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
            if creds_file and os.path.exists(creds_file):
                try:
                    with open(creds_file, 'r') as f:
                        creds_data = json.load(f)
                        project_id = creds_data.get('project_id')
                except Exception:
                    pass
            
            if not project_id:
                logger.warning("GCP_PROJECT_ID not set, using default")
                project_id = "default-project"
        
        return project_id
    
    def list_resources(self) -> List[Resource]:
        """
        List all supported GCP resources
        
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
    
    def _get_compute_instances(self) -> List[Resource]:
        """Get GCP compute instances"""
        resources = []
        
        try:
            # Create Compute client
            instance_client = compute_v1.InstancesClient()
            
            # List instances for all zones in the project
            request = compute_v1.AggregatedListInstancesRequest(project=self.project_id)
            instances_iterator = instance_client.aggregated_list(request=request)
            
            # Process each zone
            for zone, response in instances_iterator:
                if response.instances:
                    for instance in response.instances:
                        instance_id = instance.id
                        instance_name = instance.name
                        zone_name = zone.split('/')[-1]  # Extract zone name from key
                        
                        # Get instance labels (GCP uses labels instead of tags)
                        tags = instance.labels or {}
                        
                        resource = Resource(
                            resource_id=str(instance_id),
                            name=instance_name,
                            resource_type='compute-instance',
                            cloud_provider='gcp',
                            region=zone_name,
                            tags=tags,
                            compliance_status=ComplianceStatus.UNKNOWN
                        )
                        resources.append(resource)
            
        except GoogleAPIError as e:
            logger.error(f"GCP API error getting compute instances: {str(e)}")
        except Exception as e:
            logger.error(f"Error getting compute instances: {str(e)}")
        
        return resources
    
    def _get_storage_buckets(self) -> List[Resource]:
        """Get GCP storage buckets"""
        resources = []
        
        try:
            # Create Storage client
            storage_client = storage.Client()
            
            # List all buckets
            buckets = storage_client.list_buckets()
            
            for bucket in buckets:
                bucket_name = bucket.name
                bucket_location = bucket.location
                
                # Get bucket labels
                labels = bucket.labels or {}
                
                resource = Resource(
                    resource_id=bucket_name,
                    name=bucket_name,
                    resource_type='storage-bucket',
                    cloud_provider='gcp',
                    region=bucket_location,
                    tags=labels,
                    compliance_status=ComplianceStatus.UNKNOWN
                )
                resources.append(resource)
            
        except GoogleAPIError as e:
            logger.error(f"GCP API error getting storage buckets: {str(e)}")
        except Exception as e:
            logger.error(f"Error getting storage buckets: {str(e)}")
        
        return resources
    
    def update_resource_tags(self, resource_id: str, tags: Dict[str, str]) -> bool:
        """
        Update tags for a specified GCP resource
        
        Args:
            resource_id: GCP resource ID
            tags: Dict of tag keys and values to apply
            
        Returns:
            Boolean indicating success
        """
        # Determine resource type from resource_id or additional metadata
        if resource_id.isdigit():
            # Likely a compute instance
            return self._update_compute_instance_labels(resource_id, tags)
        else:
            # Likely a storage bucket
            return self._update_storage_bucket_labels(resource_id, tags)
    
    def _update_compute_instance_labels(self, instance_id: str, labels: Dict[str, str]) -> bool:
        """Update labels for a compute instance"""
        try:
            # Create Compute client
            instance_client = compute_v1.InstancesClient()
            
            # First, need to find the instance to get its zone
            request = compute_v1.AggregatedListInstancesRequest(
                project=self.project_id,
                filter=f"id={instance_id}"
            )
            instances_iterator = instance_client.aggregated_list(request=request)
            
            instance = None
            zone = None
            
            for zone_path, response in instances_iterator:
                if response.instances:
                    # Found the instance
                    instance = response.instances[0]
                    zone = zone_path.split('/')[-1]
                    break
            
            if not instance or not zone:
                logger.error(f"Instance {instance_id} not found")
                return False
            
            # Get current labels
            current_labels = instance.labels or {}
            
            # Merge existing labels with new labels
            merged_labels = {**current_labels, **labels}
            
            # Prepare the update request
            request = compute_v1.SetLabelsInstanceRequest(
                project=self.project_id,
                zone=zone,
                instance=instance.name,
                instances_set_labels_request_resource=compute_v1.InstancesSetLabelsRequest(
                    labels=merged_labels,
                    label_fingerprint=instance.label_fingerprint
                )
            )
            
            # Apply the update
            operation = instance_client.set_labels(request=request)
            operation.result()  # Wait for the operation to complete
            
            return True
            
        except GoogleAPIError as e:
            logger.error(f"GCP API error updating compute instance labels: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error updating compute instance labels: {str(e)}")
            return False
    
    def _update_storage_bucket_labels(self, bucket_name: str, labels: Dict[str, str]) -> bool:
        """Update labels for a storage bucket"""
        try:
            # Create Storage client
            storage_client = storage.Client()
            
            # Get the bucket
            bucket = storage_client.get_bucket(bucket_name)
            
            # Get current labels
            current_labels = bucket.labels or {}
            
            # Merge existing labels with new labels
            merged_labels = {**current_labels, **labels}
            
            # Update bucket labels
            bucket.labels = merged_labels
            bucket.patch()
            
            return True
            
        except GoogleAPIError as e:
            logger.error(f"GCP API error updating storage bucket labels: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error updating storage bucket labels: {str(e)}")
            return False