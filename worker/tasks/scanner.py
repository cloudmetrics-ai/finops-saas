# worker/tasks/scanner.py
"""
Background task for scanning cloud resources
"""
import logging
from datetime import datetime
from typing import Optional, List
import time

from backend.core.compliance.engine import ComplianceEngine
from backend.models.db import get_db

logger = logging.getLogger(__name__)

def scan_resources_task(cloud_provider: Optional[str] = None) -> dict:
    """
    Task to scan cloud resources and update the database
    
    Args:
        cloud_provider: Optional cloud provider to scan (aws, azure, gcp)
        
    Returns:
        Dict with scan results
    """
    logger.info(f"Starting resource scan for {cloud_provider or 'all providers'}")
    start_time = time.time()
    
    try:
        compliance_engine = ComplianceEngine()
        resources = compliance_engine.scan_resources(cloud_provider)
        
        duration = time.time() - start_time
        logger.info(f"Completed resource scan in {duration:.2f}s. Found {len(resources)} resources.")
        
        return {
            "status": "success",
            "message": f"Scanned {len(resources)} resources",
            "resource_count": len(resources),
            "duration_seconds": duration
        }
    except Exception as e:
        logger.error(f"Error in resource scan: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "message": f"Error in resource scan: {str(e)}",
            "duration_seconds": time.time() - start_time
        }

# worker/tasks/evaluator.py
"""
Background task for evaluating compliance
"""
import logging
from datetime import datetime
import time

from backend.core.compliance.engine import ComplianceEngine
from backend.models.db import get_db

logger = logging.getLogger(__name__)

def evaluate_compliance_task() -> dict:
    """
    Task to evaluate compliance for all resources
    
    Returns:
        Dict with evaluation results
    """
    logger.info("Starting compliance evaluation")
    start_time = time.time()
    
    try:
        compliance_engine = ComplianceEngine()
        results = compliance_engine.evaluate_all_resources()
        
        duration = time.time() - start_time
        logger.info(f"Completed compliance evaluation in {duration:.2f}s. "
                   f"Compliant: {results['compliant']}, Non-compliant: {results['non_compliant']}")
        
        return {
            "status": "success",
            "results": results,
            "duration_seconds": duration
        }
    except Exception as e:
        logger.error(f"Error in compliance evaluation: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "message": f"Error in compliance evaluation: {str(e)}",
            "duration_seconds": time.time() - start_time
        }

# worker/tasks/remediation.py
"""
Background task for applying remediation
"""
import logging
from datetime import datetime
import time
from typing import Dict, Optional

from backend.core.compliance.engine import ComplianceEngine
from backend.models.db import get_db
from backend.models.workflow import WorkflowModel, WorkflowStatus

logger = logging.getLogger(__name__)

def apply_remediation_task(workflow_id: int, approved_tags: Dict[str, str], 
                         approved_by: Optional[str] = None) -> dict:
    """
    Task to apply approved remediation tags
    
    Args:
        workflow_id: ID of the remediation workflow
        approved_tags: Dict of tag names and values to apply
        approved_by: User who approved the remediation
        
    Returns:
        Dict with remediation results
    """
    logger.info(f"Starting remediation for workflow {workflow_id}")
    start_time = time.time()
    
    try:
        compliance_engine = ComplianceEngine()
        success = compliance_engine.approve_remediation(workflow_id, approved_tags)
        
        duration = time.time() - start_time
        
        if success:
            logger.info(f"Completed remediation for workflow {workflow_id} in {duration:.2f}s")
            return {
                "status": "success",
                "message": f"Remediation completed for workflow {workflow_id}",
                "duration_seconds": duration
            }
        else:
            logger.error(f"Failed to apply remediation for workflow {workflow_id}")
            return {
                "status": "error",
                "message": f"Failed to apply remediation for workflow {workflow_id}",
                "duration_seconds": duration
            }
    except Exception as e:
        logger.error(f"Error in remediation task: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "message": f"Error in remediation task: {str(e)}",
            "duration_seconds": time.time() - start_time
        }

# worker/scheduler.py
"""
Scheduler configuration for periodic tasks
"""
import logging
from datetime import datetime, timedelta
from typing import Dict

from celery import Celery
from celery.schedules import crontab

from worker.tasks.scanner import scan_resources_task
from worker.tasks.evaluator import evaluate_compliance_task

# Configure Celery
app = Celery('cloud_compliance_worker')

# Set appropriate configuration for your environment
app.conf.update(
    broker_url='redis://localhost:6379/0',
    result_backend='redis://localhost:6379/0',
    timezone='UTC',
    enable_utc=True,
)

# Configure periodic tasks
app.conf.beat_schedule = {
    'scan-resources-daily': {
        'task': 'worker.tasks.scanner.scan_resources_task',
        'schedule': crontab(hour=2, minute=0),  # Run at 2:00 AM every day
        'args': (None,),  # Scan all providers
    },
    'evaluate-compliance-daily': {
        'task': 'worker.tasks.evaluator.evaluate_compliance_task',
        'schedule': crontab(hour=3, minute=0),  # Run at 3:00 AM every day
    },
    # Add additional scheduled tasks as needed
}

# Register tasks
app.task(scan_resources_task)
app.task(evaluate_compliance_task)

if __name__ == '__main__':
    app.start()