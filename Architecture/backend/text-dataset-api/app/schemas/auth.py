"""
Authentication schemas for request/response validation
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, validator


# Request Schemas
class UserRegisterRequest(BaseModel):
    """User registration request schema"""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    confirm_password: str = Field(..., min_length=8, max_length=100)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    company: Optional[str] = Field(None, max_length=255)
    accept_terms: bool = Field(..., description="User must accept terms")
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v
    
    @validator('email')
    def email_lowercase(cls, v):
        return v.lower()
    
    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123!",
                "confirm_password": "SecurePass123!",
                "first_name": "John",
                "last_name": "Doe",
                "company": "Acme Corp",
                "accept_terms": True
            }
        }


class UserLoginRequest(BaseModel):
    """User login request schema"""
    email: EmailStr
    password: str = Field(..., min_length=1)
    remember_me: bool = Field(False, description="Extended session duration")
    
    @validator('email')
    def email_lowercase(cls, v):
        return v.lower()
    
    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123!",
                "remember_me": False
            }
        }


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema"""
    refresh_token: str = Field(..., description="JWT refresh token")
    
    class Config:
        schema_extra = {
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }


class EmailVerificationRequest(BaseModel):
    """Email verification request schema"""
    token: str = Field(..., description="Email verification token")
    
    class Config:
        schema_extra = {
            "example": {
                "token": "abc123def456ghi789"
            }
        }


class PasswordResetRequest(BaseModel):
    """Password reset request schema"""
    email: EmailStr
    
    @validator('email')
    def email_lowercase(cls, v):
        return v.lower()
    
    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com"
            }
        }


class PasswordResetConfirmRequest(BaseModel):
    """Password reset confirmation request schema"""
    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=8, max_length=100)
    confirm_password: str = Field(..., min_length=8, max_length=100)
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "token": "abc123def456ghi789",
                "new_password": "NewSecurePass123!",
                "confirm_password": "NewSecurePass123!"
            }
        }


class ChangePasswordRequest(BaseModel):
    """Change password request schema"""
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=100)
    confirm_password: str = Field(..., min_length=8, max_length=100)
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "current_password": "OldPassword123!",
                "new_password": "NewSecurePass123!",
                "confirm_password": "NewSecurePass123!"
            }
        }


class CreateApiKeyRequest(BaseModel):
    """Create API key request schema"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    permissions: Optional[List[str]] = Field(None, description="API permissions")
    expires_at: Optional[datetime] = Field(None, description="Expiration date")
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Production API Key",
                "description": "API key for production environment",
                "permissions": ["documents:read", "documents:write"],
                "expires_at": "2024-12-31T23:59:59Z"
            }
        }


# Response Schemas
class TokenResponse(BaseModel):
    """Token response schema"""
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int = Field(..., description="Access token expiration in seconds")
    
    class Config:
        schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "Bearer",
                "expires_in": 1800
            }
        }


class UserResponse(BaseModel):
    """User response schema"""
    id: UUID
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    full_name: Optional[str]
    company: Optional[str]
    role: str
    status: str
    subscription_tier: str
    is_email_verified: bool
    avatar_url: Optional[str]
    created_at: datetime
    last_login_at: Optional[datetime]
    
    # Usage limits
    api_calls_per_day: int
    upload_volume_per_day: int
    documents_per_day: int
    concurrent_uploads: int
    
    # Preferences
    timezone: str
    language: str
    theme: str
    
    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "user@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "full_name": "John Doe",
                "company": "Acme Corp",
                "role": "basic",
                "status": "active",
                "subscription_tier": "basic",
                "is_email_verified": True,
                "avatar_url": "https://example.com/avatar.jpg",
                "created_at": "2024-01-01T00:00:00Z",
                "last_login_at": "2024-01-02T00:00:00Z",
                "api_calls_per_day": 1000,
                "upload_volume_per_day": 1000,
                "documents_per_day": 100,
                "concurrent_uploads": 5,
                "timezone": "UTC",
                "language": "en",
                "theme": "light"
            }
        }


class AuthResponse(BaseModel):
    """Authentication response schema"""
    user: UserResponse
    tokens: TokenResponse
    message: str = "Authentication successful"
    
    class Config:
        schema_extra = {
            "example": {
                "user": UserResponse.Config.schema_extra["example"],
                "tokens": TokenResponse.Config.schema_extra["example"],
                "message": "Authentication successful"
            }
        }


class ApiKeyResponse(BaseModel):
    """API key response schema"""
    id: UUID
    name: str
    key_prefix: str
    description: Optional[str]
    permissions: List[str]
    is_active: bool
    created_at: datetime
    last_used_at: Optional[datetime]
    expires_at: Optional[datetime]
    usage_count: int
    
    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Production API Key",
                "key_prefix": "sk_live_",
                "description": "API key for production environment",
                "permissions": ["documents:read", "documents:write"],
                "is_active": True,
                "created_at": "2024-01-01T00:00:00Z",
                "last_used_at": "2024-01-02T00:00:00Z",
                "expires_at": "2024-12-31T23:59:59Z",
                "usage_count": 150
            }
        }


class CreateApiKeyResponse(BaseModel):
    """Create API key response schema"""
    api_key: ApiKeyResponse
    secret_key: str = Field(..., description="Secret API key (shown only once)")
    message: str = "API key created successfully. Please save the secret key as it won't be shown again."
    
    class Config:
        schema_extra = {
            "example": {
                "api_key": ApiKeyResponse.Config.schema_extra["example"],
                "secret_key": "api_key_secret_example_do_not_use_in_production",
                "message": "API key created successfully. Please save the secret key as it won't be shown again."
            }
        }


class MessageResponse(BaseModel):
    """Generic message response schema"""
    message: str
    success: bool = True
    
    class Config:
        schema_extra = {
            "example": {
                "message": "Operation completed successfully",
                "success": True
            }
        }


class SessionResponse(BaseModel):
    """Session response schema"""
    id: UUID
    user_id: UUID
    ip_address: Optional[str]
    user_agent: Optional[str]
    is_active: bool
    created_at: datetime
    last_activity_at: datetime
    expires_at: datetime
    
    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "user_id": "456e7890-e89b-12d3-a456-426614174000",
                "ip_address": "192.168.1.1",
                "user_agent": "Mozilla/5.0...",
                "is_active": True,
                "created_at": "2024-01-01T00:00:00Z",
                "last_activity_at": "2024-01-01T01:00:00Z",
                "expires_at": "2024-01-08T00:00:00Z"
            }
        }


# OAuth Schemas
class OAuthLoginRequest(BaseModel):
    """OAuth login request schema"""
    provider: str = Field(..., description="OAuth provider (google, github, microsoft)")
    access_token: str = Field(..., description="OAuth access token")
    id_token: Optional[str] = Field(None, description="OAuth ID token")
    
    class Config:
        schema_extra = {
            "example": {
                "provider": "google",
                "access_token": "ya29.a0AfH6SMBx...",
                "id_token": "eyJhbGciOiJSUzI1NiIsImtpZCI..."
            }
        }


# Update Profile Schemas
class UpdateProfileRequest(BaseModel):
    """Update profile request schema"""
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    company: Optional[str] = Field(None, max_length=255)
    bio: Optional[str] = Field(None, max_length=1000)
    job_title: Optional[str] = Field(None, max_length=255)
    location: Optional[str] = Field(None, max_length=255)
    website: Optional[str] = Field(None, max_length=500)
    phone: Optional[str] = Field(None, max_length=50)
    avatar_url: Optional[str] = Field(None, max_length=500)
    
    class Config:
        schema_extra = {
            "example": {
                "first_name": "John",
                "last_name": "Doe",
                "company": "Acme Corp",
                "bio": "Software developer passionate about AI",
                "job_title": "Senior Developer",
                "location": "San Francisco, CA",
                "website": "https://johndoe.com",
                "phone": "+1-555-0123",
                "avatar_url": "https://example.com/avatar.jpg"
            }
        }


class UpdatePreferencesRequest(BaseModel):
    """Update preferences request schema"""
    timezone: Optional[str] = Field(None, max_length=50)
    language: Optional[str] = Field(None, max_length=10)
    date_format: Optional[str] = Field(None, max_length=50)
    theme: Optional[str] = Field(None, pattern="^(light|dark|system)$")
    email_notifications: Optional[bool]
    push_notifications: Optional[bool]
    marketing_emails: Optional[bool]
    
    class Config:
        schema_extra = {
            "example": {
                "timezone": "America/New_York",
                "language": "en",
                "date_format": "MM/DD/YYYY",
                "theme": "dark",
                "email_notifications": True,
                "push_notifications": False,
                "marketing_emails": False
            }
        }