"""
Chat and AI assistant related database models
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any

from sqlalchemy import (
    Column, String, Boolean, Integer, DateTime, Text, Float,
    ForeignKey, Index, JSON, BigInteger
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship

from app.models.base import BaseModel, AuditableModel, register_model


class ChatSessionStatus(str, Enum):
    """Chat session status enumeration"""
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"
    SUSPENDED = "suspended"


class MessageType(str, Enum):
    """Message type enumeration"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    ERROR = "error"


class MessageStatus(str, Enum):
    """Message status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AttachmentType(str, Enum):
    """Attachment type enumeration"""
    FILE = "file"
    IMAGE = "image"
    DOCUMENT = "document"
    AUDIO = "audio"
    VIDEO = "video"


@register_model("chat_session")
class ChatSession(AuditableModel):
    """Chat session model"""
    
    __tablename__ = "chat_sessions"
    
    # Basic Information
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Session Configuration
    model_name = Column(String(100), default="gpt-4", nullable=False)
    model_config = Column(JSON, nullable=True)  # temperature, max_tokens, etc.
    system_prompt = Column(Text, nullable=True)
    
    # Status and State
    status = Column(String(50), default=ChatSessionStatus.ACTIVE, nullable=False)
    is_pinned = Column(Boolean, default=False, nullable=False)
    message_count = Column(Integer, default=0, nullable=False)
    
    # Context and Memory
    context_window_size = Column(Integer, default=4000, nullable=False)
    document_context = Column(ARRAY(UUID(as_uuid=True)), nullable=True)  # Document IDs for context
    memory_summary = Column(Text, nullable=True)  # Summarized conversation history
    
    # Activity Tracking
    last_message_at = Column(DateTime(timezone=True), nullable=True)
    last_user_activity = Column(DateTime(timezone=True), nullable=True)
    total_tokens_used = Column(Integer, default=0, nullable=False)
    
    # Cost Tracking
    total_cost_cents = Column(Integer, default=0, nullable=False)
    
    # Additional Metadata
    metadata = Column(JSON, nullable=True)
    tags = Column(ARRAY(String), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('ix_chat_sessions_user_id', 'user_id'),
        Index('ix_chat_sessions_status', 'status'),
        Index('ix_chat_sessions_created_at', 'created_at'),
        Index('ix_chat_sessions_last_message_at', 'last_message_at'),
        Index('ix_chat_sessions_user_status', 'user_id', 'status'),
    )
    
    def __repr__(self) -> str:
        return f"<ChatSession(id={self.id}, name={self.name}, messages={self.message_count})>"
    
    @property
    def is_active(self) -> bool:
        """Check if session is active"""
        return self.status == ChatSessionStatus.ACTIVE and not self.is_deleted
    
    @property
    def total_cost_dollars(self) -> float:
        """Get total cost in dollars"""
        return self.total_cost_cents / 100.0
    
    @property
    def has_context_documents(self) -> bool:
        """Check if session has document context"""
        return bool(self.document_context and len(self.document_context) > 0)
    
    def add_message_cost(self, cost_cents: int) -> None:
        """Add to total cost and token usage"""
        self.total_cost_cents += cost_cents
    
    def add_token_usage(self, tokens: int) -> None:
        """Add to total token usage"""
        self.total_tokens_used += tokens
    
    def update_activity(self) -> None:
        """Update last activity timestamp"""
        self.last_user_activity = datetime.utcnow()
    
    def increment_message_count(self) -> None:
        """Increment message count and update last message timestamp"""
        self.message_count += 1
        self.last_message_at = datetime.utcnow()


@register_model("chat_message")
class ChatMessage(BaseModel):
    """Chat message model"""
    
    __tablename__ = "chat_messages"
    
    # Basic Information
    session_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id"), nullable=False)
    message_type = Column(String(50), nullable=False)  # user, assistant, system, error
    content = Column(Text, nullable=False)
    
    # Message Properties
    role = Column(String(50), nullable=True)  # For OpenAI API compatibility
    status = Column(String(50), default=MessageStatus.COMPLETED, nullable=False)
    
    # Processing Information
    processing_started_at = Column(DateTime(timezone=True), nullable=True)
    processing_completed_at = Column(DateTime(timezone=True), nullable=True)
    response_time_ms = Column(Integer, nullable=True)
    
    # Token Usage
    input_tokens = Column(Integer, default=0, nullable=False)
    output_tokens = Column(Integer, default=0, nullable=False)
    total_tokens = Column(Integer, default=0, nullable=False)
    
    # Cost Tracking
    cost_cents = Column(Integer, default=0, nullable=False)
    
    # Model Information
    model_name = Column(String(100), nullable=True)
    model_version = Column(String(100), nullable=True)
    temperature = Column(Float, nullable=True)
    max_tokens = Column(Integer, nullable=True)
    
    # Quality Metrics
    confidence_score = Column(Float, nullable=True)
    relevance_score = Column(Float, nullable=True)
    
    # Error Handling
    error_message = Column(Text, nullable=True)
    error_code = Column(String(100), nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    
    # User Feedback
    user_rating = Column(String(20), nullable=True)  # positive, negative, neutral
    user_feedback = Column(Text, nullable=True)
    
    # Additional Data
    metadata = Column(JSON, nullable=True)
    
    # Relationships
    session = relationship("ChatSession", back_populates="messages")
    attachments = relationship("ChatAttachment", back_populates="message", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('ix_chat_messages_session_id', 'session_id'),
        Index('ix_chat_messages_message_type', 'message_type'),
        Index('ix_chat_messages_created_at', 'created_at'),
        Index('ix_chat_messages_status', 'status'),
        Index('ix_chat_messages_session_created', 'session_id', 'created_at'),
    )
    
    def __repr__(self) -> str:
        return f"<ChatMessage(id={self.id}, type={self.message_type}, session_id={self.session_id})>"
    
    @property
    def is_user_message(self) -> bool:
        """Check if message is from user"""
        return self.message_type == MessageType.USER
    
    @property
    def is_assistant_message(self) -> bool:
        """Check if message is from assistant"""
        return self.message_type == MessageType.ASSISTANT
    
    @property
    def cost_dollars(self) -> float:
        """Get cost in dollars"""
        return self.cost_cents / 100.0
    
    @property
    def processing_time_seconds(self) -> Optional[float]:
        """Get processing time in seconds"""
        if self.processing_started_at and self.processing_completed_at:
            return (self.processing_completed_at - self.processing_started_at).total_seconds()
        return None
    
    @property
    def has_attachments(self) -> bool:
        """Check if message has attachments"""
        return bool(self.attachments)
    
    def mark_processing_started(self) -> None:
        """Mark message processing as started"""
        self.status = MessageStatus.PROCESSING
        self.processing_started_at = datetime.utcnow()
    
    def mark_processing_completed(self, content: str, tokens: dict = None) -> None:
        """Mark message processing as completed"""
        self.status = MessageStatus.COMPLETED
        self.content = content
        self.processing_completed_at = datetime.utcnow()
        
        if tokens:
            self.input_tokens = tokens.get('input_tokens', 0)
            self.output_tokens = tokens.get('output_tokens', 0)
            self.total_tokens = tokens.get('total_tokens', 0)
    
    def mark_processing_failed(self, error_message: str, error_code: str = None) -> None:
        """Mark message processing as failed"""
        self.status = MessageStatus.FAILED
        self.error_message = error_message
        self.error_code = error_code
        self.processing_completed_at = datetime.utcnow()
    
    def add_user_feedback(self, rating: str, feedback: str = None) -> None:
        """Add user feedback to message"""
        self.user_rating = rating
        self.user_feedback = feedback


@register_model("chat_attachment")
class ChatAttachment(BaseModel):
    """Chat message attachment model"""
    
    __tablename__ = "chat_attachments"
    
    # Basic Information
    message_id = Column(UUID(as_uuid=True), ForeignKey("chat_messages.id"), nullable=False)
    filename = Column(String(500), nullable=False)
    original_filename = Column(String(500), nullable=False)
    
    # File Properties
    file_size = Column(BigInteger, nullable=False)
    content_type = Column(String(100), nullable=False)
    attachment_type = Column(String(50), nullable=False)
    file_hash = Column(String(64), nullable=True)  # SHA-256
    
    # Storage
    s3_bucket = Column(String(255), nullable=True)
    s3_key = Column(String(1000), nullable=True)
    
    # Processing Status
    is_processed = Column(Boolean, default=False, nullable=False)
    extracted_text = Column(Text, nullable=True)
    
    # Additional Metadata
    metadata = Column(JSON, nullable=True)
    
    # Relationships
    message = relationship("ChatMessage", back_populates="attachments")
    
    # Indexes
    __table_args__ = (
        Index('ix_chat_attachments_message_id', 'message_id'),
        Index('ix_chat_attachments_attachment_type', 'attachment_type'),
        Index('ix_chat_attachments_created_at', 'created_at'),
        Index('ix_chat_attachments_s3_key', 's3_key'),
    )
    
    def __repr__(self) -> str:
        return f"<ChatAttachment(id={self.id}, filename={self.filename}, type={self.attachment_type})>"
    
    @property
    def file_size_mb(self) -> float:
        """Get file size in MB"""
        return self.file_size / (1024 * 1024)
    
    @property
    def is_image(self) -> bool:
        """Check if attachment is an image"""
        return self.attachment_type == AttachmentType.IMAGE
    
    @property
    def is_document(self) -> bool:
        """Check if attachment is a document"""
        return self.attachment_type == AttachmentType.DOCUMENT


@register_model("chat_template")
class ChatTemplate(AuditableModel):
    """Chat template model for reusable prompts and configurations"""
    
    __tablename__ = "chat_templates"
    
    # Basic Information
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)  # NULL for system templates
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Template Content
    system_prompt = Column(Text, nullable=True)
    initial_message = Column(Text, nullable=True)
    
    # Configuration
    model_config = Column(JSON, nullable=True)
    suggested_model = Column(String(100), nullable=True)
    
    # Usage and Sharing
    is_public = Column(Boolean, default=False, nullable=False)
    is_featured = Column(Boolean, default=False, nullable=False)
    use_count = Column(Integer, default=0, nullable=False)
    
    # Categorization
    category = Column(String(100), nullable=True)
    tags = Column(ARRAY(String), nullable=True)
    
    # Additional Metadata
    metadata = Column(JSON, nullable=True)
    
    # Relationships
    user = relationship("User")
    
    # Indexes
    __table_args__ = (
        Index('ix_chat_templates_user_id', 'user_id'),
        Index('ix_chat_templates_is_public', 'is_public'),
        Index('ix_chat_templates_category', 'category'),
        Index('ix_chat_templates_created_at', 'created_at'),
        Index('ix_chat_templates_use_count', 'use_count'),
    )
    
    def __repr__(self) -> str:
        return f"<ChatTemplate(id={self.id}, name={self.name}, public={self.is_public})>"
    
    @property
    def is_system_template(self) -> bool:
        """Check if template is a system template"""
        return self.user_id is None
    
    def increment_use_count(self) -> None:
        """Increment template usage count"""
        self.use_count += 1


@register_model("conversation_summary")
class ConversationSummary(BaseModel):
    """Conversation summary model for long chat sessions"""
    
    __tablename__ = "conversation_summaries"
    
    # Basic Information
    session_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id"), nullable=False)
    summary = Column(Text, nullable=False)
    
    # Summary Metadata
    message_count = Column(Integer, nullable=False)
    start_message_id = Column(UUID(as_uuid=True), nullable=True)
    end_message_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Processing Information
    model_used = Column(String(100), nullable=True)
    tokens_used = Column(Integer, default=0, nullable=False)
    cost_cents = Column(Integer, default=0, nullable=False)
    
    # Quality Metrics
    coherence_score = Column(Float, nullable=True)
    completeness_score = Column(Float, nullable=True)
    
    # Additional Metadata
    metadata = Column(JSON, nullable=True)
    
    # Relationships
    session = relationship("ChatSession")
    
    # Indexes
    __table_args__ = (
        Index('ix_conversation_summaries_session_id', 'session_id'),
        Index('ix_conversation_summaries_created_at', 'created_at'),
    )
    
    def __repr__(self) -> str:
        return f"<ConversationSummary(id={self.id}, session_id={self.session_id}, messages={self.message_count})>"
    
    @property
    def cost_dollars(self) -> float:
        """Get cost in dollars"""
        return self.cost_cents / 100.0