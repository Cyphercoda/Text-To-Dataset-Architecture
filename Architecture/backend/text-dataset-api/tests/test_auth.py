"""
Test authentication endpoints
"""

import pytest
from fastapi import status
from fastapi.testclient import TestClient


class TestAuthEndpoints:
    """Test authentication endpoints"""
    
    def test_register_user_success(self, client: TestClient, user_registration_data: dict):
        """Test successful user registration"""
        response = client.post("/api/v1/auth/register", json=user_registration_data)
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        
        assert "user" in data
        assert "tokens" in data
        assert data["user"]["email"] == user_registration_data["email"]
        assert data["user"]["first_name"] == user_registration_data["first_name"]
        assert data["user"]["last_name"] == user_registration_data["last_name"]
        assert "access_token" in data["tokens"]
        assert "refresh_token" in data["tokens"]
    
    def test_register_user_password_mismatch(self, client: TestClient, user_registration_data: dict):
        """Test registration with password mismatch"""
        user_registration_data["confirm_password"] = "DifferentPassword123!"
        
        response = client.post("/api/v1/auth/register", json=user_registration_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_register_user_without_terms(self, client: TestClient, user_registration_data: dict):
        """Test registration without accepting terms"""
        user_registration_data["accept_terms"] = False
        
        response = client.post("/api/v1/auth/register", json=user_registration_data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "terms and conditions" in response.json()["detail"]
    
    def test_register_user_duplicate_email(self, client: TestClient, user_registration_data: dict):
        """Test registration with duplicate email"""
        # First registration
        response1 = client.post("/api/v1/auth/register", json=user_registration_data)
        assert response1.status_code == status.HTTP_201_CREATED
        
        # Second registration with same email
        response2 = client.post("/api/v1/auth/register", json=user_registration_data)
        assert response2.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_409_CONFLICT]
    
    def test_login_success(self, client: TestClient, user_login_data: dict):
        """Test successful login"""
        # First register a user
        registration_data = {
            "email": user_login_data["email"],
            "password": user_login_data["password"],
            "confirm_password": user_login_data["password"],
            "accept_terms": True
        }
        client.post("/api/v1/auth/register", json=registration_data)
        
        # Then login
        response = client.post("/api/v1/auth/login", json=user_login_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "user" in data
        assert "tokens" in data
        assert data["user"]["email"] == user_login_data["email"]
        assert "access_token" in data["tokens"]
        assert "refresh_token" in data["tokens"]
    
    def test_login_invalid_credentials(self, client: TestClient):
        """Test login with invalid credentials"""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "wrongpassword"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_login_wrong_password(self, client: TestClient, user_login_data: dict):
        """Test login with wrong password"""
        # First register a user
        registration_data = {
            "email": user_login_data["email"],
            "password": user_login_data["password"],
            "confirm_password": user_login_data["password"],
            "accept_terms": True
        }
        client.post("/api/v1/auth/register", json=registration_data)
        
        # Then try to login with wrong password
        wrong_login_data = {
            "email": user_login_data["email"],
            "password": "wrongpassword"
        }
        
        response = client.post("/api/v1/auth/login", json=wrong_login_data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_current_user(self, client: TestClient, auth_headers: dict):
        """Test getting current user profile"""
        response = client.get("/api/v1/auth/me", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "id" in data
        assert "email" in data
        assert "first_name" in data
        assert "last_name" in data
        assert "role" in data
    
    def test_get_current_user_unauthorized(self, client: TestClient):
        """Test getting current user without authentication"""
        response = client.get("/api/v1/auth/me")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_current_user_invalid_token(self, client: TestClient):
        """Test getting current user with invalid token"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/v1/auth/me", headers=headers)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_logout_success(self, client: TestClient, auth_headers: dict):
        """Test successful logout"""
        response = client.post("/api/v1/auth/logout", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["success"] is True
        assert "logged out" in data["message"].lower()
    
    def test_logout_unauthorized(self, client: TestClient):
        """Test logout without authentication"""
        response = client.post("/api/v1/auth/logout")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_refresh_token_success(self, client: TestClient, user_login_data: dict):
        """Test successful token refresh"""
        # First register and login
        registration_data = {
            "email": user_login_data["email"],
            "password": user_login_data["password"],
            "confirm_password": user_login_data["password"],
            "accept_terms": True
        }
        client.post("/api/v1/auth/register", json=registration_data)
        
        login_response = client.post("/api/v1/auth/login", json=user_login_data)
        refresh_token = login_response.json()["tokens"]["refresh_token"]
        
        # Then refresh token
        refresh_data = {"refresh_token": refresh_token}
        response = client.post("/api/v1/auth/refresh", json=refresh_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "access_token" in data
        assert "refresh_token" in data
        assert "token_type" in data
        assert "expires_in" in data
    
    def test_refresh_token_invalid(self, client: TestClient):
        """Test token refresh with invalid token"""
        refresh_data = {"refresh_token": "invalid_refresh_token"}
        response = client.post("/api/v1/auth/refresh", json=refresh_data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_change_password_success(self, client: TestClient, auth_headers: dict):
        """Test successful password change"""
        change_data = {
            "current_password": "testpassword123",
            "new_password": "NewSecurePassword123!",
            "confirm_password": "NewSecurePassword123!"
        }
        
        response = client.post("/api/v1/auth/change-password", json=change_data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["success"] is True
    
    def test_change_password_wrong_current(self, client: TestClient, auth_headers: dict):
        """Test password change with wrong current password"""
        change_data = {
            "current_password": "wrongcurrentpassword",
            "new_password": "NewSecurePassword123!",
            "confirm_password": "NewSecurePassword123!"
        }
        
        response = client.post("/api/v1/auth/change-password", json=change_data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_change_password_mismatch(self, client: TestClient, auth_headers: dict):
        """Test password change with password mismatch"""
        change_data = {
            "current_password": "testpassword123",
            "new_password": "NewSecurePassword123!",
            "confirm_password": "DifferentPassword123!"
        }
        
        response = client.post("/api/v1/auth/change-password", json=change_data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_forgot_password(self, client: TestClient):
        """Test forgot password request"""
        forgot_data = {"email": "test@example.com"}
        response = client.post("/api/v1/auth/forgot-password", json=forgot_data)
        
        # Should always return success to prevent email enumeration
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["success"] is True
    
    def test_update_profile_success(self, client: TestClient, auth_headers: dict):
        """Test successful profile update"""
        update_data = {
            "first_name": "Updated",
            "last_name": "Name",
            "company": "New Company"
        }
        
        response = client.put("/api/v1/auth/me", json=update_data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["first_name"] == update_data["first_name"]
        assert data["last_name"] == update_data["last_name"]
        assert data["company"] == update_data["company"]
    
    def test_update_preferences_success(self, client: TestClient, auth_headers: dict):
        """Test successful preferences update"""
        preferences_data = {
            "timezone": "America/New_York",
            "language": "en",
            "theme": "dark",
            "email_notifications": False
        }
        
        response = client.put("/api/v1/auth/me/preferences", json=preferences_data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["timezone"] == preferences_data["timezone"]
        assert data["language"] == preferences_data["language"]
        assert data["theme"] == preferences_data["theme"]
    
    def test_create_api_key_success(self, client: TestClient, auth_headers: dict):
        """Test successful API key creation"""
        api_key_data = {
            "name": "Test API Key",
            "description": "A test API key",
            "permissions": ["documents:read", "documents:write"]
        }
        
        response = client.post("/api/v1/auth/api-keys", json=api_key_data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        
        assert "api_key" in data
        assert "secret_key" in data
        assert data["api_key"]["name"] == api_key_data["name"]
        assert data["api_key"]["permissions"] == api_key_data["permissions"]
    
    def test_list_api_keys(self, client: TestClient, auth_headers: dict):
        """Test listing API keys"""
        # First create an API key
        api_key_data = {
            "name": "Test API Key",
            "permissions": ["documents:read"]
        }
        client.post("/api/v1/auth/api-keys", json=api_key_data, headers=auth_headers)
        
        # Then list API keys
        response = client.get("/api/v1/auth/api-keys", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["name"] == api_key_data["name"]
    
    def test_list_sessions(self, client: TestClient, auth_headers: dict):
        """Test listing active sessions"""
        response = client.get("/api/v1/auth/sessions", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert isinstance(data, list)
    
    def test_oauth_login_not_implemented(self, client: TestClient):
        """Test OAuth login (not implemented yet)"""
        oauth_data = {
            "provider": "google",
            "access_token": "fake_oauth_token"
        }
        
        response = client.post("/api/v1/auth/oauth/login", json=oauth_data)
        
        assert response.status_code == status.HTTP_501_NOT_IMPLEMENTED