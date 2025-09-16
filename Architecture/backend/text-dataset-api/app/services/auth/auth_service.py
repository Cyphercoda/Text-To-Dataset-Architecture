"""
Authentication service for user registration, login, and token management
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from fastapi import HTTPException, status

from app.core.security import security_manager, AuthenticationError, InputValidator
from app.models.user import User, UserStatus, UserRole, UserSession, ApiKey
from app.core.config import settings
from app.services.email.email_service import EmailService
from app.services.analytics.event_service import EventService

logger = logging.getLogger(__name__)


class AuthService:
    """Authentication service for managing user authentication and sessions"""
    
    def __init__(self):
        self.security = security_manager
        self.email_service = EmailService()
        self.event_service = EventService()
    
    async def register_user(
        self,
        db: AsyncSession,
        email: str,
        password: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        company: Optional[str] = None
    ) -> Tuple[User, str, str]:
        """
        Register a new user
        
        Returns:
            Tuple of (user, access_token, refresh_token)
        """
        # Validate email format
        if not InputValidator.is_valid_email(email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email format"
            )
        
        # Validate password strength
        if not InputValidator.is_strong_password(password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password does not meet strength requirements"
            )
        
        # Check if user already exists
        existing_user = await db.execute(
            select(User).where(User.email == email.lower())
        )
        if existing_user.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered"
            )
        
        # Create new user
        hashed_password = self.security.hash_password(password)
        verification_token = self.security.generate_verification_token()
        
        user = User(
            email=email.lower(),
            hashed_password=hashed_password,
            first_name=first_name,
            last_name=last_name,
            company=company,
            full_name=f"{first_name or ''} {last_name or ''}".strip() or None,
            role=UserRole.FREE,
            status=UserStatus.PENDING,
            email_verification_token=verification_token,
            email_verification_sent_at=datetime.utcnow(),
            created_at=datetime.utcnow()
        )
        
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        # Send verification email
        await self.email_service.send_verification_email(
            email=user.email,
            name=user.display_name,
            token=verification_token
        )
        
        # Create tokens
        access_token = self.security.create_access_token(
            data={"sub": str(user.id), "email": user.email, "role": user.role}
        )
        refresh_token = self.security.create_refresh_token(
            data={"sub": str(user.id)}
        )
        
        # Create session
        await self.create_session(db, user.id, refresh_token)
        
        # Track registration event
        await self.event_service.track_event(
            db=db,
            user_id=user.id,
            event_type="user_registration",
            event_name="User Registered",
            properties={"method": "email", "role": user.role}
        )
        
        logger.info(f"User registered successfully: {user.email}")
        return user, access_token, refresh_token
    
    async def login_user(
        self,
        db: AsyncSession,
        email: str,
        password: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Tuple[User, str, str]:
        """
        Authenticate user and create session
        
        Returns:
            Tuple of (user, access_token, refresh_token)
        """
        # Find user by email
        result = await db.execute(
            select(User).where(User.email == email.lower())
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise AuthenticationError("Invalid credentials")
        
        # Verify password
        if not self.security.verify_password(password, user.hashed_password):
            raise AuthenticationError("Invalid credentials")
        
        # Check if user is active
        if user.status == UserStatus.BANNED:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account has been banned"
            )
        
        if user.status == UserStatus.SUSPENDED:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account has been suspended"
            )
        
        # Update user login information
        user.last_login_at = datetime.utcnow()
        user.login_count += 1
        user.update_last_activity()
        
        # Activate pending accounts on first login
        if user.status == UserStatus.PENDING:
            user.status = UserStatus.ACTIVE
        
        await db.commit()
        
        # Create tokens
        access_token = self.security.create_access_token(
            data={
                "sub": str(user.id),
                "email": user.email,
                "role": user.role,
                "status": user.status
            }
        )
        refresh_token = self.security.create_refresh_token(
            data={"sub": str(user.id)}
        )
        
        # Create session
        session = await self.create_session(
            db, user.id, refresh_token, ip_address, user_agent
        )
        
        # Track login event
        await self.event_service.track_event(
            db=db,
            user_id=user.id,
            event_type="user_login",
            event_name="User Login",
            properties={
                "method": "email",
                "ip_address": ip_address,
                "session_id": str(session.id)
            }
        )
        
        logger.info(f"User logged in successfully: {user.email}")
        return user, access_token, refresh_token
    
    async def logout_user(
        self,
        db: AsyncSession,
        user_id: UUID,
        session_token: Optional[str] = None
    ) -> bool:
        """Logout user and invalidate session"""
        # Find and deactivate session
        if session_token:
            result = await db.execute(
                select(UserSession).where(
                    and_(
                        UserSession.user_id == user_id,
                        UserSession.session_token == session_token,
                        UserSession.is_active == True
                    )
                )
            )
            session = result.scalar_one_or_none()
            
            if session:
                session.deactivate()
                await db.commit()
        else:
            # Deactivate all sessions for user
            result = await db.execute(
                select(UserSession).where(
                    and_(
                        UserSession.user_id == user_id,
                        UserSession.is_active == True
                    )
                )
            )
            sessions = result.scalars().all()
            
            for session in sessions:
                session.deactivate()
            
            await db.commit()
        
        # Track logout event
        await self.event_service.track_event(
            db=db,
            user_id=user_id,
            event_type="user_logout",
            event_name="User Logout"
        )
        
        logger.info(f"User logged out: {user_id}")
        return True
    
    async def refresh_access_token(
        self,
        db: AsyncSession,
        refresh_token: str
    ) -> Tuple[str, str]:
        """
        Refresh access token using refresh token
        
        Returns:
            Tuple of (new_access_token, new_refresh_token)
        """
        # Decode and validate refresh token
        try:
            payload = self.security.decode_token(refresh_token)
        except Exception:
            raise AuthenticationError("Invalid refresh token")
        
        if not self.security.verify_token_type(payload, "refresh"):
            raise AuthenticationError("Invalid token type")
        
        user_id = payload.get("sub")
        if not user_id:
            raise AuthenticationError("Invalid token payload")
        
        # Get user
        result = await db.execute(
            select(User).where(User.id == UUID(user_id))
        )
        user = result.scalar_one_or_none()
        
        if not user or not user.is_active:
            raise AuthenticationError("User not found or inactive")
        
        # Create new tokens
        new_access_token = self.security.create_access_token(
            data={
                "sub": str(user.id),
                "email": user.email,
                "role": user.role,
                "status": user.status
            }
        )
        new_refresh_token = self.security.create_refresh_token(
            data={"sub": str(user.id)}
        )
        
        # Update session with new refresh token
        result = await db.execute(
            select(UserSession).where(
                and_(
                    UserSession.user_id == user.id,
                    UserSession.refresh_token == refresh_token,
                    UserSession.is_active == True
                )
            )
        )
        session = result.scalar_one_or_none()
        
        if session:
            session.refresh_token = new_refresh_token
            session.update_activity()
            await db.commit()
        
        logger.info(f"Access token refreshed for user: {user.id}")
        return new_access_token, new_refresh_token
    
    async def verify_email(
        self,
        db: AsyncSession,
        token: str
    ) -> User:
        """Verify user email with verification token"""
        # Find user by verification token
        result = await db.execute(
            select(User).where(User.email_verification_token == token)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification token"
            )
        
        # Check if already verified
        if user.is_email_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already verified"
            )
        
        # Verify email
        user.is_email_verified = True
        user.email_verification_token = None
        user.status = UserStatus.ACTIVE
        
        await db.commit()
        await db.refresh(user)
        
        # Send welcome email
        await self.email_service.send_welcome_email(
            email=user.email,
            name=user.display_name
        )
        
        # Track verification event
        await self.event_service.track_event(
            db=db,
            user_id=user.id,
            event_type="email_verified",
            event_name="Email Verified"
        )
        
        logger.info(f"Email verified for user: {user.email}")
        return user
    
    async def request_password_reset(
        self,
        db: AsyncSession,
        email: str
    ) -> bool:
        """Request password reset for user"""
        # Find user by email
        result = await db.execute(
            select(User).where(User.email == email.lower())
        )
        user = result.scalar_one_or_none()
        
        if not user:
            # Don't reveal if email exists
            logger.warning(f"Password reset requested for non-existent email: {email}")
            return True
        
        # Generate reset token
        reset_token = self.security.generate_reset_token()
        
        # Update user with reset token
        user.password_reset_token = reset_token
        user.password_reset_sent_at = datetime.utcnow()
        user.password_reset_expires_at = datetime.utcnow() + timedelta(hours=1)
        
        await db.commit()
        
        # Send reset email
        await self.email_service.send_password_reset_email(
            email=user.email,
            name=user.display_name,
            token=reset_token
        )
        
        # Track reset request event
        await self.event_service.track_event(
            db=db,
            user_id=user.id,
            event_type="password_reset_requested",
            event_name="Password Reset Requested"
        )
        
        logger.info(f"Password reset requested for user: {user.email}")
        return True
    
    async def reset_password(
        self,
        db: AsyncSession,
        token: str,
        new_password: str
    ) -> User:
        """Reset user password with reset token"""
        # Validate password strength
        if not InputValidator.is_strong_password(new_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password does not meet strength requirements"
            )
        
        # Find user by reset token
        result = await db.execute(
            select(User).where(User.password_reset_token == token)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid reset token"
            )
        
        # Check if token expired
        if user.password_reset_expires_at < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reset token has expired"
            )
        
        # Update password
        user.hashed_password = self.security.hash_password(new_password)
        user.password_reset_token = None
        user.password_reset_sent_at = None
        user.password_reset_expires_at = None
        
        await db.commit()
        await db.refresh(user)
        
        # Invalidate all existing sessions
        await self.logout_user(db, user.id)
        
        # Send confirmation email
        await self.email_service.send_password_changed_email(
            email=user.email,
            name=user.display_name
        )
        
        # Track password reset event
        await self.event_service.track_event(
            db=db,
            user_id=user.id,
            event_type="password_reset_completed",
            event_name="Password Reset Completed"
        )
        
        logger.info(f"Password reset completed for user: {user.email}")
        return user
    
    async def change_password(
        self,
        db: AsyncSession,
        user_id: UUID,
        current_password: str,
        new_password: str
    ) -> User:
        """Change user password"""
        # Get user
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Verify current password
        if not self.security.verify_password(current_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Validate new password strength
        if not InputValidator.is_strong_password(new_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password does not meet strength requirements"
            )
        
        # Update password
        user.hashed_password = self.security.hash_password(new_password)
        
        await db.commit()
        await db.refresh(user)
        
        # Send notification email
        await self.email_service.send_password_changed_email(
            email=user.email,
            name=user.display_name
        )
        
        # Track password change event
        await self.event_service.track_event(
            db=db,
            user_id=user.id,
            event_type="password_changed",
            event_name="Password Changed"
        )
        
        logger.info(f"Password changed for user: {user.email}")
        return user
    
    async def create_session(
        self,
        db: AsyncSession,
        user_id: UUID,
        refresh_token: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> UserSession:
        """Create user session"""
        session_token = self.security.create_session_token()
        
        session = UserSession(
            user_id=user_id,
            session_token=session_token,
            refresh_token=refresh_token,
            ip_address=ip_address,
            user_agent=user_agent,
            is_active=True,
            expires_at=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
            last_activity_at=datetime.utcnow()
        )
        
        db.add(session)
        await db.commit()
        await db.refresh(session)
        
        return session
    
    async def get_user_by_id(
        self,
        db: AsyncSession,
        user_id: UUID
    ) -> Optional[User]:
        """Get user by ID"""
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_user_by_email(
        self,
        db: AsyncSession,
        email: str
    ) -> Optional[User]:
        """Get user by email"""
        result = await db.execute(
            select(User).where(User.email == email.lower())
        )
        return result.scalar_one_or_none()
    
    async def create_api_key(
        self,
        db: AsyncSession,
        user_id: UUID,
        name: str,
        permissions: Optional[list] = None
    ) -> Tuple[ApiKey, str]:
        """
        Create API key for user
        
        Returns:
            Tuple of (api_key_model, raw_api_key)
        """
        # Generate API key
        raw_key = self.security.generate_api_key()
        key_hash = self.security.hash_api_key(raw_key)
        key_prefix = raw_key[:8]
        
        # Create API key record
        api_key = ApiKey(
            user_id=user_id,
            name=name,
            key_hash=key_hash,
            key_prefix=key_prefix,
            permissions=permissions or [],
            is_active=True
        )
        
        db.add(api_key)
        await db.commit()
        await db.refresh(api_key)
        
        # Track API key creation
        await self.event_service.track_event(
            db=db,
            user_id=user_id,
            event_type="api_key_created",
            event_name="API Key Created",
            properties={"key_id": str(api_key.id), "name": name}
        )
        
        logger.info(f"API key created for user: {user_id}")
        return api_key, raw_key
    
    async def validate_api_key(
        self,
        db: AsyncSession,
        api_key: str
    ) -> Optional[ApiKey]:
        """Validate API key and return associated key record"""
        key_hash = self.security.hash_api_key(api_key)
        
        result = await db.execute(
            select(ApiKey).where(
                and_(
                    ApiKey.key_hash == key_hash,
                    ApiKey.is_active == True
                )
            )
        )
        api_key_record = result.scalar_one_or_none()
        
        if api_key_record and api_key_record.is_valid:
            # Update usage
            api_key_record.increment_usage()
            await db.commit()
            return api_key_record
        
        return None


# Create singleton instance
auth_service = AuthService()