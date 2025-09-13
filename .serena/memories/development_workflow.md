# Development Workflow for QuantyFinAI Agent

## Project Setup and Initialization

### First-Time Setup
```bash
# 1. Clone the repository
git clone <repository-url>
cd quantyFin-ai-agent

# 2. Install dependencies
poetry install --with=dev,lint,test

# 3. Set up environment
cp .env.example .env
# Edit .env with your configuration

# 4. Start development environment
docker-compose up -d

# 5. Verify setup
docker-compose exec db psql -U quantyfin -d quantyfin -c "SELECT 'Database is ready' as status;"
curl http://localhost:8000/api/v1/health
```

### Development Environment
- **Primary Tools**: Poetry for dependency management, Docker for containerization
- **IDE Integration**: Use VS Code with Python and Docker extensions
- **Hot Reload**: Use `docker-compose --profile dev up -d` for development with hot reload
- **Database**: PostgreSQL with pgvector extension running in Docker container

## Daily Development Workflow

### 1. Start Work Session
```bash
# Pull latest changes
git pull origin main

# Start development environment
docker-compose up -d

# Verify services are running
docker-compose ps
curl http://localhost:8000/api/v1/health
```

### 2. Feature Development Process
```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Make code changes
# Edit files as needed

# Run quality checks during development
poetry run black .
poetry run isort .
poetry run flake8 .
poetry run mypy app/

# Run tests
poetry run pytest
```

### 3. Testing Strategy
- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test service interactions and database operations
- **E2E Tests**: Test complete workflows through API endpoints
- **Test-Driven Development**: Write tests before implementing features when possible

### 4. Code Review Process
- **Self-Review**: Run all quality checks before submitting for review
- **Peer Review**: Submit pull requests for code review
- **Automated Checks**: CI/CD pipeline runs automated quality checks
- **Documentation**: Update documentation as needed

## Database Management

### Schema Changes
```bash
# Create new migration
# Edit migration file in scripts/migrations/

# Run migration
poetry run python scripts/migrations/migration_runner.py

# Verify migration
docker-compose exec db psql -U quantyfin -d quantyfin -c "\dt"
```

### Data Management
- **Seeds**: Use `scripts/init_db.py` for database initialization
- **Test Data**: Use factory-boy for test data generation
- **Backups**: Regular database backups in production

## Quality Assurance Process

### Pre-Commit Checks
```bash
# Install pre-commit hooks
poetry run pre-commit install

# Run pre-commit checks manually
poetry run pre-commit run --all-files
```

### Quality Gates
- **Code Coverage**: Maintain >80% test coverage
- **Type Safety**: No mypy errors allowed
- **Code Style**: Pass Black, isort, and flake8 checks
- **Security**: Pass security scanning checks

### CI/CD Pipeline
1. **Automated Testing**: Run all tests on pull requests
2. **Code Quality**: Run Black, isort, flake8, mypy
3. **Security Scanning**: Use Trivy for security scanning
4. **Docker Builds**: Automated Docker image builds
5. **Deployment**: Automated deployment to staging/production

## Debugging and Troubleshooting

### Common Issues
```bash
# Database connection issues
docker-compose logs db
docker-compose restart db

# Redis connection issues
docker-compose logs redis
docker-compose restart redis

# Application startup issues
docker-compose logs app
poetry run python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Authentication issues
curl http://localhost:8000/auth-test
curl http://localhost:8000/auth-health
```

### Debug Tools
- **Logging**: Use structured logging throughout the application
- **Debugger**: Use Python debugger (pdb) for local debugging
- **API Testing**: Use FastAPI's interactive documentation at `/docs`
- **Database Debugging**: Use `docker-compose exec db psql` for database debugging

## Deployment Workflow

### Staging Deployment
```bash
# Build and deploy to staging
docker-compose -f docker-compose.yml -f docker-compose.staging.yml build
docker-compose -f docker-compose.yml -f docker-compose.staging.yml up -d

# Verify staging deployment
curl https://staging.example.com/api/v1/health
```

### Production Deployment
```bash
# Build production images
docker-compose -f docker-compose.prod.yml build

# Deploy to production
docker-compose -f docker-compose.prod.yml up -d

# Post-deployment checks
curl https://api.example.com/api/v1/health
# Monitor logs and metrics
```

## Monitoring and Observability

### Health Checks
- **Application Health**: `/api/v1/health` endpoint
- **Database Health**: Docker health checks
- **Redis Health**: Connection verification
- **Authentication Health**: `/auth-health` endpoint

### Logging
```bash
# View application logs
docker-compose logs -f app

# View specific service logs
docker-compose logs -f db
docker-compose logs -f redis

# View logs with timestamp filtering
docker-compose logs --tail=100 -f app
```

### Performance Monitoring
- **Response Times**: Monitor API response times
- **Database Performance**: Monitor query performance
- **Cache Performance**: Monitor Redis hit/miss ratios
- **Resource Usage**: Monitor CPU, memory, and disk usage

## Collaboration Guidelines

### Branch Management
- **main**: Production-ready code
- **develop**: Integration branch for features
- **feature/***: Feature branches
- **hotfix/***: Emergency fixes

### Commit Messages
- **Format**: Clear, descriptive commit messages
- **Imperative Mood**: Use imperative mood ("Add feature" not "Added feature")
- **Context**: Include context for changes
- **References**: Reference issue numbers when applicable

### Documentation Updates
- **API Documentation**: Keep OpenAPI documentation current
- **README**: Update README with major changes
- **CLAUDE.md**: Update development guidelines
- **Architecture Docs**: Update architecture documentation

## Security Practices

### Development Security
- **Environment Variables**: Use environment variables for sensitive data
- **Secret Management**: Never commit secrets to version control
- **Dependency Updates**: Regularly update dependencies for security patches
- **Code Reviews**: Security-focused code reviews

### Production Security
- **HTTPS**: Always use HTTPS in production
- **Authentication**: JWT token validation on all protected endpoints
- **Rate Limiting**: Implement rate limiting for API endpoints
- **Input Validation**: Validate all input data with Pydantic models

## Performance Optimization

### Development Performance
- **Hot Reload**: Use development profile for hot reload
- **Local Testing**: Test locally before pushing changes
- **Database Indexing**: Ensure proper indexing for development database
- **Cache Development**: Test caching strategies locally

### Production Performance
- **Database Optimization**: Optimize queries and indexes
- **Caching Strategy**: Implement effective caching strategies
- **Load Balancing**: Use load balancing for high traffic
- **Monitoring**: Monitor performance metrics continuously