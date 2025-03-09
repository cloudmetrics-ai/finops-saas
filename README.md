# finops-saas
finops-saas


# Cloud Resource Tagging Compliance Automation - Implementation Guide

## Overview

This guide provides instructions for implementing the Cloud Resource Tagging Compliance Automation system. The system enables organizations to enforce consistent resource tagging across multiple cloud providers (AWS, Azure, GCP) with automated scanning, compliance evaluation, and remediation workflows.

## Architecture

The system consists of:

1. **Backend API** - Python/FastAPI service that connects to cloud providers, scans resources, evaluates compliance, and manages remediation workflows
2. **Frontend UI** - React application for visualizing compliance status and approving remediation workflows
3. **Database** - PostgreSQL for storing resource metadata, compliance policies, and workflow state

## Prerequisites

- Python 3.8+ for backend development
- Node.js 14+ for frontend development
- PostgreSQL 12+ for database
- Docker and Docker Compose (optional, for containerized deployment)
- Cloud provider credentials with appropriate permissions:
  - AWS: IAM credentials with read/tag permissions for resources
  - Azure: Service Principal with Reader and Tag Contributor roles
  - GCP: Service Account with appropriate viewer and tag permissions

## Setup Instructions

### 1. Database Setup

```bash
# Create PostgreSQL database
createdb cloud_compliance

# The application will automatically create necessary tables on startup
```

### 2. Backend Setup

```bash
# Clone the repository
git clone https://your-repo/cloud-tag-compliance.git
cd cloud-tag-compliance/backend

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables for cloud credentials
export DATABASE_URL="postgresql://postgres:postgres@localhost/cloud_compliance"
export AWS_ACCESS_KEY_ID="your-aws-access-key"
export AWS_SECRET_ACCESS_KEY="your-aws-secret-key"
export AZURE_CLIENT_ID="your-azure-client-id"
export AZURE_CLIENT_SECRET="your-azure-client-secret"
export AZURE_TENANT_ID="your-azure-tenant-id"
export GCP_SERVICE_ACCOUNT_JSON="/path/to/gcp-service-account.json"

# Run the application
uvicorn app:app --reload
```

### 3. Frontend Setup

```bash
# Navigate to frontend directory
cd ../frontend

# Install dependencies
npm install

# Set API URL in .env file
echo "REACT_APP_API_URL=http://localhost:8000/api" > .env

# Start development server
npm start
```

## Policy Configuration

The system uses policies to define tagging requirements. Here's an example policy structure:

```json
{
  "name": "Production Resources Policy",
  "description": "Policy for tagging production resources",
  "active": true,
  "required_tags": [
    {
      "name": "environment",
      "allowed_values": ["production", "staging", "development"],
      "default_value": "production"
    },
    {
      "name": "owner",
      "allowed_values": null
    },
    {
      "name": "cost-center",
      "allowed_values": ["finance", "marketing", "engineering", "operations"]
    }
  ],
  "resource_types": ["ec2", "s3", "rds", "vm", "storage-account"],
  "cloud_providers": ["aws", "azure"]
}
```

## Extending the System

### Adding Support for New Cloud Resources

1. Modify the appropriate cloud connector in the `cloud/` directory
2. Add the resource type to the `supported_resource_types` dictionary
3. Implement the resource fetcher function (e.g., `_get_new_resource_type`)
4. Add tag update logic in `update_resource_tags` method

### Creating Custom Compliance Rules

The compliance engine can be extended to support more complex rules:

1. Modify `core/compliance_engine.py`
2. Add new validation logic in the `evaluate_compliance` method
3. Update the policy model to include new rule types

## Deployment

### Using Docker Compose

```bash
# Build and start all services
docker-compose up -d

# Check logs
docker-compose logs -f

# Stop all services
docker-compose down
```

### Kubernetes Deployment

For production environments, consider deploying to Kubernetes:

1. Create Kubernetes deployment YAML files for each component
2. Use Kubernetes secrets for sensitive credentials
3. Set up appropriate resource limits and autoscaling
4. Use a managed PostgreSQL service or deploy with persistent volumes

## Scheduled Scanning

Configure scheduled compliance scans using the built-in scheduler or external tools:

### Using Built-in Scheduler

Configure the scanning frequency in the application settings. The system will automatically run scans at the specified intervals.

### Using External Scheduler (e.g., cron)

```bash
# Example cron job to scan resources daily
0 2 * * * curl -X GET http://localhost:8000/api/compliance/scan

# Example cron job to evaluate compliance daily
30 2 * * * curl -X GET http://localhost:8000/api/compliance/evaluate
```

## Troubleshooting

### Common Issues

1. **Cloud Provider Connection Issues**
   - Verify credentials are correct and have appropriate permissions
   - Check network connectivity to cloud provider APIs
   - Look for specific error messages in the logs

2. **Database Connectivity**
   - Ensure PostgreSQL is running and accessible
   - Verify database connection string is correct
   - Check for schema migration issues

3. **API Errors**
   - Check FastAPI logs for detailed error information
   - Verify frontend API calls match expected backend endpoints
   - Check for CORS configuration issues

### Logs

- Backend logs are written to stdout/stderr by default
- Enable debug logging by setting `LOG_LEVEL=DEBUG`
- For production, consider integrating with a centralized logging solution

## Security Considerations

1. **Credentials Management**
   - Never store cloud credentials in code or version control
   - Use environment variables, secrets management, or IAM roles
   - Rotate credentials regularly

2. **API Security**
   - Implement proper authentication and authorization
   - Use HTTPS for all communication
   - Limit API access to necessary users and services

3. **Data Protection**
   - Encrypt sensitive data at rest and in transit
   - Implement proper database access controls
   - Regularly backup the database