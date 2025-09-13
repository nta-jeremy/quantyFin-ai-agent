# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Development Commands

### Environment Setup
```bash
# Install dependencies with Poetry
poetry install

# Install development dependencies
poetry install --with=dev,lint,test

# Start local development environment with Docker
docker-compose up -d

# Start development environment with hot reload
docker-compose --profile dev up -d
```

### pgvector Database Setup
The project uses PostgreSQL with pgvector extension for vector operations. The database is configured in `Dockerfile.pgvector`.

**Building the pgvector Database:**
```bash
# Build the pgvector database container
docker-compose build db

# Start the database container
docker-compose up -d db

# Verify pgvector installation
docker-compose exec db psql -U quantyfin -d quantyfin -c "SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';"
```

**Troubleshooting pgvector Build Issues:**
If you encounter build errors with pgvector, try these solutions:

1. **Clean build cache and rebuild:**
   ```bash
   docker-compose down -v
   docker system prune -f
   docker-compose build db
   ```

2. **Use Debian base instead of Alpine:**
   The `Dockerfile.pgvector` uses Debian-based PostgreSQL image for better compatibility with pgvector build dependencies.

3. **Verify build dependencies:**
   The Dockerfile installs: `build-essential`, `postgresql-server-dev-16`, `git`, `clang`, `llvm-dev`, `cmake`

4. **Test vector functionality:**
   ```bash
   # Test vector operations
   docker-compose exec db psql -U quantyfin -d quantyfin -c "
   CREATE EXTENSION IF NOT EXISTS vector;
   CREATE TABLE test_vectors (id SERIAL PRIMARY KEY, embedding VECTOR(3) NOT NULL);
   INSERT INTO test_vectors (embedding) VALUES ('[1,2,3]'), ('[4,5,6]');
   SELECT id, embedding, embedding <-> '[0,0,0]' as distance FROM test_vectors ORDER BY distance;
   "
   ```

### Code Quality
```bash
# Format code with Black
poetry run black .

# Sort imports with isort
poetry run isort .

# Lint with flake8
poetry run flake8 .

# Type checking with mypy
poetry run mypy app/

# Run all quality checks
poetry run black . && poetry run isort . && poetry run flake8 . && poetry run mypy app/
```

### Testing
```bash
# Run all tests
poetry run pytest

# Run tests with coverage
poetry run pytest --cov=app --cov-report=html

# Run specific test file
poetry run pytest tests/test_specific.py

# Run tests with verbose output
poetry run pytest -v
```

### Running the Application
```bash
# Run with uvicorn (development)
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Run with Poetry
poetry run python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Run with Docker
docker-compose up app
```

### Database Operations
```bash
# Initialize database
poetry run python scripts/init_db.py

# Run database migrations (if using Alembic)
poetry run alembic upgrade head

# Create new migration
poetry run alembic revision --autogenerate -m "description"
```

## Architecture Overview

### Hexagonal Architecture
This project follows hexagonal architecture (ports and adapters pattern) with clean separation of concerns:

- **Domain Layer** (`app/core/domain/`): Business logic, entities, and service interfaces
- **Application Layer** (`app/core/application/`): Use cases and application services
- **Infrastructure Layer** (`app/infrastructure/`): External service implementations
- **Interface Layer** (`app/interfaces/`): API endpoints and CLI interfaces
- **Agents Layer** (`app/agents/`): AI agent implementations for LangGraph orchestration

### Multi-Agent RAG System
The system implements a 7-agent RAG architecture using LangGraph:

1. **Guard Agent**: Input validation and prompt injection protection
2. **Embedding Agent**: Document processing and vector embedding generation
3. **Retriever Agent**: Query transformation and data retrieval
4. **Search Agent**: External API integration and web search
5. **Analyze Agent**: Financial analysis and sentiment processing
6. **Predict Agent**: ML model predictions and forecasting
7. **Aggregator Agent**: Workflow orchestration and response synthesis

### Database Architecture
- **Primary Database**: PostgreSQL with pgvector extension for vector search
- **Vector Storage**: Native PostgreSQL vector storage with HNSW indexing
- **Caching Layer**: Redis for session management, rate limiting, and data caching
- **Authentication**: Keycloak integration with JWT token management

## Key Components

### Database Adapters
Located in `app/infrastructure/persistence/`:

- **PostgreSQL Adapter**: Connection pooling, transaction management, repository implementations
- **Vector DB Adapter**: Vector similarity search, embedding storage, HNSW indexing
- **Repository Pattern**: Abstract interfaces with PostgreSQL implementations

Example usage:
```python
# Database connection management
db_manager = DatabaseManager(database_url=settings.database.url)
await db_manager.initialize()

# Using repositories
users = await db_manager.user_repo.list_all()
company = await db_manager.company_repo.get_by_ticker("AAPL")
```

### Authentication System
Keycloak integration in `app/infrastructure/auth/keycloak_adapter.py`:

- JWT token validation and refresh
- Role-based access control (RBAC)
- User management and session handling
- OAuth2 authorization code flow

Example usage:
```python
# Initialize Keycloak manager
auth_manager = KeycloakAuthManager()
await auth_manager.initialize()

# Authenticate user
auth_result = await auth_manager.authenticate_user(username, password)

# Validate token
claims = await auth_manager.validate_token(access_token)
```

### Caching System
Redis adapter in `app/infrastructure/cache/redis_adapter.py`:

- Session management with TTL
- Rate limiting for API endpoints
- Batch operations support
- Key-based caching strategies

Example usage:
```python
# Initialize Redis manager
cache_manager = RedisCacheManager(redis_url=settings.redis.url)
await cache_manager.initialize()

# Basic caching
await cache_manager.cache_adapter.set("key", data, expire_seconds=3600)
cached_data = await cache_manager.cache_adapter.get("key")

# Rate limiting
rate_limit = await cache_manager.rate_limiter.check_rate_limit("user_id", 100, 3600)
if rate_limit["is_limited"]:
    raise HTTPException(status_code=429, detail="Rate limit exceeded")
```

### Configuration Management
Settings in `config/settings.py` using Pydantic:

- Environment-specific configurations
- Type-safe configuration access
- Secret management with SecretStr
- Nested configuration groups

Example usage:
```python
from config.settings import get_settings

settings = get_settings()

# Access configuration
database_url = settings.database.url
max_connections = settings.database.pool_size
is_development = settings.is_development
```

## Development Patterns

### Repository Pattern
All database operations use the repository pattern with abstract interfaces:

```python
# Abstract interface
class UserRepository(ABC):
    @abstractmethod
    async def create(self, user: User) -> User:
        pass

    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        pass

# PostgreSQL implementation
class PostgreSQLUserRepository(UserRepository):
    async def create(self, user: User) -> User:
        # Implementation with asyncpg
        pass
```

### Dependency Injection
Services use dependency injection for testability and modularity:

```python
class SomeService:
    def __init__(
        self,
        user_repo: UserRepository,
        cache_manager: RedisCacheManager,
        auth_manager: KeycloakAuthManager,
    ):
        self.user_repo = user_repo
        self.cache_manager = cache_manager
        self.auth_manager = auth_manager
```

### Type Safety
- All functions have strict type hints
- Pydantic models for data validation
- mypy for static type checking
- No usage of `Any` type except for external API responses

### Error Handling
- Specific exception types for different error scenarios
- Proper error logging with context
- HTTP status codes for API errors
- Never silently ignore exceptions

## Testing Guidelines

### Test Structure
```
tests/
├── unit/           # Unit tests for individual components
├── integration/    # Integration tests for service interactions
├── e2e/           # End-to-end tests for complete workflows
└── fixtures/      # Test data and mock configurations
```

### Testing Patterns
```python
# Use pytest-asyncio for async tests
@pytest.mark.asyncio
async def test_user_creation():
    # Arrange
    user_data = UserCreate(email="test@example.com", ...)

    # Act
    created_user = await user_repo.create(user_data)

    # Assert
    assert created_user.email == user_data.email
    assert created_user.id is not None

# Use factory-boy for test data
class UserFactory(factory.Factory):
    class Meta:
        model = User

    email = factory.Faker("email")
    username = factory.Faker("user_name")
```

## API Development

### FastAPI Patterns
- Use dependency injection for FastAPI endpoints
- Implement proper response models with Pydantic
- Use async/await for all database operations
- Include comprehensive OpenAPI documentation

Example endpoint:
```python
@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repo),
):
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
```

### Security Practices
- Always validate input data with Pydantic models
- Use parameterized queries to prevent SQL injection
- Implement proper CORS configuration
- Validate JWT tokens on protected endpoints
- Use HTTPS in production environments

## Performance Considerations

### Database Optimization
- Use connection pooling for PostgreSQL connections
- Implement proper indexing strategy for vector search
- Batch operations for multiple database operations
- Use Redis caching for frequently accessed data

### Async Patterns
- Use async/await consistently throughout the application
- Avoid blocking operations in async contexts
- Use asyncpg for PostgreSQL operations
- Implement proper timeout handling for external API calls

## Deployment

### Docker Configuration
- Multi-stage builds for optimized image size
- Health checks for container monitoring
- Environment-specific configurations
- Proper non-root user setup

### CI/CD Pipeline
- Automated testing on all pull requests
- Code quality checks (Black, isort, flake8, mypy)
- Security scanning with Trivy
- Automated Docker builds and deployment

### Code Style
- Always use async/await for all database operations
- Do not use validator instead of field_validator in Pydantic
- Always use timezone.utc for datetime operations.
- Always keep the logic in each file under 500 lines. If the logic exceeds 500 lines, consider splitting the file or refactoring/optimizing the code or consider moving the logic to a different file (except for the test files).