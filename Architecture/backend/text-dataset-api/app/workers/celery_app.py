"""
Celery application configuration for background task processing
"""

import os
import logging
from celery import Celery
from celery.signals import task_prerun, task_postrun, task_failure
from kombu import Exchange, Queue

from app.core.config import settings

logger = logging.getLogger(__name__)

# Create Celery instance
celery_app = Celery(
    "text_dataset_api",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.workers.tasks.document_tasks",
        "app.workers.tasks.processing_tasks",
        "app.workers.tasks.analytics_tasks",
        "app.workers.tasks.email_tasks",
        "app.workers.tasks.cleanup_tasks",
    ]
)

# Configure Celery
celery_app.conf.update(
    # Task execution settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Task routing
    task_routes={
        "app.workers.tasks.document_tasks.*": {"queue": "documents"},
        "app.workers.tasks.processing_tasks.*": {"queue": "processing"},
        "app.workers.tasks.analytics_tasks.*": {"queue": "analytics"},
        "app.workers.tasks.email_tasks.*": {"queue": "emails"},
        "app.workers.tasks.cleanup_tasks.*": {"queue": "cleanup"},
    },
    
    # Task time limits
    task_soft_time_limit=settings.CELERY_TASK_SOFT_TIME_LIMIT,
    task_time_limit=settings.CELERY_TASK_TIME_LIMIT,
    
    # Result backend settings
    result_expires=3600,  # 1 hour
    result_backend_always_retry=True,
    result_backend_max_retries=10,
    
    # Worker settings
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
    worker_disable_rate_limits=False,
    
    # Beat scheduler settings (for periodic tasks)
    beat_scheduler="celery.beat:PersistentScheduler",
    beat_schedule_filename="celerybeat-schedule",
    
    # Task retry settings
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_track_started=True,
    task_send_sent_event=True,
    
    # Queue configuration
    task_default_queue="default",
    task_default_exchange="default",
    task_default_exchange_type="direct",
    task_default_routing_key="default",
    
    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
)

# Define queues
celery_app.conf.task_queues = (
    Queue("default", Exchange("default"), routing_key="default"),
    Queue("documents", Exchange("documents"), routing_key="documents", priority=5),
    Queue("processing", Exchange("processing"), routing_key="processing", priority=10),
    Queue("analytics", Exchange("analytics"), routing_key="analytics", priority=3),
    Queue("emails", Exchange("emails"), routing_key="emails", priority=2),
    Queue("cleanup", Exchange("cleanup"), routing_key="cleanup", priority=1),
)

# Configure periodic tasks
celery_app.conf.beat_schedule = {
    # Cleanup tasks
    "cleanup-expired-sessions": {
        "task": "app.workers.tasks.cleanup_tasks.cleanup_expired_sessions",
        "schedule": 3600.0,  # Every hour
    },
    "cleanup-old-temp-files": {
        "task": "app.workers.tasks.cleanup_tasks.cleanup_temp_files",
        "schedule": 86400.0,  # Daily
    },
    "cleanup-failed-jobs": {
        "task": "app.workers.tasks.cleanup_tasks.cleanup_failed_jobs",
        "schedule": 3600.0,  # Every hour
    },
    
    # Analytics tasks
    "calculate-daily-analytics": {
        "task": "app.workers.tasks.analytics_tasks.calculate_daily_analytics",
        "schedule": 86400.0,  # Daily at midnight
        "options": {"queue": "analytics"},
    },
    "generate-usage-reports": {
        "task": "app.workers.tasks.analytics_tasks.generate_usage_reports",
        "schedule": 604800.0,  # Weekly
        "options": {"queue": "analytics"},
    },
    
    # System health checks
    "health-check": {
        "task": "app.workers.tasks.cleanup_tasks.system_health_check",
        "schedule": 300.0,  # Every 5 minutes
    },
}


# Signal handlers for monitoring
@task_prerun.connect
def task_prerun_handler(task_id, task, args, kwargs, **extra):
    """Handler called before task execution"""
    logger.info(f"Task {task.name} [{task_id}] starting with args={args}, kwargs={kwargs}")


@task_postrun.connect
def task_postrun_handler(task_id, task, args, kwargs, retval, state, **extra):
    """Handler called after task execution"""
    logger.info(f"Task {task.name} [{task_id}] completed with state={state}")


@task_failure.connect
def task_failure_handler(task_id, exception, args, kwargs, traceback, einfo, **extra):
    """Handler called on task failure"""
    logger.error(
        f"Task {task_id} failed with exception: {exception}\n"
        f"Args: {args}\n"
        f"Kwargs: {kwargs}\n"
        f"Traceback: {einfo}"
    )


# Celery task base class with additional functionality
class BaseTask(celery_app.Task):
    """Base task with database session management"""
    
    _db = None
    
    @property
    def db(self):
        """Get database session"""
        if self._db is None:
            from app.core.database import SessionLocal
            self._db = SessionLocal()
        return self._db
    
    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        """Clean up after task execution"""
        if self._db is not None:
            self._db.close()
            self._db = None
        super().after_return(status, retval, task_id, args, kwargs, einfo)
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure"""
        # Log failure to database
        try:
            from app.models.document import ProcessingJob, JobStatus
            
            # Update job status if job_id is in kwargs
            job_id = kwargs.get("job_id")
            if job_id:
                job = self.db.query(ProcessingJob).filter_by(id=job_id).first()
                if job:
                    job.status = JobStatus.FAILED
                    job.error_message = str(exc)
                    self.db.commit()
        except Exception as e:
            logger.error(f"Failed to update job status: {e}")
        
        super().on_failure(exc, task_id, args, kwargs, einfo)


# Register base task
celery_app.Task = BaseTask

# Worker initialization
def init_worker():
    """Initialize worker (called when worker starts)"""
    logger.info("Celery worker initialized")


# Create singleton instance
app = celery_app

if __name__ == "__main__":
    app.start()