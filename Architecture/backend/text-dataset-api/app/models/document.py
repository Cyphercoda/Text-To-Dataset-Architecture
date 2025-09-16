"""
Document and processing-related database models
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any

from sqlalchemy import (
    Column, String, Boolean, Integer, DateTime, Text, Float,
    ForeignKey, Index, JSON, LargeBinary, BigInteger
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship

from app.models.base import BaseModel, AuditableModel, register_model


class DocumentStatus(str, Enum):
    """Document processing status enumeration"""
    UPLOADING = "uploading"
    UPLOADED = "uploaded"
    VALIDATING = "validating"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ProcessingStage(str, Enum):
    """Processing pipeline stages"""
    VALIDATION = "validation"
    EXTRACTION = "extraction"
    NLP_ANALYSIS = "nlp_analysis"
    ENTITY_EXTRACTION = "entity_extraction"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    CLASSIFICATION = "classification"
    KEY_PHRASE_EXTRACTION = "key_phrase_extraction"
    DATASET_GENERATION = "dataset_generation"
    QUALITY_ASSESSMENT = "quality_assessment"
    COMPLETED = "completed"


class JobStatus(str, Enum):
    """Processing job status enumeration"""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRY = "retry"


@register_model("document")
class Document(AuditableModel):
    """Document model"""
    
    __tablename__ = "documents"
    
    # Basic Information
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    filename = Column(String(500), nullable=False)
    original_filename = Column(String(500), nullable=False)
    file_size = Column(BigInteger, nullable=False)  # bytes
    content_type = Column(String(100), nullable=False)
    
    # File Storage
    s3_bucket = Column(String(255), nullable=True)
    s3_key = Column(String(1000), nullable=True)
    s3_version_id = Column(String(255), nullable=True)
    storage_class = Column(String(50), default="STANDARD", nullable=False)
    
    # Processing Status
    status = Column(String(50), default=DocumentStatus.UPLOADING, nullable=False)
    current_stage = Column(String(100), default=ProcessingStage.VALIDATION, nullable=False)
    progress_percentage = Column(Float, default=0.0, nullable=False)
    
    # File Properties
    file_hash = Column(String(64), nullable=True)  # SHA-256
    file_format = Column(String(20), nullable=True)  # pdf, docx, txt, etc.
    encoding = Column(String(50), nullable=True)
    language = Column(String(10), nullable=True)  # ISO language code
    page_count = Column(Integer, nullable=True)
    word_count = Column(Integer, nullable=True)
    character_count = Column(Integer, nullable=True)
    
    # Quality Metrics
    quality_score = Column(Float, nullable=True)  # 0.0 to 1.0
    confidence_score = Column(Float, nullable=True)
    readability_score = Column(Float, nullable=True)
    
    # Processing Configuration
    processing_config = Column(JSON, nullable=True)
    
    # Processing Results Summary
    entities_count = Column(Integer, default=0, nullable=False)
    key_phrases_count = Column(Integer, default=0, nullable=False)
    sentiment_score = Column(Float, nullable=True)  # -1.0 to 1.0
    classification_confidence = Column(Float, nullable=True)
    
    # Timing
    upload_started_at = Column(DateTime(timezone=True), nullable=True)
    upload_completed_at = Column(DateTime(timezone=True), nullable=True)
    processing_started_at = Column(DateTime(timezone=True), nullable=True)
    processing_completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Error Tracking
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    
    # Additional Metadata
    metadata = Column(JSON, nullable=True)
    tags = Column(ARRAY(String), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="documents")
    processing_jobs = relationship("ProcessingJob", back_populates="document")
    analysis_results = relationship("AnalysisResult", back_populates="document")
    datasets = relationship("Dataset", back_populates="document")
    
    # Indexes
    __table_args__ = (
        Index('ix_documents_user_id', 'user_id'),
        Index('ix_documents_status', 'status'),
        Index('ix_documents_created_at', 'created_at'),
        Index('ix_documents_user_status', 'user_id', 'status'),
        Index('ix_documents_file_hash', 'file_hash'),
        Index('ix_documents_s3_key', 's3_key'),
    )
    
    def __repr__(self) -> str:
        return f"<Document(id={self.id}, filename={self.filename}, status={self.status})>"
    
    @property
    def is_processed(self) -> bool:
        """Check if document is fully processed"""
        return self.status == DocumentStatus.COMPLETED
    
    @property
    def is_processing(self) -> bool:
        """Check if document is currently processing"""
        return self.status in [DocumentStatus.PROCESSING, DocumentStatus.VALIDATING]
    
    @property
    def processing_duration(self) -> Optional[float]:
        """Get processing duration in seconds"""
        if self.processing_started_at and self.processing_completed_at:
            return (self.processing_completed_at - self.processing_started_at).total_seconds()
        return None
    
    @property
    def file_size_mb(self) -> float:
        """Get file size in MB"""
        return self.file_size / (1024 * 1024)
    
    def update_progress(self, stage: ProcessingStage, percentage: float) -> None:
        """Update processing progress"""
        self.current_stage = stage
        self.progress_percentage = min(max(percentage, 0.0), 100.0)
    
    def mark_processing_started(self) -> None:
        """Mark document processing as started"""
        self.status = DocumentStatus.PROCESSING
        self.processing_started_at = datetime.utcnow()
    
    def mark_processing_completed(self) -> None:
        """Mark document processing as completed"""
        self.status = DocumentStatus.COMPLETED
        self.processing_completed_at = datetime.utcnow()
        self.progress_percentage = 100.0
    
    def mark_processing_failed(self, error_message: str) -> None:
        """Mark document processing as failed"""
        self.status = DocumentStatus.FAILED
        self.error_message = error_message
        self.processing_completed_at = datetime.utcnow()


@register_model("processing_job")
class ProcessingJob(AuditableModel):
    """Processing job model for batch operations"""
    
    __tablename__ = "processing_jobs"
    
    # Basic Information
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    job_name = Column(String(255), nullable=True)
    
    # Job Configuration
    job_type = Column(String(100), nullable=False)  # full_processing, entity_extraction, etc.
    processing_config = Column(JSON, nullable=False)
    priority = Column(Integer, default=5, nullable=False)  # 1-10, higher = more priority
    
    # Status and Progress
    status = Column(String(50), default=JobStatus.QUEUED, nullable=False)
    current_stage = Column(String(100), nullable=True)
    progress_percentage = Column(Float, default=0.0, nullable=False)
    
    # Timing
    queued_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    estimated_completion_at = Column(DateTime(timezone=True), nullable=True)
    
    # Worker Information
    worker_id = Column(String(255), nullable=True)
    worker_node = Column(String(255), nullable=True)
    celery_task_id = Column(String(255), nullable=True)
    
    # Resource Usage
    cpu_time_seconds = Column(Float, default=0.0, nullable=False)
    memory_usage_mb = Column(Float, default=0.0, nullable=False)
    
    # Cost Tracking
    estimated_cost = Column(Integer, default=0, nullable=False)  # cents
    actual_cost = Column(Integer, default=0, nullable=False)  # cents
    
    # Results
    output_s3_key = Column(String(1000), nullable=True)
    output_format = Column(String(50), nullable=True)
    output_size_bytes = Column(BigInteger, nullable=True)
    
    # Error Handling
    error_message = Column(Text, nullable=True)
    error_code = Column(String(100), nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    max_retries = Column(Integer, default=3, nullable=False)
    
    # Additional Data
    metadata = Column(JSON, nullable=True)
    logs = Column(JSON, nullable=True)  # Array of log entries
    
    # Relationships
    user = relationship("User", back_populates="processing_jobs")
    document = relationship("Document", back_populates="processing_jobs")
    
    # Indexes
    __table_args__ = (
        Index('ix_processing_jobs_user_id', 'user_id'),
        Index('ix_processing_jobs_document_id', 'document_id'),
        Index('ix_processing_jobs_status', 'status'),
        Index('ix_processing_jobs_created_at', 'created_at'),
        Index('ix_processing_jobs_priority', 'priority'),
        Index('ix_processing_jobs_celery_task_id', 'celery_task_id'),
    )
    
    def __repr__(self) -> str:
        return f"<ProcessingJob(id={self.id}, status={self.status}, progress={self.progress_percentage}%)>"
    
    @property
    def is_completed(self) -> bool:
        """Check if job is completed"""
        return self.status == JobStatus.COMPLETED
    
    @property
    def is_failed(self) -> bool:
        """Check if job failed"""
        return self.status == JobStatus.FAILED
    
    @property
    def is_running(self) -> bool:
        """Check if job is running"""
        return self.status == JobStatus.RUNNING
    
    @property
    def can_retry(self) -> bool:
        """Check if job can be retried"""
        return self.is_failed and self.retry_count < self.max_retries
    
    @property
    def duration_seconds(self) -> Optional[float]:
        """Get job duration in seconds"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
    
    def start_processing(self, worker_id: str = None) -> None:
        """Mark job as started"""
        self.status = JobStatus.RUNNING
        self.started_at = datetime.utcnow()
        self.worker_id = worker_id
    
    def complete_processing(self, output_s3_key: str = None) -> None:
        """Mark job as completed"""
        self.status = JobStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.progress_percentage = 100.0
        if output_s3_key:
            self.output_s3_key = output_s3_key
    
    def fail_processing(self, error_message: str, error_code: str = None) -> None:
        """Mark job as failed"""
        self.status = JobStatus.FAILED
        self.completed_at = datetime.utcnow()
        self.error_message = error_message
        self.error_code = error_code
    
    def add_log_entry(self, level: str, message: str, data: dict = None) -> None:
        """Add log entry to job"""
        if not self.logs:
            self.logs = []
        
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "message": message,
            "data": data
        }
        self.logs.append(log_entry)
    
    def update_progress(self, stage: str, percentage: float) -> None:
        """Update job progress"""
        self.current_stage = stage
        self.progress_percentage = min(max(percentage, 0.0), 100.0)


@register_model("analysis_result")
class AnalysisResult(BaseModel):
    """Analysis results model for storing NLP processing results"""
    
    __tablename__ = "analysis_results"
    
    # Basic Information
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    analysis_type = Column(String(100), nullable=False)  # entity, sentiment, classification, etc.
    
    # Results Data
    results = Column(JSON, nullable=False)
    confidence_score = Column(Float, nullable=True)
    processing_time_ms = Column(Integer, nullable=True)
    
    # Model Information
    model_name = Column(String(255), nullable=True)
    model_version = Column(String(100), nullable=True)
    
    # Quality Metrics
    quality_score = Column(Float, nullable=True)
    
    # Additional Metadata
    metadata = Column(JSON, nullable=True)
    
    # Relationships
    document = relationship("Document", back_populates="analysis_results")
    
    # Indexes
    __table_args__ = (
        Index('ix_analysis_results_document_id', 'document_id'),
        Index('ix_analysis_results_analysis_type', 'analysis_type'),
        Index('ix_analysis_results_created_at', 'created_at'),
    )
    
    def __repr__(self) -> str:
        return f"<AnalysisResult(id={self.id}, document_id={self.document_id}, type={self.analysis_type})>"


@register_model("dataset")
class Dataset(AuditableModel):
    """Generated dataset model"""
    
    __tablename__ = "datasets"
    
    # Basic Information
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Dataset Properties
    format = Column(String(50), nullable=False)  # json, csv, parquet, huggingface
    size_bytes = Column(BigInteger, nullable=False)
    record_count = Column(Integer, nullable=False)
    column_count = Column(Integer, nullable=True)
    
    # Storage
    s3_bucket = Column(String(255), nullable=True)
    s3_key = Column(String(1000), nullable=True)
    
    # Quality Metrics
    quality_score = Column(Float, nullable=True)
    completeness = Column(Float, nullable=True)
    consistency = Column(Float, nullable=True)
    diversity = Column(Float, nullable=True)
    bias_score = Column(Float, nullable=True)
    training_readiness = Column(Float, nullable=True)
    
    # Usage Tracking
    download_count = Column(Integer, default=0, nullable=False)
    last_downloaded_at = Column(DateTime(timezone=True), nullable=True)
    
    # Versioning
    version = Column(String(50), default="1.0.0", nullable=False)
    parent_dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.id"), nullable=True)
    
    # Additional Metadata
    schema = Column(JSON, nullable=True)  # Dataset schema information
    metadata = Column(JSON, nullable=True)
    tags = Column(ARRAY(String), nullable=True)
    
    # Relationships
    user = relationship("User")
    document = relationship("Document", back_populates="datasets")
    parent_dataset = relationship("Dataset", remote_side="Dataset.id")
    
    # Indexes
    __table_args__ = (
        Index('ix_datasets_user_id', 'user_id'),
        Index('ix_datasets_document_id', 'document_id'),
        Index('ix_datasets_format', 'format'),
        Index('ix_datasets_created_at', 'created_at'),
        Index('ix_datasets_s3_key', 's3_key'),
    )
    
    def __repr__(self) -> str:
        return f"<Dataset(id={self.id}, name={self.name}, format={self.format})>"
    
    @property
    def size_mb(self) -> float:
        """Get dataset size in MB"""
        return self.size_bytes / (1024 * 1024)
    
    def increment_download_count(self) -> None:
        """Increment download count and update timestamp"""
        self.download_count += 1
        self.last_downloaded_at = datetime.utcnow()