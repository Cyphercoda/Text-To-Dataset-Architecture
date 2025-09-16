"""
Analytics service for tracking and reporting user activities
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from uuid import UUID
import json

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, and_, or_, desc, distinct
from sqlalchemy.orm import selectinload

from app.models.user import User, UsageRecord
from app.models.document import Document, ProcessingJob, Dataset
from app.models.analytics import AnalyticsEvent, ProcessingMetrics, UserActivity
from app.services.aws.cloudwatch_service import cloudwatch_service
from app.core.database import SessionLocal

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service for analytics tracking and reporting"""
    
    async def track_event(
        self,
        db: AsyncSession,
        user_id: Optional[UUID],
        event_type: str,
        event_data: Dict[str, Any],
        session_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AnalyticsEvent:
        """
        Track an analytics event
        
        Args:
            db: Database session
            user_id: User ID (optional for anonymous events)
            event_type: Type of event
            event_data: Event data
            session_id: Session ID
            ip_address: Client IP address
            user_agent: Client user agent
            
        Returns:
            Created analytics event
        """
        try:
            event = AnalyticsEvent(
                user_id=user_id,
                event_type=event_type,
                event_data=event_data,
                session_id=session_id,
                ip_address=ip_address,
                user_agent=user_agent,
                timestamp=datetime.utcnow()
            )
            
            db.add(event)
            await db.flush()
            await db.commit()
            
            # Send to CloudWatch
            dimensions = {'EventType': event_type}
            if user_id:
                dimensions['UserID'] = str(user_id)
            
            cloudwatch_service.put_metric('AnalyticsEvent', 1, 'Count', dimensions)
            
            logger.debug(f"Tracked event: {event_type} for user {user_id}")
            return event
        
        except Exception as e:
            logger.error(f"Failed to track event: {e}")
            await db.rollback()
            raise
    
    async def track_user_activity(
        self,
        db: AsyncSession,
        user_id: UUID,
        activity_type: str,
        activity_data: Dict[str, Any],
        session_id: Optional[str] = None
    ) -> UserActivity:
        """
        Track user activity
        
        Args:
            db: Database session
            user_id: User ID
            activity_type: Type of activity
            activity_data: Activity data
            session_id: Session ID
            
        Returns:
            Created user activity
        """
        try:
            activity = UserActivity(
                user_id=user_id,
                activity_type=activity_type,
                activity_data=activity_data,
                session_id=session_id,
                timestamp=datetime.utcnow()
            )
            
            db.add(activity)
            await db.flush()
            await db.commit()
            
            # Update user's last activity
            user = await db.get(User, user_id)
            if user:
                user.last_activity_at = datetime.utcnow()
                await db.commit()
            
            # Send to CloudWatch
            cloudwatch_service.record_user_activity(activity_type, str(user_id))
            
            return activity
        
        except Exception as e:
            logger.error(f"Failed to track user activity: {e}")
            await db.rollback()
            raise
    
    async def record_usage(
        self,
        db: AsyncSession,
        user_id: UUID,
        resource_type: str,
        resource_id: Optional[str] = None,
        usage_amount: float = 1.0,
        usage_unit: str = 'count',
        metadata: Optional[Dict[str, Any]] = None
    ) -> UsageRecord:
        """
        Record usage for billing/quota tracking
        
        Args:
            db: Database session
            user_id: User ID
            resource_type: Type of resource used
            resource_id: Optional resource ID
            usage_amount: Amount of usage
            usage_unit: Unit of measurement
            metadata: Additional metadata
            
        Returns:
            Created usage record
        """
        try:
            usage_record = UsageRecord(
                user_id=user_id,
                resource_type=resource_type,
                resource_id=resource_id,
                usage_amount=usage_amount,
                usage_unit=usage_unit,
                metadata=metadata or {},
                timestamp=datetime.utcnow()
            )
            
            db.add(usage_record)
            await db.flush()
            await db.commit()
            
            # Send to CloudWatch
            dimensions = {
                'ResourceType': resource_type,
                'UsageUnit': usage_unit,
                'UserID': str(user_id)
            }
            cloudwatch_service.put_metric('ResourceUsage', usage_amount, 'Count', dimensions)
            
            return usage_record
        
        except Exception as e:
            logger.error(f"Failed to record usage: {e}")
            await db.rollback()
            raise
    
    async def get_user_statistics(
        self,
        db: AsyncSession,
        user_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive user statistics
        
        Args:
            db: Database session
            user_id: User ID
            start_date: Start date for statistics
            end_date: End date for statistics
            
        Returns:
            User statistics
        """
        try:
            if not start_date:
                start_date = datetime.utcnow() - timedelta(days=30)
            if not end_date:
                end_date = datetime.utcnow()
            
            # Document statistics
            doc_stats = await db.execute(
                func.count(Document.id).label('total_documents'),
                func.sum(Document.file_size).label('total_size'),
                func.count(Document.id).filter(Document.is_processed == True).label('processed_documents')
            ).filter(
                and_(
                    Document.user_id == user_id,
                    Document.uploaded_at >= start_date,
                    Document.uploaded_at <= end_date
                )
            )
            doc_result = doc_stats.first()
            
            # Processing statistics
            processing_stats = await db.execute(
                func.count(ProcessingJob.id).label('total_jobs'),
                func.count(ProcessingJob.id).filter(ProcessingJob.status == 'completed').label('completed_jobs'),
                func.count(ProcessingJob.id).filter(ProcessingJob.status == 'failed').label('failed_jobs'),
                func.avg(
                    func.extract('epoch', ProcessingJob.completed_at - ProcessingJob.started_at)
                ).label('avg_processing_time')
            ).filter(
                and_(
                    ProcessingJob.user_id == user_id,
                    ProcessingJob.created_at >= start_date,
                    ProcessingJob.created_at <= end_date
                )
            )
            processing_result = processing_stats.first()
            
            # Dataset statistics
            dataset_count = await db.scalar(
                func.count(Dataset.id).filter(
                    and_(
                        Dataset.user_id == user_id,
                        Dataset.created_at >= start_date,
                        Dataset.created_at <= end_date
                    )
                )
            )
            
            # Activity statistics
            activity_stats = await db.execute(
                func.count(UserActivity.id).label('total_activities'),
                func.count(distinct(UserActivity.session_id)).label('unique_sessions')
            ).filter(
                and_(
                    UserActivity.user_id == user_id,
                    UserActivity.timestamp >= start_date,
                    UserActivity.timestamp <= end_date
                )
            )
            activity_result = activity_stats.first()
            
            # Usage statistics
            usage_stats = await db.execute(
                func.count(UsageRecord.id).label('total_usage_records'),
                func.sum(UsageRecord.usage_amount).label('total_usage_amount')
            ).filter(
                and_(
                    UsageRecord.user_id == user_id,
                    UsageRecord.timestamp >= start_date,
                    UsageRecord.timestamp <= end_date
                )
            )
            usage_result = usage_stats.first()
            
            return {
                'user_id': str(user_id),
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                },
                'documents': {
                    'total': doc_result.total_documents or 0,
                    'processed': doc_result.processed_documents or 0,
                    'total_size_bytes': doc_result.total_size or 0,
                    'total_size_mb': round((doc_result.total_size or 0) / 1024 / 1024, 2)
                },
                'processing': {
                    'total_jobs': processing_result.total_jobs or 0,
                    'completed_jobs': processing_result.completed_jobs or 0,
                    'failed_jobs': processing_result.failed_jobs or 0,
                    'success_rate': (
                        (processing_result.completed_jobs or 0) / 
                        max(processing_result.total_jobs or 1, 1) * 100
                    ),
                    'avg_processing_time_seconds': processing_result.avg_processing_time or 0
                },
                'datasets': {
                    'generated': dataset_count or 0
                },
                'activity': {
                    'total_activities': activity_result.total_activities or 0,
                    'unique_sessions': activity_result.unique_sessions or 0
                },
                'usage': {
                    'total_records': usage_result.total_usage_records or 0,
                    'total_amount': usage_result.total_usage_amount or 0
                }
            }
        
        except Exception as e:
            logger.error(f"Failed to get user statistics: {e}")
            raise
    
    async def get_system_statistics(
        self,
        db: AsyncSession,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get system-wide statistics
        
        Args:
            db: Database session
            start_date: Start date for statistics
            end_date: End date for statistics
            
        Returns:
            System statistics
        """
        try:
            if not start_date:
                start_date = datetime.utcnow() - timedelta(days=7)
            if not end_date:
                end_date = datetime.utcnow()
            
            # User statistics
            user_stats = await db.execute(
                func.count(User.id).label('total_users'),
                func.count(User.id).filter(User.created_at >= start_date).label('new_users'),
                func.count(User.id).filter(User.last_activity_at >= start_date).label('active_users')
            )
            user_result = user_stats.first()
            
            # Document statistics
            doc_stats = await db.execute(
                func.count(Document.id).label('total_documents'),
                func.count(Document.id).filter(Document.uploaded_at >= start_date).label('new_documents'),
                func.sum(Document.file_size).label('total_storage')
            )
            doc_result = doc_stats.first()
            
            # Processing statistics
            processing_stats = await db.execute(
                func.count(ProcessingJob.id).label('total_jobs'),
                func.count(ProcessingJob.id).filter(ProcessingJob.created_at >= start_date).label('new_jobs'),
                func.count(ProcessingJob.id).filter(
                    and_(
                        ProcessingJob.status == 'completed',
                        ProcessingJob.completed_at >= start_date
                    )
                ).label('completed_jobs'),
                func.count(ProcessingJob.id).filter(
                    and_(
                        ProcessingJob.status == 'failed',
                        ProcessingJob.completed_at >= start_date
                    )
                ).label('failed_jobs')
            )
            processing_result = processing_stats.first()
            
            # Dataset statistics
            dataset_count = await db.scalar(
                func.count(Dataset.id).filter(Dataset.created_at >= start_date)
            )
            
            # Event statistics
            event_stats = await db.execute(
                func.count(AnalyticsEvent.id).label('total_events'),
                func.count(distinct(AnalyticsEvent.session_id)).label('unique_sessions')
            ).filter(AnalyticsEvent.timestamp >= start_date)
            event_result = event_stats.first()
            
            return {
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                },
                'users': {
                    'total': user_result.total_users or 0,
                    'new': user_result.new_users or 0,
                    'active': user_result.active_users or 0
                },
                'documents': {
                    'total': doc_result.total_documents or 0,
                    'new': doc_result.new_documents or 0,
                    'total_storage_bytes': doc_result.total_storage or 0,
                    'total_storage_gb': round((doc_result.total_storage or 0) / 1024 / 1024 / 1024, 2)
                },
                'processing': {
                    'total_jobs': processing_result.total_jobs or 0,
                    'new_jobs': processing_result.new_jobs or 0,
                    'completed_jobs': processing_result.completed_jobs or 0,
                    'failed_jobs': processing_result.failed_jobs or 0,
                    'success_rate': (
                        (processing_result.completed_jobs or 0) / 
                        max(processing_result.new_jobs or 1, 1) * 100
                    )
                },
                'datasets': {
                    'generated': dataset_count or 0
                },
                'events': {
                    'total': event_result.total_events or 0,
                    'unique_sessions': event_result.unique_sessions or 0
                }
            }
        
        except Exception as e:
            logger.error(f"Failed to get system statistics: {e}")
            raise
    
    async def get_usage_trends(
        self,
        db: AsyncSession,
        user_id: Optional[UUID] = None,
        days: int = 30,
        granularity: str = 'daily'
    ) -> List[Dict[str, Any]]:
        """
        Get usage trends over time
        
        Args:
            db: Database session
            user_id: Optional user ID (system-wide if None)
            days: Number of days to look back
            granularity: Granularity (daily, hourly)
            
        Returns:
            List of usage data points
        """
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            if granularity == 'daily':
                date_format = '%Y-%m-%d'
                date_trunc = 'day'
            elif granularity == 'hourly':
                date_format = '%Y-%m-%d %H:00'
                date_trunc = 'hour'
            else:
                raise ValueError(f"Invalid granularity: {granularity}")
            
            # Build query filters
            filters = [ProcessingJob.created_at >= start_date]
            if user_id:
                filters.append(ProcessingJob.user_id == user_id)
            
            # Get processing trends
            query = db.query(
                func.date_trunc(date_trunc, ProcessingJob.created_at).label('period'),
                func.count(ProcessingJob.id).label('total_jobs'),
                func.count(ProcessingJob.id).filter(ProcessingJob.status == 'completed').label('completed'),
                func.count(ProcessingJob.id).filter(ProcessingJob.status == 'failed').label('failed')
            ).filter(and_(*filters)).group_by('period').order_by('period')
            
            results = await db.execute(query)
            
            trends = []
            for row in results:
                trends.append({
                    'period': row.period.strftime(date_format),
                    'total_jobs': row.total_jobs,
                    'completed_jobs': row.completed,
                    'failed_jobs': row.failed,
                    'success_rate': (row.completed / max(row.total_jobs, 1)) * 100
                })
            
            return trends
        
        except Exception as e:
            logger.error(f"Failed to get usage trends: {e}")
            raise
    
    async def get_popular_features(
        self,
        db: AsyncSession,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get most popular features/activities
        
        Args:
            db: Database session
            start_date: Start date for analysis
            end_date: End date for analysis
            limit: Maximum number of results
            
        Returns:
            List of popular features
        """
        try:
            if not start_date:
                start_date = datetime.utcnow() - timedelta(days=30)
            if not end_date:
                end_date = datetime.utcnow()
            
            # Get activity type popularity
            query = db.query(
                UserActivity.activity_type,
                func.count(UserActivity.id).label('usage_count'),
                func.count(distinct(UserActivity.user_id)).label('unique_users')
            ).filter(
                and_(
                    UserActivity.timestamp >= start_date,
                    UserActivity.timestamp <= end_date
                )
            ).group_by(UserActivity.activity_type).order_by(desc('usage_count')).limit(limit)
            
            results = await db.execute(query)
            
            features = []
            for row in results:
                features.append({
                    'feature': row.activity_type,
                    'usage_count': row.usage_count,
                    'unique_users': row.unique_users,
                    'avg_usage_per_user': row.usage_count / max(row.unique_users, 1)
                })
            
            return features
        
        except Exception as e:
            logger.error(f"Failed to get popular features: {e}")
            raise
    
    async def generate_user_report(
        self,
        db: AsyncSession,
        user_id: UUID,
        report_type: str = 'monthly',
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive user report
        
        Args:
            db: Database session
            user_id: User ID
            report_type: Type of report (daily, weekly, monthly)
            start_date: Optional start date
            end_date: Optional end date
            
        Returns:
            User report data
        """
        try:
            # Determine date range based on report type
            if not start_date or not end_date:
                end_date = datetime.utcnow()
                if report_type == 'daily':
                    start_date = end_date - timedelta(days=1)
                elif report_type == 'weekly':
                    start_date = end_date - timedelta(days=7)
                elif report_type == 'monthly':
                    start_date = end_date - timedelta(days=30)
                else:
                    start_date = end_date - timedelta(days=30)
            
            # Get user info
            user = await db.get(User, user_id)
            if not user:
                raise ValueError(f"User {user_id} not found")
            
            # Get comprehensive statistics
            statistics = await self.get_user_statistics(db, user_id, start_date, end_date)
            
            # Get usage trends
            trends = await self.get_usage_trends(db, user_id, days=(end_date - start_date).days)
            
            # Get top activities
            activities_query = db.query(
                UserActivity.activity_type,
                func.count(UserActivity.id).label('count')
            ).filter(
                and_(
                    UserActivity.user_id == user_id,
                    UserActivity.timestamp >= start_date,
                    UserActivity.timestamp <= end_date
                )
            ).group_by(UserActivity.activity_type).order_by(desc('count')).limit(5)
            
            activities_result = await db.execute(activities_query)
            top_activities = [
                {'activity': row.activity_type, 'count': row.count}
                for row in activities_result
            ]
            
            report = {
                'report_type': report_type,
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                },
                'user': {
                    'id': str(user.id),
                    'email': user.email,
                    'name': user.full_name,
                    'subscription_tier': user.subscription_tier
                },
                'statistics': statistics,
                'trends': trends,
                'top_activities': top_activities,
                'generated_at': datetime.utcnow().isoformat()
            }
            
            return report
        
        except Exception as e:
            logger.error(f"Failed to generate user report: {e}")
            raise


# Global instance
analytics_service = AnalyticsService()