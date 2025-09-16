"""
Security utilities for authentication, authorization, and cryptography
"""

import hashlib
import hmac
import secrets
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Union
from passlib.context import CryptContext
from fastapi import HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends, Request

from app.core.config import settings
from app.models.user import User, UserRole

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Security
security = HTTPBearer(auto_error=False)

# Algorithm for JWT
ALGORITHM = "HS256"


class SecurityManager:
    """Centralized security management"""
    
    def __init__(self):
        self.pwd_context = pwd_context
        self.secret_key = settings.SECRET_KEY
        self.algorithm = ALGORITHM
        self.access_token_expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire_days = settings.REFRESH_TOKEN_EXPIRE_DAYS
    
    # Password Management
    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt"""
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def generate_password(self, length: int = 12) -> str:
        """Generate a secure random password"""
        alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    # JWT Token Management
    def create_access_token(
        self, 
        data: Dict[str, Any], 
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        })
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def create_refresh_token(
        self, 
        data: Dict[str, Any], 
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT refresh token"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        })
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def decode_token(self, token: str) -> Dict[str, Any]:
        """Decode and validate JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    def verify_token_type(self, payload: Dict[str, Any], expected_type: str) -> bool:
        """Verify token type (access/refresh)"""
        return payload.get("type") == expected_type
    
    # API Key Management
    def generate_api_key(self, length: int = 32) -> str:
        """Generate a secure API key"""
        return secrets.token_urlsafe(length)
    
    def hash_api_key(self, api_key: str) -> str:
        """Hash API key for secure storage"""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    def verify_api_key(self, api_key: str, hashed_key: str) -> bool:
        """Verify API key against its hash"""
        return hmac.compare_digest(self.hash_api_key(api_key), hashed_key)
    
    # Secure Token Generation
    def generate_secure_token(self, length: int = 32) -> str:
        """Generate a cryptographically secure token"""
        return secrets.token_urlsafe(length)
    
    def generate_verification_token(self) -> str:
        """Generate email verification token"""
        return self.generate_secure_token(32)
    
    def generate_reset_token(self) -> str:
        """Generate password reset token"""
        return self.generate_secure_token(32)
    
    # HMAC Signatures
    def create_signature(self, data: str, key: Optional[str] = None) -> str:
        """Create HMAC signature for data"""
        signing_key = key or self.secret_key
        return hmac.new(
            signing_key.encode(),
            data.encode(),
            hashlib.sha256
        ).hexdigest()
    
    def verify_signature(self, data: str, signature: str, key: Optional[str] = None) -> bool:
        """Verify HMAC signature"""
        signing_key = key or self.secret_key
        expected_signature = self.create_signature(data, signing_key)
        return hmac.compare_digest(signature, expected_signature)
    
    # Rate Limiting Helpers
    def create_rate_limit_key(self, identifier: str, window: str) -> str:
        """Create rate limiting key for Redis"""
        return f"rate_limit:{identifier}:{window}"
    
    # Session Management
    def create_session_token(self) -> str:
        """Create session token"""
        return self.generate_secure_token(48)
    
    def hash_session_token(self, token: str) -> str:
        """Hash session token"""
        return hashlib.sha256(token.encode()).hexdigest()


# Global security manager instance
security_manager = SecurityManager()


class AuthenticationError(HTTPException):
    """Custom authentication error"""
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class AuthorizationError(HTTPException):
    """Custom authorization error"""
    def __init__(self, detail: str = "Insufficient permissions"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )


async def get_current_user_from_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[str]:
    """Extract user ID from JWT token"""
    if not credentials:
        return None
    
    try:
        payload = security_manager.decode_token(credentials.credentials)
        if not security_manager.verify_token_type(payload, "access"):
            raise AuthenticationError("Invalid token type")
        
        user_id: str = payload.get("sub")
        if user_id is None:
            raise AuthenticationError("Invalid token payload")
        
        return user_id
    
    except HTTPException:
        raise
    except Exception:
        raise AuthenticationError("Token validation failed")


async def require_authentication(
    user_id: Optional[str] = Depends(get_current_user_from_token)
) -> str:
    """Require user to be authenticated"""
    if user_id is None:
        raise AuthenticationError("Authentication required")
    return user_id


def require_roles(*allowed_roles: UserRole):
    """Decorator factory for role-based access control"""
    async def role_checker(
        request: Request,
        current_user_id: str = Depends(require_authentication)
    ) -> str:
        # This would need to fetch user from database to check role
        # Implementation depends on how you want to handle database access in dependencies
        # For now, returning user_id
        return current_user_id
    
    return role_checker


class PermissionChecker:
    """Permission checking utilities"""
    
    @staticmethod
    def can_access_resource(user: User, resource_user_id: str) -> bool:
        """Check if user can access resource owned by another user"""
        # Admin can access everything
        if user.role == UserRole.ADMIN:
            return True
        
        # Users can access their own resources
        if str(user.id) == resource_user_id:
            return True
        
        return False
    
    @staticmethod
    def can_modify_resource(user: User, resource_user_id: str) -> bool:
        """Check if user can modify resource"""
        # Admin can modify everything
        if user.role == UserRole.ADMIN:
            return True
        
        # Users can modify their own resources
        if str(user.id) == resource_user_id:
            return True
        
        return False
    
    @staticmethod
    def can_delete_resource(user: User, resource_user_id: str) -> bool:
        """Check if user can delete resource"""
        # Admin can delete everything
        if user.role == UserRole.ADMIN:
            return True
        
        # Users can delete their own resources
        if str(user.id) == resource_user_id:
            return True
        
        return False
    
    @staticmethod
    def has_admin_access(user: User) -> bool:
        """Check if user has admin access"""
        return user.role == UserRole.ADMIN
    
    @staticmethod
    def has_premium_features(user: User) -> bool:
        """Check if user has access to premium features"""
        return user.role in [UserRole.PRO, UserRole.ENTERPRISE, UserRole.ADMIN]


# Rate limiting utilities
class RateLimiter:
    """Rate limiting implementation using Redis"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
    
    async def is_allowed(
        self, 
        key: str, 
        limit: int, 
        window_seconds: int
    ) -> bool:
        """Check if request is within rate limit"""
        current_time = int(datetime.utcnow().timestamp())
        window_start = current_time - window_seconds
        
        # Use Redis pipeline for atomic operations
        pipe = self.redis.pipeline()
        
        # Remove expired entries
        pipe.zremrangebyscore(key, 0, window_start)
        
        # Count current requests in window
        pipe.zcard(key)
        
        # Add current request
        pipe.zadd(key, {str(current_time): current_time})
        
        # Set expiration
        pipe.expire(key, window_seconds)
        
        results = await pipe.execute()
        
        # Check if within limit
        current_count = results[1]
        return current_count < limit
    
    async def get_remaining_requests(
        self, 
        key: str, 
        limit: int, 
        window_seconds: int
    ) -> int:
        """Get remaining requests in current window"""
        current_time = int(datetime.utcnow().timestamp())
        window_start = current_time - window_seconds
        
        # Count current requests
        current_count = await self.redis.zcount(key, window_start, current_time)
        return max(0, limit - current_count)


# Webhook signature verification
def verify_webhook_signature(
    payload: bytes, 
    signature: str, 
    secret: str
) -> bool:
    """Verify webhook signature"""
    expected_signature = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    # Remove 'sha256=' prefix if present
    if signature.startswith('sha256='):
        signature = signature[7:]
    
    return hmac.compare_digest(signature, expected_signature)


# CORS and security headers
def get_security_headers() -> Dict[str, str]:
    """Get security headers for responses"""
    return {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
    }


# Input validation and sanitization
class InputValidator:
    """Input validation utilities"""
    
    @staticmethod
    def is_valid_email(email: str) -> bool:
        """Validate email format"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def is_strong_password(password: str) -> bool:
        """Check if password meets strength requirements"""
        if len(password) < settings.PASSWORD_MIN_LENGTH:
            return False
        
        # Check for at least one uppercase, lowercase, digit, and special char
        import re
        patterns = [
            r'[A-Z]',  # Uppercase
            r'[a-z]',  # Lowercase  
            r'\d',     # Digit
            r'[!@#$%^&*()_+\-=\[\]{}|;\':",./<>?]'  # Special char
        ]
        
        return all(re.search(pattern, password) for pattern in patterns)
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename for safe storage"""
        import re
        # Remove or replace dangerous characters
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        filename = filename.strip('. ')
        return filename[:255]  # Limit length


# Export commonly used functions
__all__ = [
    "security_manager",
    "AuthenticationError", 
    "AuthorizationError",
    "get_current_user_from_token",
    "require_authentication",
    "require_roles",
    "PermissionChecker",
    "RateLimiter",
    "verify_webhook_signature",
    "get_security_headers",
    "InputValidator",
]