"""
Core application configuration settings
"""

import os
import secrets
from functools import lru_cache
from typing import Any, Dict, List, Optional, Union

from pydantic import (
    BaseSettings,
    PostgresDsn,
    RedisDsn,
    AnyHttpUrl,
    validator,
    Field,
)


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Application
    PROJECT_NAME: str = "Text Dataset Platform API"
    PROJECT_VERSION: str = "1.0.0"
    ENVIRONMENT: str = Field("development", env="ENVIRONMENT")
    DEBUG: bool = Field(False, env="DEBUG")
    
    # Server
    HOST: str = Field("0.0.0.0", env="HOST")
    PORT: int = Field(8000, env="PORT")
    WORKERS: int = Field(4, env="WORKERS")
    
    # API
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = Field(secrets.token_urlsafe(32), env="SECRET_KEY")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(7, env="REFRESH_TOKEN_EXPIRE_DAYS")
    PASSWORD_MIN_LENGTH: int = 8
    SESSION_MAX_AGE: int = Field(3600, env="SESSION_MAX_AGE")  # 1 hour
    
    # CORS
    ALLOWED_ORIGINS: List[str] = Field(
        ["http://localhost:3000", "https://textdataset.com"],
        env="ALLOWED_ORIGINS"
    )
    ALLOWED_HOSTS: List[str] = Field(["*"], env="ALLOWED_HOSTS")
    
    # Database
    DATABASE_URL: PostgresDsn = Field(..., env="DATABASE_URL")
    DATABASE_POOL_SIZE: int = Field(10, env="DATABASE_POOL_SIZE")
    DATABASE_MAX_OVERFLOW: int = Field(20, env="DATABASE_MAX_OVERFLOW")
    DATABASE_POOL_TIMEOUT: int = Field(30, env="DATABASE_POOL_TIMEOUT")
    
    # Redis
    REDIS_URL: RedisDsn = Field("redis://localhost:6379", env="REDIS_URL")
    REDIS_DB: int = Field(0, env="REDIS_DB")
    REDIS_PASSWORD: Optional[str] = Field(None, env="REDIS_PASSWORD")
    REDIS_POOL_SIZE: int = Field(10, env="REDIS_POOL_SIZE")
    
    # AWS Configuration
    AWS_ACCESS_KEY_ID: Optional[str] = Field(None, env="AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: Optional[str] = Field(None, env="AWS_SECRET_ACCESS_KEY")
    AWS_REGION: str = Field("us-east-1", env="AWS_REGION")
    AWS_S3_BUCKET: str = Field(..., env="AWS_S3_BUCKET")
    AWS_S3_PRESIGNED_URL_EXPIRE_SECONDS: int = Field(3600, env="AWS_S3_PRESIGNED_URL_EXPIRE_SECONDS")
    
    # AWS Cognito
    AWS_COGNITO_USER_POOL_ID: Optional[str] = Field(None, env="AWS_COGNITO_USER_POOL_ID")
    AWS_COGNITO_CLIENT_ID: Optional[str] = Field(None, env="AWS_COGNITO_CLIENT_ID")
    AWS_COGNITO_CLIENT_SECRET: Optional[str] = Field(None, env="AWS_COGNITO_CLIENT_SECRET")
    
    # AWS CloudWatch
    AWS_CLOUDWATCH_LOG_GROUP: str = Field("/aws/textdataset/api", env="AWS_CLOUDWATCH_LOG_GROUP")
    AWS_CLOUDWATCH_LOG_STREAM: str = Field("application-logs", env="AWS_CLOUDWATCH_LOG_STREAM")
    
    # AWS SQS
    AWS_SQS_PROCESSING_QUEUE_URL: Optional[str] = Field(None, env="AWS_SQS_PROCESSING_QUEUE_URL")
    AWS_SQS_NOTIFICATION_QUEUE_URL: Optional[str] = Field(None, env="AWS_SQS_NOTIFICATION_QUEUE_URL")
    
    # Celery
    CELERY_BROKER_URL: str = Field("redis://localhost:6379/1", env="CELERY_BROKER_URL")
    CELERY_RESULT_BACKEND: str = Field("redis://localhost:6379/2", env="CELERY_RESULT_BACKEND")
    CELERY_TASK_SOFT_TIME_LIMIT: int = Field(300, env="CELERY_TASK_SOFT_TIME_LIMIT")  # 5 minutes
    CELERY_TASK_TIME_LIMIT: int = Field(600, env="CELERY_TASK_TIME_LIMIT")  # 10 minutes
    CELERY_WORKER_CONCURRENCY: int = Field(4, env="CELERY_WORKER_CONCURRENCY")
    
    # File Processing
    MAX_FILE_SIZE: int = Field(100 * 1024 * 1024, env="MAX_FILE_SIZE")  # 100MB
    MAX_FILES_PER_UPLOAD: int = Field(50, env="MAX_FILES_PER_UPLOAD")
    SUPPORTED_FILE_TYPES: List[str] = Field([
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain",
        "text/csv",
        "application/json",
        "application/xml",
        "text/xml"
    ], env="SUPPORTED_FILE_TYPES")
    
    # Processing Configuration
    DEFAULT_PROCESSING_CONFIG: Dict[str, Any] = {
        "extract_entities": True,
        "analyze_sentiment": True,
        "classify_document": True,
        "extract_key_phrases": True,
        "quality_threshold": 0.8,
        "output_formats": ["json"],
    }
    
    # Rate Limiting
    RATE_LIMIT_CALLS: int = Field(100, env="RATE_LIMIT_CALLS")
    RATE_LIMIT_PERIOD: int = Field(60, env="RATE_LIMIT_PERIOD")  # seconds
    
    # WebSocket
    WEBSOCKET_HEARTBEAT_INTERVAL: int = Field(30, env="WEBSOCKET_HEARTBEAT_INTERVAL")
    WEBSOCKET_MAX_CONNECTIONS: int = Field(1000, env="WEBSOCKET_MAX_CONNECTIONS")
    
    # Monitoring
    ENABLE_METRICS: bool = Field(True, env="ENABLE_METRICS")
    METRICS_PORT: int = Field(9090, env="METRICS_PORT")
    
    # Logging
    LOG_LEVEL: str = Field("INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = Field("json", env="LOG_FORMAT")  # json or text
    LOG_TO_FILE: bool = Field(False, env="LOG_TO_FILE")
    LOG_FILE_PATH: str = Field("logs/app.log", env="LOG_FILE_PATH")
    LOG_ROTATION_SIZE: str = Field("100MB", env="LOG_ROTATION_SIZE")
    LOG_RETENTION_COUNT: int = Field(10, env="LOG_RETENTION_COUNT")
    
    # Email Configuration (for notifications)
    EMAIL_HOST: Optional[str] = Field(None, env="EMAIL_HOST")
    EMAIL_PORT: int = Field(587, env="EMAIL_PORT")
    EMAIL_USERNAME: Optional[str] = Field(None, env="EMAIL_USERNAME")
    EMAIL_PASSWORD: Optional[str] = Field(None, env="EMAIL_PASSWORD")
    EMAIL_USE_TLS: bool = Field(True, env="EMAIL_USE_TLS")
    EMAIL_FROM: Optional[str] = Field(None, env="EMAIL_FROM")
    
    # Third-party Services
    OPENAI_API_KEY: Optional[str] = Field(None, env="OPENAI_API_KEY")
    ANTHROPIC_API_KEY: Optional[str] = Field(None, env="ANTHROPIC_API_KEY")
    HUGGING_FACE_API_KEY: Optional[str] = Field(None, env="HUGGING_FACE_API_KEY")
    
    # Analytics
    ANALYTICS_RETENTION_DAYS: int = Field(90, env="ANALYTICS_RETENTION_DAYS")
    ENABLE_USER_ANALYTICS: bool = Field(True, env="ENABLE_USER_ANALYTICS")
    
    # Testing
    TESTING: bool = Field(False, env="TESTING")
    TEST_DATABASE_URL: Optional[str] = Field(None, env="TEST_DATABASE_URL")
    
    # Feature Flags
    ENABLE_CHAT: bool = Field(True, env="ENABLE_CHAT")
    ENABLE_REAL_TIME_PROCESSING: bool = Field(True, env="ENABLE_REAL_TIME_PROCESSING")
    ENABLE_BATCH_PROCESSING: bool = Field(True, env="ENABLE_BATCH_PROCESSING")
    ENABLE_ANALYTICS: bool = Field(True, env="ENABLE_ANALYTICS")
    ENABLE_WEBHOOKS: bool = Field(True, env="ENABLE_WEBHOOKS")
    
    @validator("ALLOWED_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    @validator("ALLOWED_HOSTS", pre=True)
    def assemble_allowed_hosts(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    @validator("SUPPORTED_FILE_TYPES", pre=True)
    def assemble_file_types(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    @property
    def database_url_sync(self) -> str:
        """Get synchronous database URL (for Alembic)"""
        return str(self.DATABASE_URL).replace("postgresql+asyncpg://", "postgresql://")
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.ENVIRONMENT.lower() in ("development", "dev", "local")
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.ENVIRONMENT.lower() in ("production", "prod")
    
    @property
    def is_testing(self) -> bool:
        """Check if running in testing environment"""
        return self.TESTING or self.ENVIRONMENT.lower() in ("test", "testing")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Global settings instance
settings = get_settings()