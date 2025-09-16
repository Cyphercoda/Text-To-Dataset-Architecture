"""
Pytest configuration and fixtures for testing
"""

import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import get_db, Base
from app.core.config import settings
from app.core.security import security_manager
from app.services.storage.s3_service import s3_service
from app.services.aws.cloudwatch_service import cloudwatch_service
from app.api.websocket.manager import websocket_manager
from app.models.user import User
from app.models.document import Document


# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def async_engine():
    """Create test database engine"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest_asyncio.fixture
async def async_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session"""
    async_session_maker = async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with async_session_maker() as session:
        yield session


@pytest.fixture
def override_get_db(async_session: AsyncSession):
    """Override the get_db dependency"""
    async def _override_get_db():
        yield async_session
    
    return _override_get_db


@pytest.fixture
def client(override_get_db):
    """Create test client with overridden dependencies"""
    app.dependency_overrides[get_db] = override_get_db
    
    # Mock external services
    with pytest.mock.patch.object(s3_service, 'upload_file'), \
         pytest.mock.patch.object(cloudwatch_service, 'put_metric'), \
         pytest.mock.patch.object(websocket_manager, 'send_to_user'):
        
        yield TestClient(app)
    
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(async_session: AsyncSession) -> User:
    """Create a test user"""
    user_data = {
        "email": "test@example.com",
        "hashed_password": security_manager.get_password_hash("testpassword123"),
        "first_name": "Test",
        "last_name": "User",
        "is_active": True,
        "is_email_verified": True,
        "role": "basic",
        "subscription_tier": "basic"
    }
    
    user = User(**user_data)
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)
    
    return user


@pytest_asyncio.fixture
async def test_admin_user(async_session: AsyncSession) -> User:
    """Create a test admin user"""
    user_data = {
        "email": "admin@example.com",
        "hashed_password": security_manager.get_password_hash("adminpassword123"),
        "first_name": "Admin",
        "last_name": "User",
        "is_active": True,
        "is_email_verified": True,
        "role": "admin",
        "subscription_tier": "enterprise"
    }
    
    user = User(**user_data)
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)
    
    return user


@pytest.fixture
def auth_headers(test_user: User) -> dict:
    """Create authentication headers for test user"""
    access_token = security_manager.create_access_token(
        data={"sub": str(test_user.id)}
    )
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def admin_auth_headers(test_admin_user: User) -> dict:
    """Create authentication headers for admin user"""
    access_token = security_manager.create_access_token(
        data={"sub": str(test_admin_user.id)}
    )
    return {"Authorization": f"Bearer {access_token}"}


@pytest_asyncio.fixture
async def test_document(async_session: AsyncSession, test_user: User) -> Document:
    """Create a test document"""
    document_data = {
        "user_id": test_user.id,
        "filename": "test_document.pdf",
        "title": "Test Document",
        "description": "A test document for testing",
        "file_size": 1024,
        "content_type": "application/pdf",
        "s3_bucket": "test-bucket",
        "s3_key": "documents/test_document.pdf",
        "document_type": "PDF",
        "status": "uploaded",
        "is_processed": False
    }
    
    document = Document(**document_data)
    async_session.add(document)
    await async_session.commit()
    await async_session.refresh(document)
    
    return document


@pytest.fixture
def mock_s3_service():
    """Mock S3 service for testing"""
    mock = MagicMock()
    mock.upload_file.return_value = {
        'success': True,
        'bucket': 'test-bucket',
        'key': 'documents/test.pdf',
        'file_size': 1024,
        'content_type': 'application/pdf',
        'content_hash': 'abc123',
        'file_url': 'https://test-bucket.s3.amazonaws.com/documents/test.pdf'
    }
    mock.download_file.return_value = b'test file content'
    mock.delete_file.return_value = True
    mock.generate_presigned_url.return_value = 'https://presigned-url.com'
    
    return mock


@pytest.fixture
def mock_cloudwatch_service():
    """Mock CloudWatch service for testing"""
    mock = MagicMock()
    mock.put_metric.return_value = True
    mock.record_api_request.return_value = None
    mock.record_document_processing.return_value = None
    
    return mock


@pytest.fixture
def mock_websocket_manager():
    """Mock WebSocket manager for testing"""
    mock = AsyncMock()
    mock.send_to_user.return_value = None
    mock.send_processing_update.return_value = None
    mock.broadcast_to_all.return_value = None
    
    return mock


@pytest.fixture
def sample_pdf_content() -> bytes:
    """Sample PDF content for testing"""
    # Minimal PDF content for testing
    return b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj
4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
100 700 Td
(Hello World) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000204 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
297
%%EOF"""


@pytest.fixture
def sample_text_content() -> str:
    """Sample text content for testing"""
    return """This is a sample text document for testing.
It contains multiple sentences and paragraphs.

This is a second paragraph with more content.
The document should be processed correctly by the system."""


@pytest.fixture
def mock_processing_options() -> dict:
    """Mock processing options for testing"""
    return {
        "extract_entities": True,
        "extract_keywords": True,
        "generate_summary": True,
        "classify_text": True,
        "calculate_readability": True,
        "num_keywords": 10,
        "summary_max_length": 200
    }


# Test data fixtures
@pytest.fixture
def user_registration_data() -> dict:
    """Sample user registration data"""
    return {
        "email": "newuser@example.com",
        "password": "SecurePassword123!",
        "confirm_password": "SecurePassword123!",
        "first_name": "New",
        "last_name": "User",
        "accept_terms": True
    }


@pytest.fixture
def user_login_data() -> dict:
    """Sample user login data"""
    return {
        "email": "test@example.com",
        "password": "testpassword123"
    }


@pytest.fixture
def document_upload_data() -> dict:
    """Sample document upload data"""
    return {
        "title": "Test Document",
        "description": "A test document",
        "tags": "test,document,sample",
        "auto_process": True
    }


@pytest.fixture
def dataset_generation_config() -> dict:
    """Sample dataset generation configuration"""
    return {
        "name": "Test Dataset",
        "description": "A test dataset",
        "format": "jsonl",
        "include_metadata": True,
        "shuffle": True,
        "max_records": 1000,
        "split_ratio": {"train": 0.8, "test": 0.2}
    }


# Utility fixtures
@pytest.fixture
def mock_celery_task():
    """Mock Celery task for testing"""
    mock = MagicMock()
    mock.apply_async.return_value = MagicMock(id='test-task-id')
    return mock


@pytest.fixture
def disable_rate_limiting():
    """Disable rate limiting for testing"""
    # This would disable rate limiting middleware if implemented
    pass


# Cleanup fixtures
@pytest.fixture(autouse=True)
async def cleanup_test_data(async_session: AsyncSession):
    """Cleanup test data after each test"""
    yield
    
    # Clean up any test data that might have been created
    try:
        await async_session.rollback()
    except Exception:
        pass