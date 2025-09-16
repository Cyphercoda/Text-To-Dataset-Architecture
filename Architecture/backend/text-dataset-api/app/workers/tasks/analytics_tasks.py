"""
Analytics and reporting tasks
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from uuid import UUID

from celery import Task
from sqlalchemy import func, and_, or_

from app.workers.celery_app import celery_app
from app.models.user import User, UsageRecord
from app.models.document import Document, ProcessingJob, Dataset
from app.models.analytics import AnalyticsEvent, ProcessingMetrics, UserActivity
from app.services.analytics.analytics_service import analytics_service
from app.services.reporting.report_generator import report_generator
from app.api.websocket.manager import websocket_manager
from app.core.database import SessionLocal

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="calculate_daily_analytics")
def calculate_daily_analytics(
    self: Task,
    date: Optional[str] = None
) -> Dict[str, Any]:
    """
    Calculate daily analytics aggregations
    
    Args:
        date: Date to calculate analytics for (YYYY-MM-DD), defaults to yesterday
    
    Returns:
        Analytics calculation results
    """
    db = SessionLocal()
    
    try:
        # Parse date or use yesterday
        if date:
            target_date = datetime.strptime(date, "%Y-%m-%d").date()
        else:
            target_date = (datetime.utcnow() - timedelta(days=1)).date()
        
        start_time = datetime.combine(target_date, datetime.min.time())
        end_time = datetime.combine(target_date, datetime.max.time())
        
        logger.info(f"Calculating daily analytics for {target_date}")
        
        # User metrics
        new_users = db.query(User).filter(
            func.date(User.created_at) == target_date
        ).count()
        
        active_users = db.query(UserActivity).filter(
            and_(
                UserActivity.timestamp >= start_time,
                UserActivity.timestamp <= end_time
            )
        ).distinct(UserActivity.user_id).count()
        
        # Document metrics
        documents_uploaded = db.query(Document).filter(
            func.date(Document.uploaded_at) == target_date
        ).count()
        
        documents_processed = db.query(Document).filter(
            func.date(Document.processed_at) == target_date
        ).count()
        
        total_file_size = db.query(func.sum(Document.file_size)).filter(
            func.date(Document.uploaded_at) == target_date
        ).scalar() or 0
        
        # Processing metrics
        processing_jobs = db.query(ProcessingJob).filter(
            func.date(ProcessingJob.created_at) == target_date
        ).count()
        
        successful_jobs = db.query(ProcessingJob).filter(
            and_(
                func.date(ProcessingJob.created_at) == target_date,
                ProcessingJob.status == "completed"
            )
        ).count()
        
        failed_jobs = db.query(ProcessingJob).filter(
            and_(
                func.date(ProcessingJob.created_at) == target_date,
                ProcessingJob.status == "failed"
            )
        ).count()
        
        # Average processing time
        avg_processing_time = db.query(
            func.avg(
                func.extract('epoch', ProcessingJob.completed_at - ProcessingJob.started_at)
            )
        ).filter(
            and_(
                func.date(ProcessingJob.completed_at) == target_date,
                ProcessingJob.status == "completed"
            )
        ).scalar() or 0
        
        # Dataset metrics
        datasets_generated = db.query(Dataset).filter(
            func.date(Dataset.created_at) == target_date
        ).count()
        
        # Usage metrics
        api_calls = db.query(UsageRecord).filter(
            func.date(UsageRecord.timestamp) == target_date
        ).count()
        
        # Store metrics
        metrics = ProcessingMetrics(
            date=target_date,
            new_users=new_users,
            active_users=active_users,
            documents_uploaded=documents_uploaded,
            documents_processed=documents_processed,
            total_file_size_bytes=total_file_size,
            processing_jobs=processing_jobs,
            successful_jobs=successful_jobs,
            failed_jobs=failed_jobs,
            avg_processing_time_seconds=avg_processing_time,
            datasets_generated=datasets_generated,
            api_calls=api_calls,
            created_at=datetime.utcnow()
        )
        
        db.add(metrics)
        db.commit()
        
        # Calculate derived metrics
        success_rate = (successful_jobs / processing_jobs * 100) if processing_jobs > 0 else 0
        failure_rate = (failed_jobs / processing_jobs * 100) if processing_jobs > 0 else 0
        
        analytics_data = {
            "date": target_date.isoformat(),
            "users": {
                "new_users": new_users,
                "active_users": active_users
            },
            "documents": {
                "uploaded": documents_uploaded,
                "processed": documents_processed,
                "total_size_mb": round(total_file_size / 1024 / 1024, 2)
            },
            "processing": {
                "total_jobs": processing_jobs,
                "successful_jobs": successful_jobs,
                "failed_jobs": failed_jobs,
                "success_rate": round(success_rate, 2),
                "failure_rate": round(failure_rate, 2),
                "avg_processing_time_minutes": round(avg_processing_time / 60, 2)
            },
            "datasets": {
                "generated": datasets_generated
            },
            "api": {
                "total_calls": api_calls
            }
        }
        
        logger.info(f"Daily analytics calculated: {analytics_data}")
        
        return {
            "success": True,
            "date": target_date.isoformat(),
            "analytics": analytics_data
        }
    
    except Exception as e:
        logger.error(f"Daily analytics calculation failed: {e}")
        raise
    
    finally:
        db.close()


@celery_app.task(bind=True, name="generate_usage_reports")
def generate_usage_reports(
    self: Task,
    period: str = "weekly",
    user_ids: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Generate usage reports for users or system
    
    Args:
        period: Report period (daily, weekly, monthly)
        user_ids: Optional list of user IDs to generate reports for
    
    Returns:
        Report generation results
    """
    db = SessionLocal()
    
    try:
        # Determine date range
        if period == "daily":
            start_date = datetime.utcnow().date() - timedelta(days=1)
            end_date = start_date
        elif period == "weekly":
            start_date = datetime.utcnow().date() - timedelta(days=7)
            end_date = datetime.utcnow().date() - timedelta(days=1)
        elif period == "monthly":
            start_date = datetime.utcnow().date() - timedelta(days=30)
            end_date = datetime.utcnow().date() - timedelta(days=1)
        else:
            raise ValueError(f"Invalid period: {period}")
        
        start_time = datetime.combine(start_date, datetime.min.time())
        end_time = datetime.combine(end_date, datetime.max.time())
        
        # Get users to generate reports for
        if user_ids:
            users = db.query(User).filter(User.id.in_(user_ids)).all()
        else:
            # Generate for all active users
            users = db.query(User).filter(
                and_(
                    User.is_active == True,
                    User.last_login_at >= start_time
                )
            ).all()
        
        reports = []
        
        for user in users:
            # Generate user report
            report_data = report_generator.generate_user_report(
                user_id=str(user.id),
                start_date=start_date,
                end_date=end_date,
                db=db
            )
            
            # Store report
            report_path = report_generator.save_report(
                user_id=str(user.id),
                report_type=f"{period}_usage",
                data=report_data,
                period=f"{start_date}_to_{end_date}"
            )
            
            reports.append({
                "user_id": str(user.id),
                "report_path": report_path,
                "data": report_data
            })
            
            # Send notification to user
            websocket_manager.send_notification(str(user.id), {
                "type": "report_generated",
                "title": f"{period.title()} Usage Report",
                "message": f"Your {period} usage report is ready",
                "report_url": report_path,
                "period": f"{start_date} to {end_date}"
            })
        
        logger.info(f"Generated {len(reports)} {period} usage reports")
        
        return {
            "success": True,
            "period": period,
            "reports_generated": len(reports),
            "reports": reports
        }
    
    except Exception as e:
        logger.error(f"Usage report generation failed: {e}")
        raise
    
    finally:
        db.close()


@celery_app.task(bind=True, name="track_user_activity")
def track_user_activity(
    self: Task,
    user_id: str,
    activity_type: str,
    activity_data: Dict[str, Any],
    session_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Track user activity for analytics
    
    Args:
        user_id: User ID
        activity_type: Type of activity
        activity_data: Activity data
        session_id: Optional session ID
    
    Returns:
        Activity tracking result
    """
    db = SessionLocal()
    
    try:
        # Create activity record
        activity = UserActivity(
            user_id=UUID(user_id),
            activity_type=activity_type,
            activity_data=activity_data,
            session_id=session_id,
            timestamp=datetime.utcnow()
        )
        
        db.add(activity)
        db.commit()
        
        # Update user's last activity
        user = db.query(User).filter_by(id=user_id).first()
        if user:
            user.last_activity_at = datetime.utcnow()
            db.commit()
        
        return {
            "success": True,
            "activity_id": str(activity.id)
        }
    
    except Exception as e:
        logger.error(f"Activity tracking failed: {e}")
        raise
    
    finally:
        db.close()


@celery_app.task(bind=True, name="calculate_user_metrics")
def calculate_user_metrics(
    self: Task,
    user_id: str,
    period_days: int = 30
) -> Dict[str, Any]:
    """
    Calculate comprehensive user metrics
    
    Args:
        user_id: User ID
        period_days: Number of days to look back
    
    Returns:
        User metrics
    """
    db = SessionLocal()
    
    try:
        start_date = datetime.utcnow() - timedelta(days=period_days)
        
        # Document metrics
        documents_uploaded = db.query(Document).filter(
            and_(
                Document.user_id == user_id,
                Document.uploaded_at >= start_date
            )
        ).count()
        
        documents_processed = db.query(Document).filter(
            and_(
                Document.user_id == user_id,
                Document.processed_at >= start_date
            )
        ).count()
        
        total_size = db.query(func.sum(Document.file_size)).filter(
            and_(
                Document.user_id == user_id,
                Document.uploaded_at >= start_date
            )
        ).scalar() or 0
        
        # Processing jobs
        processing_jobs = db.query(ProcessingJob).filter(
            and_(
                ProcessingJob.user_id == user_id,
                ProcessingJob.created_at >= start_date
            )
        ).count()
        
        # Datasets
        datasets_created = db.query(Dataset).filter(
            and_(
                Dataset.user_id == user_id,
                Dataset.created_at >= start_date
            )
        ).count()
        
        # API usage
        api_calls = db.query(UsageRecord).filter(
            and_(
                UsageRecord.user_id == user_id,
                UsageRecord.timestamp >= start_date
            )
        ).count()
        
        # Activity sessions
        activity_sessions = db.query(UserActivity).filter(
            and_(
                UserActivity.user_id == user_id,
                UserActivity.timestamp >= start_date
            )
        ).distinct(UserActivity.session_id).count()
        
        metrics = {
            "user_id": user_id,
            "period_days": period_days,
            "documents": {
                "uploaded": documents_uploaded,
                "processed": documents_processed,
                "total_size_mb": round(total_size / 1024 / 1024, 2)
            },
            "processing": {
                "jobs": processing_jobs
            },
            "datasets": {
                "created": datasets_created
            },
            "api": {
                "calls": api_calls
            },
            "activity": {
                "sessions": activity_sessions
            },
            "calculated_at": datetime.utcnow().isoformat()
        }
        
        return {
            "success": True,
            "metrics": metrics
        }
    
    except Exception as e:
        logger.error(f"User metrics calculation failed: {e}")
        raise
    
    finally:
        db.close()


@celery_app.task(bind=True, name="generate_system_health_report")
def generate_system_health_report(
    self: Task
) -> Dict[str, Any]:
    """
    Generate system health report
    
    Returns:
        System health report
    """
    db = SessionLocal()
    
    try:
        now = datetime.utcnow()
        last_24h = now - timedelta(hours=24)
        last_hour = now - timedelta(hours=1)
        
        # Database health
        total_users = db.query(User).count()
        active_users_24h = db.query(User).filter(
            User.last_activity_at >= last_24h
        ).count()
        
        total_documents = db.query(Document).count()
        processing_queue_size = db.query(ProcessingJob).filter(
            ProcessingJob.status == "pending"
        ).count()
        
        # Recent errors
        recent_failures = db.query(ProcessingJob).filter(
            and_(
                ProcessingJob.status == "failed",
                ProcessingJob.completed_at >= last_24h
            )
        ).count()
        
        # Processing metrics
        avg_processing_time_1h = db.query(
            func.avg(
                func.extract('epoch', ProcessingJob.completed_at - ProcessingJob.started_at)
            )
        ).filter(
            and_(
                ProcessingJob.completed_at >= last_hour,
                ProcessingJob.status == "completed"
            )
        ).scalar() or 0
        
        # Storage metrics
        total_storage_bytes = db.query(func.sum(Document.file_size)).scalar() or 0
        
        health_report = {
            "timestamp": now.isoformat(),
            "users": {
                "total": total_users,
                "active_24h": active_users_24h
            },
            "documents": {
                "total": total_documents,
                "total_storage_gb": round(total_storage_bytes / 1024 / 1024 / 1024, 2)
            },
            "processing": {
                "queue_size": processing_queue_size,
                "recent_failures": recent_failures,
                "avg_processing_time_minutes": round(avg_processing_time_1h / 60, 2)
            },
            "health_status": "healthy" if processing_queue_size < 100 and recent_failures < 10 else "warning"
        }
        
        # Send to admin users via WebSocket
        admin_users = db.query(User).filter(User.role == "admin").all()
        for admin in admin_users:
            websocket_manager.send_notification(str(admin.id), {
                "type": "system_health_report",
                "title": "System Health Report",
                "data": health_report
            })
        
        logger.info(f"System health report generated: {health_report['health_status']}")
        
        return {
            "success": True,
            "report": health_report
        }
    
    except Exception as e:
        logger.error(f"System health report generation failed: {e}")
        raise
    
    finally:
        db.close()


@celery_app.task(bind=True, name="aggregate_analytics_events")
def aggregate_analytics_events(
    self: Task,
    hours_back: int = 1
) -> Dict[str, Any]:
    """
    Aggregate analytics events into summaries
    
    Args:
        hours_back: Number of hours to look back
    
    Returns:
        Aggregation results
    """
    db = SessionLocal()
    
    try:
        start_time = datetime.utcnow() - timedelta(hours=hours_back)
        
        # Get events to aggregate
        events = db.query(AnalyticsEvent).filter(
            AnalyticsEvent.timestamp >= start_time
        ).all()
        
        # Aggregate by event type
        event_counts = {}
        for event in events:
            event_type = event.event_type
            if event_type not in event_counts:
                event_counts[event_type] = 0
            event_counts[event_type] += 1
        
        # User activity aggregation
        user_activities = {}
        for event in events:
            if event.user_id:
                user_id = str(event.user_id)
                if user_id not in user_activities:
                    user_activities[user_id] = []
                user_activities[user_id].append(event.event_type)
        
        aggregation_results = {
            "period": f"{start_time.isoformat()} to {datetime.utcnow().isoformat()}",
            "total_events": len(events),
            "event_types": event_counts,
            "unique_users": len(user_activities),
            "aggregated_at": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Aggregated {len(events)} analytics events")
        
        return {
            "success": True,
            "results": aggregation_results
        }
    
    except Exception as e:
        logger.error(f"Analytics event aggregation failed: {e}")
        raise
    
    finally:
        db.close()