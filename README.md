# DC - Document Processing & Dataset Generation Platform

A comprehensive full-stack application for intelligent document processing, text analysis, and dataset generation using advanced NLP techniques and cloud infrastructure.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)
![React](https://img.shields.io/badge/React-18+-blue.svg)
![AWS](https://img.shields.io/badge/AWS-Cloud-orange.svg)

## 🌟 Features

### Document Processing
- **Multi-format Support**: PDF, DOCX, TXT file processing
- **Intelligent Text Extraction**: Advanced OCR and text parsing
- **NLP Pipeline**: Entity recognition, keyword extraction, summarization
- **Real-time Processing**: Live updates via WebSocket connections

### Dataset Generation
- **Custom Datasets**: Generate training datasets from processed documents
- **Multiple Formats**: JSON, JSONL, CSV export options
- **Quality Control**: Automated data validation and cleaning
- **Batch Processing**: Handle large document collections efficiently

### User Experience
- **Modern Web Interface**: React-based responsive frontend
- **Real-time Dashboard**: Live processing status and analytics
- **User Management**: Authentication, profiles, and API keys
- **Analytics & Reporting**: Comprehensive usage statistics

### Cloud Infrastructure
- **AWS Integration**: S3 storage, CloudWatch monitoring
- **Scalable Architecture**: Containerized microservices
- **Background Processing**: Celery-based task queue
- **High Availability**: Load balancing and auto-scaling

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React Frontend │────│   FastAPI API   │────│   PostgreSQL    │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                        │                        │
         │              ┌─────────────────┐              │
         │              │   Redis Cache   │              │
         │              │   & Message     │              │
         │              │     Broker      │              │
         │              └─────────────────┘              │
         │                        │                        │
         │              ┌─────────────────┐              │
         │              │ Celery Workers  │              │
         │              │  (Background    │              │
         │              │   Processing)   │              │
         │              └─────────────────┘              │
         │                                               │
         │              ┌─────────────────┐              │
         └──────────────│  WebSocket API  │──────────────┘
                        │ (Real-time      │
                        │  Updates)       │
                        └─────────────────┘
                                 │
                        ┌─────────────────┐
                        │   AWS Services  │
                        │  S3 + CloudWatch│
                        └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- **Docker & Docker Compose** (recommended)
- **Python 3.11+** (for local development)
- **Node.js 18+** (for frontend development)
- **Git** for version control

### Option 1: Docker Compose (Recommended)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Cyphercoda/DC.git
   cd DC
   ```

2. **Set up environment variables:**
   ```bash
   # Backend environment
   cp Architecture/backend/text-dataset-api/.env.example Architecture/backend/text-dataset-api/.env
   
   # Frontend environment  
   cp frontend/.env.example frontend/.env
   
   # Edit the .env files with your configuration
   nano Architecture/backend/text-dataset-api/.env
   nano frontend/.env
   ```

3. **Start all services:**
   ```bash
   docker-compose up -d
   ```

4. **Initialize the database:**
   ```bash
   docker-compose exec api alembic upgrade head
   ```

5. **Access the application:**
   - **Frontend**: http://localhost:3000
   - **API Documentation**: http://localhost:8000/docs
   - **API Health Check**: http://localhost:8000/health
   - **Celery Monitoring (Flower)**: http://localhost:5555
   - **Grafana Dashboard**: http://localhost:3001 (admin/admin)

### Option 2: Local Development Setup

#### Backend Setup

1. **Navigate to backend directory:**
   ```bash
   cd Architecture/backend/text-dataset-api
   ```

2. **Install Poetry (Python dependency manager):**
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

3. **Install Python dependencies:**
   ```bash
   poetry install
   ```

4. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your database and AWS credentials
   ```

5. **Start required services:**
   ```bash
   # Start PostgreSQL and Redis
   docker-compose up -d db redis
   ```

6. **Run database migrations:**
   ```bash
   poetry run alembic upgrade head
   ```

7. **Start the FastAPI server:**
   ```bash
   poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

8. **Start Celery worker (in another terminal):**
   ```bash
   cd Architecture/backend/text-dataset-api
   poetry run celery -A app.workers.celery_app worker --loglevel=info
   ```

9. **Start Celery beat scheduler (in another terminal):**
   ```bash
   cd Architecture/backend/text-dataset-api
   poetry run celery -A app.workers.celery_app beat --loglevel=info
   ```

#### Frontend Setup

1. **Navigate to frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install Node.js dependencies:**
   ```bash
   npm install
   ```

3. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your API endpoints
   ```

4. **Start the development server:**
   ```bash
   npm run dev
   ```

## 📖 Usage Guide

### 1. User Registration & Authentication

1. **Register a new account:**
   ```bash
   curl -X POST "http://localhost:8000/api/v1/auth/register" \
   -H "Content-Type: application/json" \
   -d '{
     "email": "user@example.com",
     "password": "SecurePassword123!",
     "confirm_password": "SecurePassword123!",
     "first_name": "John",
     "last_name": "Doe",
     "accept_terms": true
   }'
   ```

2. **Login to get access token:**
   ```bash
   curl -X POST "http://localhost:8000/api/v1/auth/login" \
   -H "Content-Type: application/json" \
   -d '{
     "email": "user@example.com",
     "password": "SecurePassword123!"
   }'
   ```

### 2. Document Upload & Processing

1. **Upload a document:**
   ```bash
   curl -X POST "http://localhost:8000/api/v1/documents/upload" \
   -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
   -F "file=@/path/to/your/document.pdf" \
   -F "title=My Document" \
   -F "description=Test document for processing" \
   -F "auto_process=true"
   ```

2. **Check processing status:**
   ```bash
   curl -X GET "http://localhost:8000/api/v1/documents/processing-jobs/JOB_ID" \
   -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
   ```

3. **List your documents:**
   ```bash
   curl -X GET "http://localhost:8000/api/v1/documents/" \
   -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
   ```

### 3. Dataset Generation

1. **Generate dataset from processed documents:**
   ```bash
   curl -X POST "http://localhost:8000/api/v1/documents/datasets/generate" \
   -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
   -H "Content-Type: application/json" \
   -d '{
     "document_ids": ["doc_id_1", "doc_id_2"],
     "config": {
       "name": "My Training Dataset",
       "description": "Dataset for ML training",
       "format": "jsonl",
       "include_metadata": true,
       "shuffle": true
     }
   }'
   ```

### 4. Real-time Updates via WebSocket

```javascript
// Connect to WebSocket for real-time updates
const ws = new WebSocket('ws://localhost:8000/ws?token=YOUR_ACCESS_TOKEN');

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Real-time update:', data);
    
    // Handle different message types
    switch(data.type) {
        case 'processing_update':
            console.log(`Processing progress: ${data.progress * 100}%`);
            break;
        case 'processing_completed':
            console.log('Document processing completed!');
            break;
    }
};

// Subscribe to job updates
ws.send(JSON.stringify({
    type: 'subscribe',
    subscription_type: 'job',
    target_id: 'YOUR_JOB_ID'
}));
```

## 🔧 Configuration

### Environment Variables

#### Backend (.env)
```env
# Environment
ENVIRONMENT=development

# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/text_dataset_db

# Redis
REDIS_URL=redis://localhost:6379
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# JWT Security
JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production
JWT_REFRESH_SECRET_KEY=your-super-secret-refresh-key
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# AWS Configuration
AWS_ACCESS_KEY_ID=your_aws_access_key_id
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
AWS_REGION=us-west-2
S3_BUCKET_NAME=your-s3-bucket-name

# Application Settings
APP_NAME=TextDatasetAPI
API_V1_STR=/api/v1
CORS_ORIGINS=http://localhost:3000,http://localhost:8080

# Celery Configuration
CELERY_TASK_SOFT_TIME_LIMIT=300
CELERY_TASK_TIME_LIMIT=600

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_BURST=100
```

#### Frontend (.env)
```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
NEXT_PUBLIC_APP_NAME=Document Processing Platform
NEXT_PUBLIC_AWS_REGION=us-west-2
NEXT_PUBLIC_COGNITO_USER_POOL_ID=your_user_pool_id
NEXT_PUBLIC_COGNITO_USER_POOL_CLIENT_ID=your_client_id
```

## 🧪 Testing

### Backend Tests

```bash
cd Architecture/backend/text-dataset-api

# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=app --cov-report=html --cov-report=term-missing

# Run specific test categories
poetry run pytest -m "auth"          # Authentication tests
poetry run pytest -m "documents"     # Document processing tests
poetry run pytest -m "api"          # API endpoint tests

# Run integration tests
poetry run pytest -m "integration"

# Run tests in parallel
poetry run pytest -n auto
```

### Frontend Tests

```bash
cd frontend

# Run unit tests
npm test

# Run with coverage
npm run test:coverage

# Run E2E tests
npm run test:e2e

# Run component tests
npm run test:components
```

## 🚀 Deployment

### AWS ECS Deployment

1. **Build and push Docker images:**
   ```bash
   # Build images
   docker build -t your-registry/dc-api:latest Architecture/backend/text-dataset-api/
   docker build -t your-registry/dc-frontend:latest frontend/
   
   # Push to ECR or Docker Hub
   docker push your-registry/dc-api:latest
   docker push your-registry/dc-frontend:latest
   ```

2. **Deploy infrastructure:**
   ```bash
   # Use AWS CDK or CloudFormation
   cd infrastructure/
   cdk deploy
   ```

3. **Update ECS services:**
   ```bash
   aws ecs update-service \
     --cluster dc-cluster \
     --service dc-api-service \
     --force-new-deployment
   ```

### Docker Compose Production

1. **Use production docker-compose:**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

2. **Set up SSL certificates:**
   ```bash
   # Use Let's Encrypt
   certbot --nginx -d yourdomain.com
   ```

## 📊 Monitoring & Analytics

### Health Checks

- **API Health**: `GET /health`
- **Detailed Health**: `GET /api/v1/health`
- **Database Health**: `GET /api/v1/health/db`
- **Redis Health**: `GET /api/v1/health/redis`

### Monitoring Dashboards

1. **Grafana Dashboard**: http://localhost:3001
   - Username: `admin`
   - Password: `admin`

2. **Celery Monitoring**: http://localhost:5555

3. **API Documentation**: http://localhost:8000/docs

### CloudWatch Integration

The application automatically sends metrics to AWS CloudWatch:
- API request metrics
- Processing job statistics
- Error rates and response times
- System resource utilization

## 🔧 Development

### Adding New Features

1. **Backend API Endpoint:**
   ```bash
   # Create new endpoint
   touch Architecture/backend/text-dataset-api/app/api/v1/endpoints/new_feature.py
   
   # Add to router
   echo 'router.include_router(new_feature.router)' >> Architecture/backend/text-dataset-api/app/api/v1/api.py
   ```

2. **Frontend Component:**
   ```bash
   # Create new component
   mkdir frontend/src/components/NewFeature
   touch frontend/src/components/NewFeature/index.tsx
   ```

3. **Database Migration:**
   ```bash
   cd Architecture/backend/text-dataset-api
   poetry run alembic revision --autogenerate -m "Add new feature"
   poetry run alembic upgrade head
   ```

### Code Quality

```bash
# Backend linting and formatting
poetry run black .
poetry run isort .
poetry run flake8 .
poetry run mypy app/

# Frontend linting
npm run lint
npm run format
```

## 🐛 Troubleshooting

### Common Issues

1. **Database Connection Error:**
   ```bash
   # Check if PostgreSQL is running
   docker-compose ps db
   
   # Check database logs
   docker-compose logs db
   ```

2. **Celery Tasks Not Processing:**
   ```bash
   # Check Celery worker status
   docker-compose logs worker
   
   # Check Redis connection
   redis-cli ping
   ```

3. **Frontend API Connection Error:**
   ```bash
   # Check if backend is running
   curl http://localhost:8000/health
   
   # Check CORS configuration
   grep CORS_ORIGINS Architecture/backend/text-dataset-api/.env
   ```

4. **File Upload Issues:**
   ```bash
   # Check S3 credentials
   aws s3 ls s3://your-bucket-name
   
   # Check file permissions
   ls -la uploads/
   ```

### Debug Mode

1. **Enable backend debug logging:**
   ```bash
   export LOG_LEVEL=DEBUG
   poetry run uvicorn app.main:app --reload --log-level debug
   ```

2. **Enable frontend debug mode:**
   ```bash
   export NODE_ENV=development
   npm run dev
   ```

## 🤝 Contributing

1. **Fork the repository**
2. **Create a feature branch:**
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Make your changes and add tests**
4. **Run the test suite:**
   ```bash
   # Backend tests
   cd Architecture/backend/text-dataset-api && poetry run pytest
   
   # Frontend tests
   cd frontend && npm test
   ```
5. **Commit your changes:**
   ```bash
   git commit -m 'Add some amazing feature'
   ```
6. **Push to the branch:**
   ```bash
   git push origin feature/amazing-feature
   ```
7. **Open a Pull Request**

### Development Guidelines

- Follow PEP 8 for Python code
- Use TypeScript for all new frontend code
- Write tests for new features
- Update documentation for API changes
- Use conventional commits for commit messages

## 📋 API Reference

### Authentication Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register new user |
| POST | `/api/v1/auth/login` | User login |
| POST | `/api/v1/auth/logout` | User logout |
| POST | `/api/v1/auth/refresh` | Refresh access token |
| GET | `/api/v1/auth/me` | Get current user |

### Document Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/documents/upload` | Upload document |
| GET | `/api/v1/documents/` | List documents |
| GET | `/api/v1/documents/{id}` | Get document details |
| DELETE | `/api/v1/documents/{id}` | Delete document |
| POST | `/api/v1/documents/{id}/process` | Process document |

### Dataset Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/documents/datasets/generate` | Generate dataset |
| GET | `/api/v1/documents/datasets/` | List datasets |
| GET | `/api/v1/documents/datasets/{id}` | Get dataset details |

For complete API documentation, visit: http://localhost:8000/docs

## 🛡️ Security

### Authentication & Authorization

- JWT tokens with refresh mechanism
- API key authentication for programmatic access
- Role-based access control (RBAC)
- Rate limiting to prevent abuse

### Data Security

- All data encrypted in transit (HTTPS/TLS)
- Database encryption at rest
- Secure file upload validation
- Input sanitization and validation

### AWS Security

- IAM roles with least privilege access
- S3 bucket encryption
- VPC security groups
- CloudWatch monitoring for security events

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙋‍♂️ Support

### Documentation

- **API Documentation**: http://localhost:8000/docs
- **Architecture Guide**: [Architecture/README.md](Architecture/README.md)
- **Frontend Guide**: [frontend/README.md](frontend/README.md)

### Getting Help

- **Issues**: [GitHub Issues](https://github.com/Cyphercoda/DC/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Cyphercoda/DC/discussions)
- **Email**: support@example.com

### Reporting Security Issues

Please report security vulnerabilities to: security@example.com

---

## 🎯 Roadmap

- [ ] **Multi-language Support** - Add support for non-English documents
- [ ] **Advanced Analytics** - Machine learning insights and recommendations  
- [ ] **Collaboration Features** - Team workspaces and document sharing
- [ ] **API Rate Plans** - Tiered pricing with usage limits
- [ ] **Mobile App** - React Native mobile application
- [ ] **Plugin System** - Custom processing plugins and integrations

---

**Built with ❤️ by the DC Team**

*Empowering intelligent document processing and dataset generation for the modern world.*