# Text Dataset Platform - Backend API

A high-performance FastAPI backend for the AI-powered text-to-dataset platform with real-time processing, AWS cloud integration, and enterprise-grade architecture.

## 🚀 Features

- **FastAPI** - Modern, fast web framework with automatic API documentation
- **Real-time Processing** - WebSocket connections for live updates
- **AWS Cloud Integration** - S3, Cognito, CloudWatch, SQS, Lambda
- **Advanced NLP Pipeline** - Entity extraction, sentiment analysis, classification
- **PostgreSQL Database** - With SQLAlchemy ORM and Alembic migrations
- **Redis Cache** - For session management and caching
- **Celery Workers** - Distributed task processing
- **Comprehensive Testing** - Unit, integration, and load tests
- **Monitoring & Observability** - Structured logging, metrics, tracing
- **Security** - JWT authentication, rate limiting, input validation
- **Docker Support** - Multi-stage builds and container orchestration

## 📁 Project Structure

```
text-dataset-api/
├── app/
│   ├── api/                    # API routes and endpoints
│   │   ├── v1/                 # API version 1
│   │   │   ├── endpoints/      # Route handlers
│   │   │   └── dependencies/   # Route dependencies
│   │   └── websocket/          # WebSocket handlers
│   ├── core/                   # Core configuration and utilities
│   │   ├── config.py           # Application settings
│   │   ├── security.py         # Authentication and authorization
│   │   ├── database.py         # Database connection and session
│   │   └── logging.py          # Logging configuration
│   ├── models/                 # Database models (SQLAlchemy)
│   ├── schemas/                # Pydantic models for validation
│   ├── services/               # Business logic layer
│   │   ├── auth/               # Authentication services
│   │   ├── documents/          # Document processing services
│   │   ├── processing/         # NLP processing pipeline
│   │   ├── analytics/          # Analytics and reporting
│   │   ├── chat/               # AI chat services
│   │   └── aws/                # AWS integration services
│   ├── workers/                # Celery task workers
│   ├── utils/                  # Utility functions and helpers
│   ├── tests/                  # Test suite
│   └── main.py                 # Application entry point
├── migrations/                 # Database migrations (Alembic)
├── scripts/                    # Deployment and utility scripts
├── docker/                     # Docker configurations
├── docs/                       # API documentation
└── requirements/               # Python dependencies
```

## 🛠 Technology Stack

- **Framework**: FastAPI 0.104+
- **Database**: PostgreSQL 15+ with SQLAlchemy 2.0
- **Cache**: Redis 7+
- **Task Queue**: Celery with Redis broker
- **Authentication**: JWT with AWS Cognito integration
- **File Storage**: AWS S3
- **Monitoring**: AWS CloudWatch, Prometheus
- **Testing**: pytest, pytest-asyncio
- **Documentation**: Automatic OpenAPI/Swagger
- **Deployment**: Docker, AWS ECS, Lambda

## 🚦 Quick Start

### Development Setup

```bash
# Clone and setup
git clone <repository>
cd text-dataset-api

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements/dev.txt

# Setup environment variables
cp .env.example .env
# Edit .env with your configuration

# Setup database
alembic upgrade head

# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Docker Setup

```bash
# Build and run with Docker Compose
docker-compose up -d --build

# Run tests
docker-compose exec api pytest

# View logs
docker-compose logs -f api
```

## 📊 API Endpoints

### Authentication
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/register` - User registration  
- `POST /api/v1/auth/refresh` - Refresh JWT token
- `POST /api/v1/auth/logout` - User logout

### Documents
- `POST /api/v1/documents/upload` - Upload documents
- `GET /api/v1/documents/` - List documents
- `GET /api/v1/documents/{id}` - Get document details
- `DELETE /api/v1/documents/{id}` - Delete document

### Processing
- `POST /api/v1/processing/jobs` - Create processing job
- `GET /api/v1/processing/jobs` - List processing jobs
- `GET /api/v1/processing/jobs/{id}` - Get job status
- `POST /api/v1/processing/jobs/{id}/cancel` - Cancel job

### Analytics
- `GET /api/v1/analytics/dashboard` - Dashboard metrics
- `GET /api/v1/analytics/processing-volume` - Processing volume data
- `GET /api/v1/analytics/export` - Export analytics data

### Chat
- `POST /api/v1/chat/sessions` - Create chat session
- `GET /api/v1/chat/sessions` - List chat sessions
- `POST /api/v1/chat/sessions/{id}/messages` - Send message
- `GET /api/v1/chat/sessions/{id}/messages` - Get messages

### Real-time
- `WS /ws` - WebSocket connection for real-time updates

## 🔧 Configuration

Key environment variables:

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost/dbname

# Redis
REDIS_URL=redis://localhost:6379

# AWS
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
AWS_S3_BUCKET=your-bucket-name

# Security
SECRET_KEY=your-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Processing
CELERY_BROKER_URL=redis://localhost:6379
CELERY_RESULT_BACKEND=redis://localhost:6379
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest app/tests/test_auth.py

# Run integration tests
pytest app/tests/integration/
```

## 📈 Performance

- **Async/Await**: Full async support for I/O operations
- **Connection Pooling**: Optimized database connections
- **Caching Strategy**: Redis for frequently accessed data
- **Background Tasks**: Celery for heavy processing
- **Rate Limiting**: API rate limiting with Redis
- **Monitoring**: Real-time metrics and alerting

## 🔒 Security

- **JWT Authentication**: Secure token-based auth
- **Input Validation**: Pydantic schema validation
- **SQL Injection Protection**: SQLAlchemy ORM
- **CORS Configuration**: Controlled cross-origin requests
- **Rate Limiting**: Protection against abuse
- **Secrets Management**: Environment-based configuration

## 📚 Documentation

- **API Docs**: Available at `/docs` (Swagger UI)
- **ReDoc**: Available at `/redoc`
- **OpenAPI Spec**: Available at `/openapi.json`

## 🚀 Deployment

### AWS ECS Deployment

```bash
# Build and push Docker image
docker build -t text-dataset-api .
docker tag text-dataset-api:latest your-ecr-repo/text-dataset-api:latest
docker push your-ecr-repo/text-dataset-api:latest

# Deploy with ECS
aws ecs update-service --cluster your-cluster --service text-dataset-api --force-new-deployment
```

### Lambda Deployment (for specific functions)

```bash
# Package and deploy processing functions
cd workers/
zip -r processing_function.zip .
aws lambda update-function-code --function-name text-processing --zip-file fileb://processing_function.zip
```

## 📞 Support

- **Documentation**: Check `/docs` endpoint
- **Issues**: GitHub Issues
- **Email**: support@textdataset.com
- **Slack**: #text-dataset-api

## 📄 License

MIT License - see LICENSE file for details.