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