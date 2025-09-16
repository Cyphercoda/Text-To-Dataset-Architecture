"""
Analytics and monitoring related database models
"""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any

from sqlalchemy import (
    Column, String, Boolean, Integer, DateTime, Text, Float,
    ForeignKey, Index, JSON, BigInteger, Numeric
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship

from app.models.base import BaseModel, register_model


class MetricType(str, Enum):
    """Metric type enumeration"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class EventType(str, Enum):
    """Event type enumeration"""
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    DOCUMENT_UPLOAD = "document_upload"
    PROCESSING_START = "processing_start"
    PROCESSING_COMPLETE = "processing_complete"
    PROCESSING_FAILED = "processing_failed"
    CHAT_MESSAGE = "chat_message"
    API_REQUEST = "api_request"
    ERROR = "error"
    SYSTEM = "system"


class NotificationChannel(str, Enum):
    """Notification channel enumeration"""
    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"
    SMS = "sms"
    PUSH = "push"


@register_model("analytics_event")
class AnalyticsEvent(BaseModel):
    """Analytics event model for tracking user actions and system events"""
    
    __tablename__ = "analytics_events"
    
    # Basic Information
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    session_id = Column(String(255), nullable=True)
    event_type = Column(String(100), nullable=False)
    event_name = Column(String(255), nullable=False)
    
    # Event Details
    category = Column(String(100), nullable=True)
    action = Column(String(100), nullable=True)
    label = Column(String(255), nullable=True)
    value = Column(Float, nullable=True)
    
    # Context Information
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    referrer = Column(String(500), nullable=True)
    page_url = Column(String(500), nullable=True)
    
    # Device Information
    device_type = Column(String(50), nullable=True)  # desktop, mobile, tablet
    device_os = Column(String(100), nullable=True)
    browser = Column(String(100), nullable=True)
    screen_resolution = Column(String(50), nullable=True)
    
    # Geographic Information
    country = Column(String(100), nullable=True)
    region = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    timezone = Column(String(50), nullable=True)
    
    # Performance Metrics
    response_time_ms = Column(Integer, nullable=True)
    page_load_time_ms = Column(Integer, nullable=True)
    
    # Custom Properties
    properties = Column(JSON, nullable=True)
    
    # Indexes
    __table_args__ = (
        Index('ix_analytics_events_user_id', 'user_id'),
        Index('ix_analytics_events_event_type', 'event_type'),
        Index('ix_analytics_events_created_at', 'created_at'),
        Index('ix_analytics_events_event_name', 'event_name'),
        Index('ix_analytics_events_user_created', 'user_id', 'created_at'),
        Index('ix_analytics_events_type_created', 'event_type', 'created_at'),
    )
    
    def __repr__(self) -> str:
        return f"<AnalyticsEvent(id={self.id}, type={self.event_type}, name={self.event_name})>"


@register_model("system_metric")
class SystemMetric(BaseModel):
    """System metrics model for monitoring application performance"""
    
    __tablename__ = "system_metrics"
    
    # Basic Information
    metric_name = Column(String(255), nullable=False)
    metric_type = Column(String(50), nullable=False)
    
    # Metric Data
    value = Column(Numeric(precision=20, scale=6), nullable=False)
    unit = Column(String(50), nullable=True)
    
    # Labels and Tags
    labels = Column(JSON, nullable=True)  # Key-value pairs for metric dimensions
    tags = Column(ARRAY(String), nullable=True)
    
    # Context
    source = Column(String(255), nullable=True)  # Source system/service
    environment = Column(String(50), nullable=True)  # production, staging, etc.
    
    # Timestamp (can be different from created_at for historical data)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('ix_system_metrics_name', 'metric_name'),
        Index('ix_system_metrics_timestamp', 'timestamp'),
        Index('ix_system_metrics_name_timestamp', 'metric_name', 'timestamp'),
        Index('ix_system_metrics_source', 'source'),
    )
    
    def __repr__(self) -> str:
        return f"<SystemMetric(id={self.id}, name={self.metric_name}, value={self.value})>"


@register_model("performance_log")
class PerformanceLog(BaseModel):
    """Performance logging model for tracking request/response times and resource usage"""
    
    __tablename__ = "performance_logs"
    
    # Request Information
    request_id = Column(String(255), nullable=False, index=True)
    endpoint = Column(String(500), nullable=False)
    method = Column(String(10), nullable=False)
    
    # User Context
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Timing Information
    started_at = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=False)
    duration_ms = Column(Integer, nullable=False)
    
    # Response Information
    status_code = Column(Integer, nullable=False)
    response_size_bytes = Column(Integer, nullable=True)
    
    # Resource Usage
    cpu_time_ms = Column(Float, nullable=True)
    memory_usage_mb = Column(Float, nullable=True)
    db_query_count = Column(Integer, nullable=True)
    db_query_time_ms = Column(Float, nullable=True)
    
    # External Service Calls
    external_api_calls = Column(Integer, default=0, nullable=False)
    external_api_time_ms = Column(Float, nullable=True)
    
    # Error Information
    error_message = Column(Text, nullable=True)
    error_type = Column(String(255), nullable=True)
    
    # Additional Data
    metadata = Column(JSON, nullable=True)
    
    # Indexes
    __table_args__ = (
        Index('ix_performance_logs_request_id', 'request_id'),
        Index('ix_performance_logs_endpoint', 'endpoint'),
        Index('ix_performance_logs_user_id', 'user_id'),
        Index('ix_performance_logs_started_at', 'started_at'),
        Index('ix_performance_logs_duration', 'duration_ms'),
        Index('ix_performance_logs_status_code', 'status_code'),
    )
    
    def __repr__(self) -> str:
        return f"<PerformanceLog(id={self.id}, endpoint={self.endpoint}, duration={self.duration_ms}ms)>"


@register_model("audit_log")
class AuditLog(BaseModel):
    """Audit log model for tracking important system actions and changes"""
    
    __tablename__ = "audit_logs"
    
    # Basic Information
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    action = Column(String(255), nullable=False)
    resource_type = Column(String(100), nullable=False)
    resource_id = Column(String(255), nullable=True)
    
    # Action Details
    description = Column(Text, nullable=True)
    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)
    
    # Context Information
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    request_id = Column(String(255), nullable=True)
    
    # Result
    success = Column(Boolean, nullable=False)
    error_message = Column(Text, nullable=True)
    
    # Additional Metadata
    metadata = Column(JSON, nullable=True)
    
    # Relationships
    user = relationship("User")
    
    # Indexes
    __table_args__ = (
        Index('ix_audit_logs_user_id', 'user_id'),
        Index('ix_audit_logs_action', 'action'),
        Index('ix_audit_logs_resource_type', 'resource_type'),
        Index('ix_audit_logs_resource_id', 'resource_id'),
        Index('ix_audit_logs_created_at', 'created_at'),
        Index('ix_audit_logs_success', 'success'),
    )
    
    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, action={self.action}, resource={self.resource_type})>"


@register_model("alert")
class Alert(BaseModel):
    """Alert model for system monitoring and notifications"""
    
    __tablename__ = "alerts"
    
    # Basic Information
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Alert Configuration
    metric_name = Column(String(255), nullable=False)
    condition = Column(String(50), nullable=False)  # greater_than, less_than, equals, etc.
    threshold_value = Column(Float, nullable=False)
    
    # Current State
    is_active = Column(Boolean, default=True, nullable=False)
    current_value = Column(Float, nullable=True)
    triggered_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Severity and Priority
    severity = Column(String(20), default="medium", nullable=False)  # low, medium, high, critical
    priority = Column(Integer, default=3, nullable=False)  # 1-5
    
    # Notification Settings
    notification_channels = Column(ARRAY(String), nullable=True)
    notification_sent = Column(Boolean, default=False, nullable=False)
    notification_sent_at = Column(DateTime(timezone=True), nullable=True)
    
    # Escalation
    escalation_timeout_minutes = Column(Integer, default=60, nullable=False)
    escalated = Column(Boolean, default=False, nullable=False)
    escalated_at = Column(DateTime(timezone=True), nullable=True)
    
    # Additional Configuration
    evaluation_window_minutes = Column(Integer, default=5, nullable=False)
    evaluation_frequency_minutes = Column(Integer, default=1, nullable=False)
    
    # Metadata
    tags = Column(ARRAY(String), nullable=True)
    metadata = Column(JSON, nullable=True)
    
    # Indexes
    __table_args__ = (
        Index('ix_alerts_metric_name', 'metric_name'),
        Index('ix_alerts_is_active', 'is_active'),
        Index('ix_alerts_severity', 'severity'),
        Index('ix_alerts_triggered_at', 'triggered_at'),
        Index('ix_alerts_priority', 'priority'),
    )
    
    def __repr__(self) -> str:
        return f"<Alert(id={self.id}, name={self.name}, metric={self.metric_name})>"
    
    @property
    def is_triggered(self) -> bool:
        """Check if alert is currently triggered"""
        return self.triggered_at is not None and self.resolved_at is None
    
    def trigger(self, current_value: float) -> None:
        """Trigger the alert"""
        self.current_value = current_value
        self.triggered_at = datetime.utcnow()
        self.resolved_at = None
        self.notification_sent = False
    
    def resolve(self, current_value: float) -> None:
        """Resolve the alert"""
        self.current_value = current_value
        self.resolved_at = datetime.utcnow()
        self.escalated = False


@register_model("notification")
class Notification(BaseModel):
    """Notification model for tracking sent notifications"""
    
    __tablename__ = "notifications"
    
    # Basic Information
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    
    # Notification Properties
    notification_type = Column(String(100), nullable=False)
    channel = Column(String(50), nullable=False)
    priority = Column(String(20), default="medium", nullable=False)
    
    # Status
    sent = Column(Boolean, default=False, nullable=False)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    read = Column(Boolean, default=False, nullable=False)
    read_at = Column(DateTime(timezone=True), nullable=True)
    
    # Delivery Information
    recipient = Column(String(255), nullable=True)  # email, phone, etc.
    delivery_status = Column(String(50), nullable=True)  # sent, delivered, failed, etc.
    delivery_error = Column(Text, nullable=True)
    
    # Reference Information
    reference_type = Column(String(100), nullable=True)
    reference_id = Column(String(255), nullable=True)
    
    # Additional Data
    data = Column(JSON, nullable=True)  # Additional notification data
    metadata = Column(JSON, nullable=True)
    
    # Relationships
    user = relationship("User")
    
    # Indexes
    __table_args__ = (
        Index('ix_notifications_user_id', 'user_id'),
        Index('ix_notifications_notification_type', 'notification_type'),
        Index('ix_notifications_channel', 'channel'),
        Index('ix_notifications_sent', 'sent'),
        Index('ix_notifications_read', 'read'),
        Index('ix_notifications_created_at', 'created_at'),
        Index('ix_notifications_user_read', 'user_id', 'read'),
    )
    
    def __repr__(self) -> str:
        return f"<Notification(id={self.id}, type={self.notification_type}, sent={self.sent})>"
    
    def mark_sent(self) -> None:
        """Mark notification as sent"""
        self.sent = True
        self.sent_at = datetime.utcnow()
    
    def mark_read(self) -> None:
        """Mark notification as read"""
        self.read = True
        self.read_at = datetime.utcnow()


@register_model("feature_flag")
class FeatureFlag(BaseModel):
    """Feature flag model for controlling application features"""
    
    __tablename__ = "feature_flags"
    
    # Basic Information
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    
    # Flag Configuration
    is_enabled = Column(Boolean, default=False, nullable=False)
    rollout_percentage = Column(Integer, default=0, nullable=False)  # 0-100
    
    # Targeting Rules
    user_targeting_rules = Column(JSON, nullable=True)  # Rules for targeting specific users
    environment_filter = Column(ARRAY(String), nullable=True)  # production, staging, etc.
    
    # Scheduling
    enabled_at = Column(DateTime(timezone=True), nullable=True)
    disabled_at = Column(DateTime(timezone=True), nullable=True)
    
    # Usage Tracking
    evaluation_count = Column(Integer, default=0, nullable=False)
    last_evaluated_at = Column(DateTime(timezone=True), nullable=True)
    
    # Additional Metadata
    tags = Column(ARRAY(String), nullable=True)
    metadata = Column(JSON, nullable=True)
    
    # Indexes
    __table_args__ = (
        Index('ix_feature_flags_name', 'name'),
        Index('ix_feature_flags_is_enabled', 'is_enabled'),
        Index('ix_feature_flags_rollout_percentage', 'rollout_percentage'),
    )
    
    def __repr__(self) -> str:
        return f"<FeatureFlag(id={self.id}, name={self.name}, enabled={self.is_enabled})>"
    
    def evaluate(self, user_id: str = None, context: dict = None) -> bool:
        """Evaluate feature flag for given user and context"""
        if not self.is_enabled:
            return False
        
        # Update evaluation count
        self.evaluation_count += 1
        self.last_evaluated_at = datetime.utcnow()
        
        # Check rollout percentage
        if self.rollout_percentage < 100:
            # Simple hash-based rollout (in real implementation, use more sophisticated logic)
            import hashlib
            hash_input = f"{self.name}:{user_id or 'anonymous'}"
            hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
            if (hash_value % 100) >= self.rollout_percentage:
                return False
        
        return True