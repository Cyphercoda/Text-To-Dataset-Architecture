#!/bin/bash

# Script to set up the GitHub repository with all the backend code
# Run this script from the /home/kali/Desktop/DC/Architecture/backend/text-dataset-api directory

echo "🚀 Setting up GitHub repository for Text Dataset API"

# Initialize git repository
git init

# Create .gitignore file
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
env/
ENV/
.venv/
.env/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/
coverage.xml

# Database
*.db
*.sqlite

# Logs
*.log
logs/

# Environment variables
.env
.env.local
.env.production

# AWS
.aws/

# Docker
.docker/

# OS
.DS_Store
Thumbs.db

# Temporary files
tmp/
temp/
*.tmp

# Celery
celerybeat-schedule
celerybeat.pid

# Redis
dump.rdb

# Jupyter
.ipynb_checkpoints/

# mypy
.mypy_cache/
.dmypy.json
dmypy.json
EOF

# Create README.md
cat > README.md << 'EOF'
# Text Dataset API

A comprehensive FastAPI-based backend application for processing documents and generating datasets using advanced NLP techniques.

## 🚀 Features

- **Document Processing**: Upload and process PDF, DOCX, and TXT files
- **NLP Pipeline**: Text extraction, entity recognition, summarization, and classification
- **Dataset Generation**: Create training datasets from processed documents
- **Real-time Updates**: WebSocket connections for live processing updates
- **User Management**: Authentication, authorization, and API key management
- **Analytics**: Comprehensive tracking and reporting
- **AWS Integration**: S3 storage, CloudWatch monitoring
- **Background Tasks**: Celery-based distributed processing
- **RESTful API**: Complete REST API with OpenAPI documentation

## 🛠️ Technology Stack

- **FastAPI** - Modern, fast web framework for building APIs
- **SQLAlchemy** - SQL toolkit and Object-Relational Mapping
- **PostgreSQL** - Advanced open source relational database
- **Redis** - In-memory data structure store for caching and message broker
- **Celery** - Distributed task queue for background processing
- **AWS Services** - S3, CloudWatch, and more cloud services
- **Docker** - Containerization platform
- **pytest** - Testing framework

## 📁 Project Structure

```
text-dataset-api/
├── app/
│   ├── api/                    # API routes and endpoints
│   ├── core/                   # Core configuration and utilities
│   ├── models/                 # Database models
│   ├── services/               # Business logic services
│   ├── workers/                # Celery tasks and workers
│   └── schemas/                # Pydantic models for validation
├── tests/                      # Test suite
├── alembic/                    # Database migrations
├── monitoring/                 # Monitoring configuration
├── nginx/                      # Nginx configuration
└── docker-compose.yml         # Docker services orchestration
```

## 🚀 Getting Started

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (if running locally)
- PostgreSQL 15+
- Redis 7+

### Quick Start with Docker

1. **Clone the repository:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/text-dataset-api.git
   cd text-dataset-api
   ```

2. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start all services:**
   ```bash
   docker-compose up -d
   ```

4. **Run database migrations:**
   ```bash
   docker-compose exec api alembic upgrade head
   ```

5. **Access the application:**
   - API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - Flower (Celery monitoring): http://localhost:5555
   - Grafana (Metrics): http://localhost:3000

### Local Development Setup

1. **Install Poetry:**
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

2. **Install dependencies:**
   ```bash
   poetry install
   ```

3. **Set up environment variables:**
   ```bash
   cp .env.example .env
   ```

4. **Start services:**
   ```bash
   # Start PostgreSQL and Redis
   docker-compose up -d db redis
   
   # Run migrations
   poetry run alembic upgrade head
   
   # Start the API
   poetry run uvicorn app.main:app --reload
   
   # Start Celery worker (in another terminal)
   poetry run celery -A app.workers.celery_app worker --loglevel=info
   ```

## 📖 API Documentation

Once the application is running, you can access:

- **Interactive API docs (Swagger UI)**: http://localhost:8000/docs
- **ReDoc documentation**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=app --cov-report=html

# Run specific test categories
poetry run pytest -m "auth"
poetry run pytest -m "documents"
```

## 🚀 Deployment

### AWS ECS Deployment

The application is configured for deployment on AWS ECS with:

- **ECS Fargate** for serverless container hosting
- **Application Load Balancer** for traffic distribution
- **RDS PostgreSQL** for database
- **ElastiCache Redis** for caching and message broker
- **S3** for file storage
- **CloudWatch** for monitoring and logging

### Environment Variables

Key environment variables for production:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname

# Redis
REDIS_URL=redis://host:6379
CELERY_BROKER_URL=redis://host:6379/0
CELERY_RESULT_BACKEND=redis://host:6379/0

# AWS
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-west-2
S3_BUCKET_NAME=your-bucket-name

# Security
JWT_SECRET_KEY=your-super-secret-jwt-key
JWT_REFRESH_SECRET_KEY=your-super-secret-refresh-key

# Application
ENVIRONMENT=production
APP_NAME=TextDatasetAPI
CORS_ORIGINS=https://yourdomain.com
```

## 🔧 Development

### Adding New Endpoints

1. Create the endpoint in `app/api/v1/endpoints/`
2. Add Pydantic models in `app/schemas/`
3. Implement business logic in `app/services/`
4. Add tests in `tests/`

### Database Migrations

```bash
# Create new migration
poetry run alembic revision --autogenerate -m "Description"

# Apply migrations
poetry run alembic upgrade head
```

### Adding Background Tasks

1. Create task in `app/workers/tasks/`
2. Register in `app/workers/celery_app.py`
3. Call from endpoints using `.apply_async()`

## 📊 Monitoring

The application includes comprehensive monitoring:

- **Health checks** at `/health` and `/api/v1/health`
- **Metrics** exported to CloudWatch
- **Logging** structured JSON logs
- **Grafana dashboards** for visualization
- **Flower** for Celery task monitoring

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

If you encounter any issues or have questions:

1. Check the [documentation](http://localhost:8000/docs)
2. Search existing [issues](https://github.com/YOUR_USERNAME/text-dataset-api/issues)
3. Create a new issue with detailed information

---

Built with ❤️ using FastAPI and modern Python technologies.
EOF

# Create .env.example
cat > .env.example << 'EOF'
# Environment
ENVIRONMENT=development

# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/text_dataset_db

# Redis
REDIS_URL=redis://localhost:6379
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# JWT
JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production
JWT_REFRESH_SECRET_KEY=your-super-secret-refresh-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# AWS
AWS_ACCESS_KEY_ID=your_aws_access_key_id
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
AWS_REGION=us-west-2
S3_BUCKET_NAME=your-s3-bucket-name

# Application
APP_NAME=TextDatasetAPI
API_V1_STR=/api/v1
CORS_ORIGINS=http://localhost:3000,http://localhost:8080

# Celery
CELERY_TASK_SOFT_TIME_LIMIT=300
CELERY_TASK_TIME_LIMIT=600

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_BURST=100
EOF

echo "📁 Adding all files to git..."
git add .

echo "📝 Creating initial commit..."
git commit -m "🎉 Initial commit: Complete Text Dataset API backend

✨ Features:
- FastAPI application with async support
- User authentication and authorization
- Document upload and processing pipeline
- NLP text analysis (entities, keywords, summarization)
- Real-time WebSocket updates
- Celery background task processing
- AWS S3 integration for file storage
- CloudWatch monitoring and logging
- Comprehensive test suite with pytest
- Docker containerization
- CI/CD pipeline with GitHub Actions
- Database migrations with Alembic
- Analytics and reporting system

🛠️ Tech Stack:
- FastAPI + SQLAlchemy + PostgreSQL
- Redis + Celery for background tasks
- AWS S3 + CloudWatch
- Docker + Docker Compose
- pytest for testing
- GitHub Actions for CI/CD"

echo "🔗 Repository initialized! Now connect to your GitHub repository:"
echo ""
echo "1. Create a new repository on GitHub (don't initialize with README)"
echo "2. Run these commands (replace YOUR_USERNAME and REPO_NAME):"
echo ""
echo "   git remote add origin https://github.com/YOUR_USERNAME/REPO_NAME.git"
echo "   git branch -M main"
echo "   git push -u origin main"
echo ""
echo "✅ All done! Your repository is ready to be pushed to GitHub."
EOF