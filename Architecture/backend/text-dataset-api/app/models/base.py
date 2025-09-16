"""
Base model classes with common fields and functionality
"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Column, DateTime, String, Boolean, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import declarative_base

# Base class for all models
Base = declarative_base()


class TimestampMixin:
    """Mixin for created_at and updated_at timestamp fields"""
    
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="Timestamp when the record was created"
    )
    
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        doc="Timestamp when the record was last updated"
    )


class UUIDMixin:
    """Mixin for UUID primary key"""
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        doc="Unique identifier"
    )


class SoftDeleteMixin:
    """Mixin for soft delete functionality"""
    
    is_deleted = Column(
        Boolean,
        default=False,
        nullable=False,
        doc="Whether the record is soft deleted"
    )
    
    deleted_at = Column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp when the record was deleted"
    )


class AuditMixin:
    """Mixin for audit trail fields"""
    
    created_by = Column(
        UUID(as_uuid=True),
        nullable=True,
        doc="ID of the user who created the record"
    )
    
    updated_by = Column(
        UUID(as_uuid=True),
        nullable=True,
        doc="ID of the user who last updated the record"
    )


class BaseModel(Base, UUIDMixin, TimestampMixin):
    """Base model class with common fields"""
    
    __abstract__ = True
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(id={self.id})>"
    
    def to_dict(self) -> dict[str, Any]:
        """Convert model to dictionary"""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }
    
    @classmethod
    def get_table_name(cls) -> str:
        """Get the table name"""
        return cls.__tablename__


class AuditableModel(BaseModel, SoftDeleteMixin, AuditMixin):
    """Base model with audit trail and soft delete"""
    
    __abstract__ = True


class NameDescriptionMixin:
    """Mixin for models with name and description fields"""
    
    name = Column(
        String(255),
        nullable=False,
        doc="Name of the entity"
    )
    
    description = Column(
        Text,
        nullable=True,
        doc="Description of the entity"
    )


class SlugMixin:
    """Mixin for models with slug field"""
    
    slug = Column(
        String(255),
        nullable=False,
        unique=True,
        doc="URL-friendly identifier"
    )


class MetadataMixin:
    """Mixin for storing JSON metadata"""
    
    metadata_ = Column(
        "metadata",  # Column name in database
        Text,
        nullable=True,
        doc="Additional metadata in JSON format"
    )


class StatusMixin:
    """Mixin for models with status field"""
    
    @declared_attr
    def status(cls):
        return Column(
            String(50),
            nullable=False,
            default="active",
            doc="Status of the entity"
        )


class VersionMixin:
    """Mixin for versioning support"""
    
    version = Column(
        String(50),
        nullable=False,
        default="1.0.0",
        doc="Version of the entity"
    )


class TagsMixin:
    """Mixin for storing tags"""
    
    tags = Column(
        Text,
        nullable=True,
        doc="Comma-separated tags"
    )
    
    def get_tags(self) -> list[str]:
        """Get tags as a list"""
        if not self.tags:
            return []
        return [tag.strip() for tag in self.tags.split(",") if tag.strip()]
    
    def set_tags(self, tags: list[str]) -> None:
        """Set tags from a list"""
        self.tags = ",".join(tags) if tags else None


# Utility functions for models
def generate_uuid() -> str:
    """Generate a new UUID as string"""
    return str(uuid.uuid4())


def utc_now() -> datetime:
    """Get current UTC datetime"""
    return datetime.utcnow()


# Model registry for dynamic model access
class ModelRegistry:
    """Registry to keep track of all models"""
    
    _models: dict[str, type] = {}
    
    @classmethod
    def register(cls, name: str, model_class: type) -> None:
        """Register a model class"""
        cls._models[name] = model_class
    
    @classmethod
    def get(cls, name: str) -> type:
        """Get a model class by name"""
        return cls._models.get(name)
    
    @classmethod
    def get_all(cls) -> dict[str, type]:
        """Get all registered models"""
        return cls._models.copy()


# Global model registry instance
model_registry = ModelRegistry()


def register_model(name: str):
    """Decorator to register models in the registry"""
    def decorator(model_class):
        model_registry.register(name, model_class)
        return model_class
    return decorator