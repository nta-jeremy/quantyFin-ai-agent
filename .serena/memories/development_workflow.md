# Development Workflow - QuantyFinAI Agent

## Project Structure
```
app/
├── core/                 # Domain layer (business logic, entities)
│   ├── domain/          # Domain models and services
│   └── application/    # Use cases and application services
├── infrastructure/      # External service implementations
│   ├── persistence/    # Database adapters and repositories
│   ├── auth/          # Authentication (Keycloak)
│   ├── cache/         # Redis caching
│   └── api/           # External API clients
├── interfaces/         # API endpoints and CLI
│   ├── api/           # FastAPI routes and dependencies
│   └── cli/           # Command-line interface
└── agents/            # AI agent implementations (LangGraph)
```

## Git Workflow
1. **Feature Branches**: Create feature branches from `dev` or `main`
2. **Small Commits**: Make frequent, small commits with clear messages
3. **Code Quality**: Run quality checks before committing
4. **Testing**: Ensure all tests pass before pushing

## Development Process

### 1. Setup
```bash
# Clone and setup
git clone <repository>
cd quantyFin-ai-agent
poetry install --with=dev,lint,test
cp .env.example .env
docker-compose up -d
```

### 2. Code Development
```bash
# Create feature branch
git checkout -b feature/new-feature

# Work on code with hot reload
docker-compose --profile dev up -d

# Run quality checks frequently
poetry run black . && poetry run isort . && poetry run flake8 .
```

### 3. Testing
```bash
# Run tests during development
poetry run pytest

# Run specific tests
poetry run pytest -m "unit"
poetry run pytest -m "integration"

# Check coverage
poetry run pytest --cov=app --cov-report=html
```

### 4. Code Review Process
1. **Self-review**: Run all quality checks
2. **Pre-commit**: Ensure pre-commit hooks pass
3. **Pull Request**: Create detailed PR with:
   - Clear description of changes
   - Testing approach
   - Related issues

### 5. Integration Testing
```bash
# Test full stack
docker-compose up -d

# Test API endpoints
curl http://localhost:8000/api/v1/health
curl http://localhost:8000/docs

# Test database
docker-compose exec db psql -U quantyfin -d quantyfin
```

## Pre-commit Workflow
```bash
# Install pre-commit hooks
pre-commit install

# Run manually
pre-commit run --all-files

# Hooks include:
# - black (code formatting)
# - isort (import sorting)
# - flake8 (linting)
# - mypy (type checking)
# - bandit (security)
# - pytest (tests)
```

## Database Workflow
```bash
# Schema changes:
# 1. Create migration file in scripts/migrations/
# 2. Update models in app/core/domain/models.py
# 3. Update repositories in app/infrastructure/persistence/
# 4. Test with existing data
# 5. Run migration runner
```

## Authentication Development
1. **Keycloak Setup**: Ensure Keycloak is running
2. **Token Management**: Test token generation and validation
3. **Role-based Access**: Implement proper RBAC checks
4. **Session Management**: Test Redis session storage

## AI Agent Development
1. **Agent Creation**: Add new agents in app/agents/
2. **LangGraph Integration**: Use LangGraph for agent orchestration
3. **Testing**: Test agent workflows individually and integrated
4. **Performance**: Monitor agent response times and resource usage

## Deployment Process
1. **Build**: Create optimized Docker images
2. **Test**: Run comprehensive test suite
3. **Security**: Run security scans
4. **Deploy**: Deploy to target environment
5. **Monitor**: Set up monitoring and alerting

## Troubleshooting
```bash
# Common issues:
# Database connection: Check docker-compose logs db
# Authentication: Check Keycloak logs and configuration
# Redis: Check Redis logs and connection settings
# Performance: Check database queries and indexing
```

## Quality Gates
- **Code Coverage**: Minimum 80% coverage
- **Type Safety**: No mypy errors
- **Linting**: No flake8 errors
- **Security**: No bandit issues
- **Tests**: All tests must pass