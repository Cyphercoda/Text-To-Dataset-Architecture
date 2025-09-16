"""
User-related database models
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List

from sqlalchemy import (
    Column, String, Boolean, Integer, DateTime, Text, 
    ForeignKey, UniqueConstraint, Index, JSON, Float
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel, AuditableModel, register_model


class UserRole(str, Enum):
    """User role enumeration"""
    FREE = "free"
    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"
    ADMIN = "admin"


class UserStatus(str, Enum):
    """User status enumeration"""
    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    INACTIVE = "inactive"
    BANNED = "banned"


@register_model("user")
class User(AuditableModel):
    """User model"""
    
    __tablename__ = "users"
    
    # Basic Information
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=True, index=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    full_name = Column(String(255), nullable=True)
    
    # Authentication
    hashed_password = Column(String(255), nullable=True)  # None for OAuth users
    is_email_verified = Column(Boolean, default=False, nullable=False)
    email_verification_token = Column(String(255), nullable=True)
    email_verification_sent_at = Column(DateTime(timezone=True), nullable=True)
    
    # Password Reset
    password_reset_token = Column(String(255), nullable=True)
    password_reset_sent_at = Column(DateTime(timezone=True), nullable=True)
    password_reset_expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Profile
    avatar_url = Column(String(500), nullable=True)
    bio = Column(Text, nullable=True)
    company = Column(String(255), nullable=True)
    job_title = Column(String(255), nullable=True)
    location = Column(String(255), nullable=True)
    website = Column(String(500), nullable=True)
    phone = Column(String(50), nullable=True)
    
    # Account Status
    role = Column(String(50), default=UserRole.FREE, nullable=False)
    status = Column(String(50), default=UserStatus.PENDING, nullable=False)
    subscription_tier = Column(String(50), default="free", nullable=False)
    
    # Usage Limits
    api_calls_per_day = Column(Integer, default=100, nullable=False)
    upload_volume_per_day = Column(Integer, default=1000, nullable=False)  # MB
    documents_per_day = Column(Integer, default=10, nullable=False)
    concurrent_uploads = Column(Integer, default=2, nullable=False)
    
    # Usage Tracking
    total_api_calls = Column(Integer, default=0, nullable=False)
    total_documents_processed = Column(Integer, default=0, nullable=False)
    total_storage_used = Column(Integer, default=0, nullable=False)  # bytes
    
    # Activity
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    last_activity_at = Column(DateTime(timezone=True), nullable=True)
    login_count = Column(Integer, default=0, nullable=False)
    
    # OAuth Integration
    google_id = Column(String(255), nullable=True, unique=True)
    github_id = Column(String(255), nullable=True, unique=True)
    microsoft_id = Column(String(255), nullable=True, unique=True)
    
    # AWS Cognito
    cognito_user_id = Column(String(255), nullable=True, unique=True)
    cognito_username = Column(String(255), nullable=True)
    
    # Preferences
    timezone = Column(String(50), default="UTC", nullable=False)
    language = Column(String(10), default="en", nullable=False)
    date_format = Column(String(50), default="YYYY-MM-DD", nullable=False)
    theme = Column(String(20), default="system", nullable=False)
    
    # Notifications
    email_notifications = Column(Boolean, default=True, nullable=False)
    push_notifications = Column(Boolean, default=True, nullable=False)
    marketing_emails = Column(Boolean, default=False, nullable=False)
    
    # Privacy
    profile_visibility = Column(String(20), default="public", nullable=False)
    data_sharing_consent = Column(Boolean, default=False, nullable=False)
    analytics_consent = Column(Boolean, default=True, nullable=False)
    
    # Additional Data
    metadata = Column(JSON, nullable=True)
    
    # Relationships
    documents = relationship("Document", back_populates="user")
    processing_jobs = relationship("ProcessingJob", back_populates="user")
    chat_sessions = relationship("ChatSession", back_populates="user")
    api_keys = relationship("ApiKey", back_populates="user")
    usage_records = relationship("UsageRecord", back_populates="user")
    
    # Indexes
    __table_args__ = (
        Index('ix_users_email_status', 'email', 'status'),
        Index('ix_users_role_status', 'role', 'status'),
        Index('ix_users_created_at', 'created_at'),
        Index('ix_users_last_activity', 'last_activity_at'),
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"
    
    @property
    def display_name(self) -> str:
        """Get user's display name"""
        if self.full_name:
            return self.full_name
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        if self.first_name:
            return self.first_name
        if self.username:
            return self.username
        return self.email.split('@')[0]
    
    @property
    def is_active(self) -> bool:
        """Check if user is active"""
        return self.status == UserStatus.ACTIVE and not self.is_deleted
    
    @property
    def is_premium(self) -> bool:
        """Check if user has premium subscription"""
        return self.role in [UserRole.PRO, UserRole.ENTERPRISE]
    
    @property
    def can_upload(self) -> bool:
        """Check if user can upload files"""
        return self.is_active and self.status != UserStatus.SUSPENDED
    
    def update_last_activity(self) -> None:
        """Update last activity timestamp"""
        self.last_activity_at = datetime.utcnow()
    
    def increment_login_count(self) -> None:
        """Increment login count and update last login"""
        self.login_count += 1
        self.last_login_at = datetime.utcnow()
        self.update_last_activity()


@register_model("api_key")
class ApiKey(BaseModel):
    """API Key model for programmatic access"""
    
    __tablename__ = "api_keys"
    
    # Basic Information
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    key_hash = Column(String(255), nullable=False, unique=True)
    key_prefix = Column(String(20), nullable=False)  # First few chars for identification
    
    # Status and Limits
    is_active = Column(Boolean, default=True, nullable=False)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    usage_count = Column(Integer, default=0, nullable=False)
    
    # Rate Limiting
    rate_limit_per_minute = Column(Integer, default=60, nullable=False)
    rate_limit_per_hour = Column(Integer, default=1000, nullable=False)
    rate_limit_per_day = Column(Integer, default=10000, nullable=False)
    
    # Expiration
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Permissions (JSON array of allowed endpoints/actions)
    permissions = Column(JSON, nullable=True)
    
    # Metadata
    description = Column(Text, nullable=True)
    metadata = Column(JSON, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="api_keys")
    
    # Indexes
    __table_args__ = (
        Index('ix_api_keys_user_id', 'user_id'),
        Index('ix_api_keys_key_hash', 'key_hash'),
        Index('ix_api_keys_is_active', 'is_active'),
    )
    
    def __repr__(self) -> str:
        return f"<ApiKey(id={self.id}, name={self.name}, user_id={self.user_id})>"
    
    @property
    def is_expired(self) -> bool:
        """Check if API key is expired"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_valid(self) -> bool:
        """Check if API key is valid for use"""
        return self.is_active and not self.is_expired
    
    def increment_usage(self) -> None:
        """Increment usage count and update last used timestamp"""
        self.usage_count += 1
        self.last_used_at = datetime.utcnow()


@register_model("usage_record")
class UsageRecord(BaseModel):
    """Usage tracking model"""
    
    __tablename__ = "usage_records"
    
    # User and Date
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    date = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Usage Metrics
    api_calls = Column(Integer, default=0, nullable=False)
    documents_processed = Column(Integer, default=0, nullable=False)
    storage_used = Column(Integer, default=0, nullable=False)  # bytes
    processing_time = Column(Float, default=0.0, nullable=False)  # seconds
    
    # Costs (in cents)
    total_cost = Column(Integer, default=0, nullable=False)
    api_cost = Column(Integer, default=0, nullable=False)
    storage_cost = Column(Integer, default=0, nullable=False)
    processing_cost = Column(Integer, default=0, nullable=False)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="usage_records")
    
    # Indexes
    __table_args__ = (
        UniqueConstraint('user_id', 'date', name='uq_usage_records_user_date'),
        Index('ix_usage_records_user_id_date', 'user_id', 'date'),
        Index('ix_usage_records_date', 'date'),
    )
    
    def __repr__(self) -> str:
        return f"<UsageRecord(id={self.id}, user_id={self.user_id}, date={self.date})>"


@register_model("user_session")
class UserSession(BaseModel):
    """User session model for tracking active sessions"""
    
    __tablename__ = "user_sessions"
    
    # User and Session Info
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    session_token = Column(String(255), nullable=False, unique=True)
    refresh_token = Column(String(255), nullable=True)
    
    # Session Details
    ip_address = Column(String(45), nullable=True)  # IPv6 support
    user_agent = Column(Text, nullable=True)
    device_info = Column(JSON, nullable=True)
    location = Column(String(255), nullable=True)
    
    # Status and Timing
    is_active = Column(Boolean, default=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    last_activity_at = Column(DateTime(timezone=True), nullable=False)
    
    # Relationships
    user = relationship("User")
    
    # Indexes
    __table_args__ = (
        Index('ix_user_sessions_user_id', 'user_id'),
        Index('ix_user_sessions_session_token', 'session_token'),
        Index('ix_user_sessions_is_active', 'is_active'),
        Index('ix_user_sessions_expires_at', 'expires_at'),
    )
    
    def __repr__(self) -> str:
        return f"<UserSession(id={self.id}, user_id={self.user_id}, active={self.is_active})>"
    
    @property
    def is_expired(self) -> bool:
        """Check if session is expired"""
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_valid(self) -> bool:
        """Check if session is valid"""
        return self.is_active and not self.is_expired
    
    def update_activity(self) -> None:
        """Update last activity timestamp"""
        self.last_activity_at = datetime.utcnow()
    
    def deactivate(self) -> None:
        """Deactivate session"""
        self.is_active = False