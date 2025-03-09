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