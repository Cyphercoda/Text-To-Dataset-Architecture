"""
Authentication API endpoints
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import require_authentication, security_manager
from app.core.config import settings
from app.services.auth.auth_service import auth_service
from app.schemas.auth import (
    UserRegisterRequest, UserLoginRequest, RefreshTokenRequest,
    EmailVerificationRequest, PasswordResetRequest, PasswordResetConfirmRequest,
    ChangePasswordRequest, CreateApiKeyRequest, UpdateProfileRequest,
    UpdatePreferencesRequest, OAuthLoginRequest,
    AuthResponse, TokenResponse, UserResponse, MessageResponse,
    CreateApiKeyResponse, ApiKeyResponse, SessionResponse
)
from app.models.user import User
from app.services.user.user_service import user_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: UserRegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user account
    
    - **email**: Valid email address (will be verified)
    - **password**: Must meet strength requirements (8+ chars, uppercase, lowercase, digit, special)
    - **accept_terms**: Must be true to register
    """
    if not request.accept_terms:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must accept the terms and conditions"
        )
    
    try:
        user, access_token, refresh_token = await auth_service.register_user(
            db=db,
            email=request.email,
            password=request.password,
            first_name=request.first_name,
            last_name=request.last_name,
            company=request.company
        )
        
        return AuthResponse(
            user=UserResponse.from_orm(user),
            tokens=TokenResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="Bearer",
                expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
            ),
            message="Registration successful. Please check your email to verify your account."
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed. Please try again."
        )


@router.post("/login", response_model=AuthResponse)
async def login(
    request: UserLoginRequest,
    http_request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Login with email and password
    
    Returns access and refresh tokens for authentication
    """
    try:
        # Get client IP and user agent
        ip_address = http_request.client.host if http_request.client else None
        user_agent = http_request.headers.get("User-Agent")
        
        user, access_token, refresh_token = await auth_service.login_user(
            db=db,
            email=request.email,
            password=request.password,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return AuthResponse(
            user=UserResponse.from_orm(user),
            tokens=TokenResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="Bearer",
                expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
            ),
            message="Login successful"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed. Please try again."
        )


@router.post("/logout", response_model=MessageResponse)
async def logout(
    current_user_id: str = Depends(require_authentication),
    db: AsyncSession = Depends(get_db)
):
    """
    Logout current user and invalidate session
    """
    try:
        await auth_service.logout_user(
            db=db,
            user_id=UUID(current_user_id)
        )
        
        return MessageResponse(
            message="Logged out successfully",
            success=True
        )
    
    except Exception as e:
        logger.error(f"Logout failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Refresh access token using refresh token
    """
    try:
        access_token, refresh_token = await auth_service.refresh_access_token(
            db=db,
            refresh_token=request.refresh_token
        )
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="Bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )


@router.post("/verify-email", response_model=MessageResponse)
async def verify_email(
    request: EmailVerificationRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Verify email address with verification token
    """
    try:
        await auth_service.verify_email(
            db=db,
            token=request.token
        )
        
        return MessageResponse(
            message="Email verified successfully. You can now login.",
            success=True
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Email verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Email verification failed"
        )


@router.post("/resend-verification", response_model=MessageResponse)
async def resend_verification(
    current_user_id: str = Depends(require_authentication),
    db: AsyncSession = Depends(get_db)
):
    """
    Resend email verification link
    """
    try:
        user = await auth_service.get_user_by_id(db, UUID(current_user_id))
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if user.is_email_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already verified"
            )
        
        # Resend verification email
        # Implementation would go here
        
        return MessageResponse(
            message="Verification email sent successfully",
            success=True
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Resend verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to resend verification email"
        )


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(
    request: PasswordResetRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Request password reset link
    """
    try:
        await auth_service.request_password_reset(
            db=db,
            email=request.email
        )
        
        return MessageResponse(
            message="If an account exists with this email, a password reset link has been sent.",
            success=True
        )
    
    except Exception as e:
        logger.error(f"Password reset request failed: {e}")
        # Don't reveal if email exists
        return MessageResponse(
            message="If an account exists with this email, a password reset link has been sent.",
            success=True
        )


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    request: PasswordResetConfirmRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Reset password with reset token
    """
    try:
        await auth_service.reset_password(
            db=db,
            token=request.token,
            new_password=request.new_password
        )
        
        return MessageResponse(
            message="Password reset successfully. You can now login with your new password.",
            success=True
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password reset failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset failed"
        )


@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    request: ChangePasswordRequest,
    current_user_id: str = Depends(require_authentication),
    db: AsyncSession = Depends(get_db)
):
    """
    Change current user's password
    """
    try:
        await auth_service.change_password(
            db=db,
            user_id=UUID(current_user_id),
            current_password=request.current_password,
            new_password=request.new_password
        )
        
        return MessageResponse(
            message="Password changed successfully",
            success=True
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password change failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change failed"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    current_user_id: str = Depends(require_authentication),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current user profile
    """
    try:
        user = await auth_service.get_user_by_id(db, UUID(current_user_id))
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserResponse.from_orm(user)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user profile"
        )


@router.put("/me", response_model=UserResponse)
async def update_profile(
    request: UpdateProfileRequest,
    current_user_id: str = Depends(require_authentication),
    db: AsyncSession = Depends(get_db)
):
    """
    Update current user's profile
    """
    try:
        user = await user_service.update_profile(
            db=db,
            user_id=UUID(current_user_id),
            **request.dict(exclude_unset=True)
        )
        
        return UserResponse.from_orm(user)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Profile update failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Profile update failed"
        )


@router.put("/me/preferences", response_model=UserResponse)
async def update_preferences(
    request: UpdatePreferencesRequest,
    current_user_id: str = Depends(require_authentication),
    db: AsyncSession = Depends(get_db)
):
    """
    Update user preferences
    """
    try:
        user = await user_service.update_preferences(
            db=db,
            user_id=UUID(current_user_id),
            **request.dict(exclude_unset=True)
        )
        
        return UserResponse.from_orm(user)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Preferences update failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Preferences update failed"
        )


@router.post("/api-keys", response_model=CreateApiKeyResponse)
async def create_api_key(
    request: CreateApiKeyRequest,
    current_user_id: str = Depends(require_authentication),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new API key
    """
    try:
        api_key, secret_key = await auth_service.create_api_key(
            db=db,
            user_id=UUID(current_user_id),
            name=request.name,
            permissions=request.permissions
        )
        
        return CreateApiKeyResponse(
            api_key=ApiKeyResponse.from_orm(api_key),
            secret_key=secret_key,
            message="API key created successfully. Please save the secret key as it won't be shown again."
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API key creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API key creation failed"
        )


@router.get("/api-keys", response_model=list[ApiKeyResponse])
async def list_api_keys(
    current_user_id: str = Depends(require_authentication),
    db: AsyncSession = Depends(get_db)
):
    """
    List user's API keys
    """
    try:
        api_keys = await user_service.get_api_keys(
            db=db,
            user_id=UUID(current_user_id)
        )
        
        return [ApiKeyResponse.from_orm(key) for key in api_keys]
    
    except Exception as e:
        logger.error(f"List API keys failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list API keys"
        )


@router.delete("/api-keys/{key_id}", response_model=MessageResponse)
async def delete_api_key(
    key_id: UUID,
    current_user_id: str = Depends(require_authentication),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete an API key
    """
    try:
        await user_service.delete_api_key(
            db=db,
            user_id=UUID(current_user_id),
            key_id=key_id
        )
        
        return MessageResponse(
            message="API key deleted successfully",
            success=True
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API key deletion failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API key deletion failed"
        )


@router.get("/sessions", response_model=list[SessionResponse])
async def list_sessions(
    current_user_id: str = Depends(require_authentication),
    db: AsyncSession = Depends(get_db)
):
    """
    List user's active sessions
    """
    try:
        sessions = await user_service.get_active_sessions(
            db=db,
            user_id=UUID(current_user_id)
        )
        
        return [SessionResponse.from_orm(session) for session in sessions]
    
    except Exception as e:
        logger.error(f"List sessions failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list sessions"
        )


@router.delete("/sessions/{session_id}", response_model=MessageResponse)
async def revoke_session(
    session_id: UUID,
    current_user_id: str = Depends(require_authentication),
    db: AsyncSession = Depends(get_db)
):
    """
    Revoke a specific session
    """
    try:
        await user_service.revoke_session(
            db=db,
            user_id=UUID(current_user_id),
            session_id=session_id
        )
        
        return MessageResponse(
            message="Session revoked successfully",
            success=True
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Session revocation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Session revocation failed"
        )


@router.post("/oauth/login", response_model=AuthResponse)
async def oauth_login(
    request: OAuthLoginRequest,
    http_request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Login with OAuth provider (Google, GitHub, Microsoft)
    """
    try:
        # Get client IP and user agent
        ip_address = http_request.client.host if http_request.client else None
        user_agent = http_request.headers.get("User-Agent")
        
        # OAuth login implementation would go here
        # This would verify the OAuth token with the provider
        # and create/update user account
        
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="OAuth login not yet implemented"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OAuth login failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OAuth login failed"
        )