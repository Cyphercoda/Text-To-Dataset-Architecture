"""
Database models package

This module imports all database models to ensure they are registered
with SQLAlchemy and available for migrations and queries.
"""

# Import base classes first
from .base import Base, BaseModel, AuditableModel, TimestampMixin, UUIDMixin

# Import all model modules to register them
from .user import (
    User, ApiKey, UsageRecord, UserSession,
    UserRole, UserStatus
)

from .document import (
    Document, ProcessingJob, AnalysisResult, Dataset,
    DocumentStatus, ProcessingStage, JobStatus
)

from .chat import (
    ChatSession, ChatMessage, ChatAttachment, ChatTemplate, ConversationSummary,
    ChatSessionStatus, MessageType, MessageStatus, AttachmentType
)

from .analytics import (
    AnalyticsEvent, SystemMetric, PerformanceLog, AuditLog,
    Alert, Notification, FeatureFlag,
    MetricType, EventType, NotificationChannel
)

# Export commonly used models and types
__all__ = [
    # Base classes
    "Base",
    "BaseModel", 
    "AuditableModel",
    "TimestampMixin",
    "UUIDMixin",
    
    # User models
    "User",
    "ApiKey", 
    "UsageRecord",
    "UserSession",
    "UserRole",
    "UserStatus",
    
    # Document models
    "Document",
    "ProcessingJob",
    "AnalysisResult", 
    "Dataset",
    "DocumentStatus",
    "ProcessingStage",
    "JobStatus",
    
    # Chat models
    "ChatSession",
    "ChatMessage",
    "ChatAttachment",
    "ChatTemplate",
    "ConversationSummary",
    "ChatSessionStatus",
    "MessageType",
    "MessageStatus", 
    "AttachmentType",
    
    # Analytics models
    "AnalyticsEvent",
    "SystemMetric",
    "PerformanceLog",
    "AuditLog",
    "Alert",
    "Notification",
    "FeatureFlag",
    "MetricType",
    "EventType",
    "NotificationChannel",
]