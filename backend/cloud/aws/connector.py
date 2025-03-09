# cloud/aws/connector.py
import boto3
import logging
from typing import Dict, List, Any, Optional
from botocore.exceptions import ClientError

from models.resource import Resource, ComplianceStatus

logger = logging.getLogger(__name__)

class AWSConnector:
    """Connector for AWS cloud resources"""
    
    def __init__(self):
        self.session = boto3.Session()
        self.supported_resource_types = {
            'ec2': self._get_ec2_resources,
            's3': self._get_s3_resources,
            'rds': self._get_rds_resources,
            'lambda': self._get_lambda_resources,
        }
    
    def list_resources(self) -> List[Resource]:
        """
        List all supported AWS resources across regions
        
        Returns:
            List of Resource objects
        """
        resources = []
        
        # Get list of all regions
        ec2_client = self.session.client('ec2', region_name='us-east-1')
        try:
            regions = [region['RegionName'] for region in ec2_client.describe_regions()['Regions']]
        except ClientError as e:
            logger.error(f"Error getting AWS regions: {str(e)}")
            regions = ['us-east-1', 'us-east-2', 'us-west-1', 'us-west-2', 'eu-west-1']
        
        # Fetch resources from each region
        for region in regions:
            for resource_type, resource_fetcher in self.supported_resource_types.items():
                try:
                    region_resources = resource_fetcher(region)
                    resources.extend(region_resources)
                except Exception as e:
                    logger.error(f"Error fetching {resource_type} resources in {region}: {str(e)}")
        
        return resources
    
    def _get_ec2_resources(self, region: str) -> List[Resource]:
        """Get EC2 instances in the specified region"""
        ec2_client = self.session.client('ec2', region_name=region)
        resources = []
        
        try:
            response = ec2_client.describe_instances()
            
            for reservation in response.get('Reservations', []):
                for instance in reservation.get('Instances', []):
                    instance_id = instance['InstanceId']
                    tags = {tag['Key']: tag['Value'] for tag in instance.get('Tags', [])}
                    
                    resource = Resource(
                        resource_id=instance_id,
                        name=tags.get('Name', instance_id),
                        resource_type='ec2',
                        cloud_provider='aws',
                        region=region,
                        tags=tags,
                        compliance_status=ComplianceStatus.UNKNOWN
                    )
                    resources.append(resource)
                    
            return resources
            
        except ClientError as e:
            logger.error(f"Error getting EC2 instances in {region}: {str(e)}")
            return []
    
    def _get_s3_resources(self, region: str) -> List[Resource]:
        """Get S3 buckets"""
        # S3 is a global service, so we only need to fetch once
        if region != 'us-east-1':
            return []
            
        s3_client = self.session.client('s3')
        resources = []
        
        try:
            response = s3_client.list_buckets()
            
            for bucket in response.get('Buckets', []):
                bucket_name = bucket['Name']
                
                # Get bucket tags
                try:
                    tag_response = s3_client.get_bucket_tagging(Bucket=bucket_name)
                    tags = {tag['Key']: tag['Value'] for tag in tag_response.get('TagSet', [])}
                except ClientError:
                    # Bucket might not have tags
                    tags = {}
                
                # Get bucket region
                try:
                    bucket_region = s3_client.get_bucket_location(Bucket=bucket_name)
                    bucket_region = bucket_region.get('LocationConstraint', 'us-east-1')
                    if bucket_region is None:
                        bucket_region = 'us-east-1'
                except ClientError:
                    bucket_region = 'unknown'
                
                resource = Resource(
                    resource_id=bucket_name,
                    name=bucket_name,
                    resource_type='s3',
                    cloud_provider='aws',
                    region=bucket_region,
                    tags=tags,
                    compliance_status=ComplianceStatus.UNKNOWN
                )
                resources.append(resource)
                
            return resources
            
        except ClientError as e:
            logger.error(f"Error getting S3 buckets: {str(e)}")
            return []
    
    def _get_rds_resources(self, region: str) -> List[Resource]:
        """Get RDS instances in the specified region"""
        rds_client = self.session.client('rds', region_name=region)
        resources = []
        
        try:
            response = rds_client.describe_db_instances()
            
            for instance in response.get('DBInstances', []):
                instance_id = instance['DBInstanceIdentifier']
                
                # Get instance tags
                try:
                    arn = instance['DBInstanceArn']
                    tag_response = rds_client.list_tags_for_resource(ResourceName=arn)
                    tags = {tag['Key']: tag['Value'] for tag in tag_response.get('TagList', [])}
                except ClientError:
                    tags = {}
                
                resource = Resource(
                    resource_id=instance_id,
                    name=instance_id,
                    resource_type='rds',
                    cloud_provider='aws',
                    region=region,
                    tags=tags,
                    compliance_status=ComplianceStatus.UNKNOWN
                )
                resources.append(resource)
                
            return resources
            
        except ClientError as e:
            logger.error(f"Error getting RDS instances in {region}: {str(e)}")
            return []
    
    def _get_lambda_resources(self, region: str) -> List[Resource]:
        """Get Lambda functions in the specified region"""
        lambda_client = self.session.client('lambda', region_name=region)
        resources = []
        
        try:
            response = lambda_client.list_functions()
            
            for function in response.get('Functions', []):
                function_name = function['FunctionName']
                function_arn = function['FunctionArn']
                
                # Get function tags
                try:
                    tag_response = lambda_client.list_tags(Resource=function_arn)
                    tags = tag_response.get('Tags', {})
                except ClientError:
                    tags = {}
                
                resource = Resource(
                    resource_id=function_arn,
                    name=function_name,
                    resource_type='lambda',
                    cloud_provider='aws',
                    region=region,
                    tags=tags,
                    compliance_status=ComplianceStatus.UNKNOWN
                )
                resources.append(resource)
                
            return resources
            
        except ClientError as e:
            logger.error(f"Error getting Lambda functions in {region}: {str(e)}")
            return []
    
    def update_resource_tags(self, resource_id: str, tags: Dict[str, str]) -> bool:
        """
        Update tags for a specified AWS resource
        
        Args:
            resource_id: AWS resource ID
            tags: Dict of tag keys and values to apply
            
        Returns:
            Boolean indicating success
        """
        # Determine resource type and region from the resource ID
        if resource_id.startswith('i-'):
            # EC2 instance
            resource_type = 'ec2'
            # Extract region from ARN or assume default
            region = 'us-east-1'  # Default if we can't determine
            
            # Create EC2 client
            ec2_client = self.session.client('ec2', region_name=region)
            
            try:
                # Format tags for EC2
                tag_list = [{'Key': key, 'Value': value} for key, value in tags.items()]
                ec2_client.create_tags(Resources=[resource_id], Tags=tag_list)
                return True
            except ClientError as e:
                logger.error(f"Error updating tags for EC2 instance {resource_id}: {str(e)}")
                return False
                
        elif resource_id.startswith('arn:aws:s3'):
            # S3 bucket
            bucket_name = resource_id.split(':')[-1]
            s3_client = self.session.client('s3')
            
            try:
                # Format tags for S3
                tag_set = [{'Key': key, 'Value': value} for key, value in tags.items()]
                s3_client.put_bucket_tagging(Bucket=bucket_name, Tagging={'TagSet': tag_set})
                return True
            except ClientError as e:
                logger.error(f"Error updating tags for S3 bucket {resource_id}: {str(e)}")
                return False
                
        elif resource_id.startswith('arn:aws:rds'):
            # RDS instance
            rds_client = self.session.client('rds')
            
            try:
                # Format tags for RDS
                tag_list = [{'Key': key, 'Value': value} for key, value in tags.items()]
                rds_client.add_tags_to_resource(ResourceName=resource_id, Tags=tag_list)
                return True
            except ClientError as e:
                logger.error(f"Error updating tags for RDS instance {resource_id}: {str(e)}")
                return False
                
        elif resource_id.startswith('arn:aws:lambda'):
            # Lambda function
            lambda_client = self.session.client('lambda')
            
            try:
                lambda_client.tag_resource(Resource=resource_id, Tags=tags)
                return True
            except ClientError as e:
                logger.error(f"Error updating tags for Lambda function {resource_id}: {str(e)}")
                return False
                
        else:
            logger.error(f"Unsupported resource type for ID: {resource_id}")
            return False