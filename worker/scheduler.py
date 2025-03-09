# worker/scheduler.py
"""
Scheduler configuration for periodic tasks
"""
import logging
from datetime import datetime, timedelta
from typing import Dict
import os

from celery import Celery
from celery.schedules import crontab

from worker.tasks.scanner import scan_resources_task
from worker.tasks.evaluator import evaluate_compliance_task
from worker.tasks.remediation import apply_remediation_task

logger = logging.getLogger(__name__)

# Get Celery configuration from environment variables
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

# Configure Celery
app = Celery(
    'cloud_compliance_worker',
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND
)

# Set additional configuration
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
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
    'scan-aws-resources-hourly': {
        'task': 'worker.tasks.scanner.scan_resources_task',
        'schedule': crontab(minute=0),  # Run every hour
        'args': ('aws',),  # Scan only AWS resources
    },
    'scan-azure-resources-hourly': {
        'task': 'worker.tasks.scanner.scan_resources_task',
        'schedule': crontab(minute=15),  # Run every hour at 15 minutes past
        'args': ('azure',),  # Scan only Azure resources
    },
    'scan-gcp-resources-hourly': {
        'task': 'worker.tasks.scanner.scan_resources_task',
        'schedule': crontab(minute=30),  # Run every hour at 30 minutes past
        'args': ('gcp',),  # Scan only GCP resources
    },
}

# Register tasks
@app.task(name='worker.tasks.scanner.scan_resources_task')
def scan_resources_task_wrapper(cloud_provider=None):
    return scan_resources_task(cloud_provider)

@app.task(name='worker.tasks.evaluator.evaluate_compliance_task')
def evaluate_compliance_task_wrapper():
    return evaluate_compliance_task()

@app.task(name='worker.tasks.remediation.apply_remediation_task')
def apply_remediation_task_wrapper(workflow_id, approved_tags, approved_by=None):
    return apply_remediation_task(workflow_id, approved_tags, approved_by)

if __name__ == '__main__':
    # If this file is run directly, start the Celery worker
    app.start()