# Development Commands for QuantyFinAI Agent

## Environment Setup
```bash
# Install dependencies with Poetry
poetry install

# Install development dependencies
poetry install --with=dev,lint,test

# Start local development environment with Docker
docker-compose up -d

# Start development environment with hot reload
docker-compose --profile dev up -d

# Initialize database
poetry run python scripts/init_db.py
```

## Database Operations
```bash
# Build the pgvector database container
docker-compose build db

# Start the database container
docker-compose up -d db

# Verify pgvector installation
docker-compose exec db psql -U quantyfin -d quantyfin -c "SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';"

# Test vector operations
docker-compose exec db psql -U quantyfin -d quantyfin -c "
CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE test_vectors (id SERIAL PRIMARY KEY, embedding VECTOR(3) NOT NULL);
INSERT INTO test_vectors (embedding) VALUES ('[1,2,3]'), ('[4,5,6]');
SELECT id, embedding, embedding <-> '[0,0,0]' as distance FROM test_vectors ORDER BY distance;
"

# Clean build cache and rebuild
docker-compose down -v
docker system prune -f
docker-compose build db
```

## Code Quality
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

## Testing
```bash
# Run all tests
poetry run pytest

# Run tests with coverage
poetry run pytest --cov=app --cov-report=html

# Run specific test file
poetry run pytest tests/test_specific.py

# Run tests with verbose output
poetry run pytest -v

# Run specific test categories
poetry run pytest -m "unit"
poetry run pytest -m "integration"
poetry run pytest -m "e2e"
```

## Running the Application
```bash
# Run with uvicorn (development)
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Run with Poetry
poetry run python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Run with Docker
docker-compose up app

# Run development server with hot reload
docker-compose --profile dev up -d
```

## Container Management
```bash
# View all containers
docker-compose ps

# View application logs
docker-compose logs -f app

# View database logs
docker-compose logs -f db

# View all service logs
docker-compose logs -f

# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v

# Start specific services
docker-compose up -d db redis

# Start development profile
docker-compose --profile dev up -d

# Start test profile
docker-compose --profile test up -d
```

## System Utilities (Darwin/macOS)
```bash
# Find files by name
find . -name "*.py" -type f

# Search for text in files
grep -r "pattern" app/

# Search with ripgrep (faster alternative)
rg "pattern" app/

# Check file sizes and complexity
find . -name "*.py" | xargs wc -l

# Monitor system resources
top

# Check available disk space
df -h

# Check available memory
vm_stat

# List processes
ps aux

# Kill process by ID
kill <pid>

# Force kill process
kill -9 <pid>
```

## Git Operations
```bash
# Check git status
git status

# View staged and unstaged changes
git diff

# Add files to staging area
git add .

# Commit with formatted message
git commit -m "$(printf "Title\n\n- Point 1\n- Point 2")"

# View commit history
git log --oneline

# Pull latest changes
git pull origin main

# Push changes
git push origin main

# Create new branch
git checkout -b feature/branch-name

# Switch to branch
git checkout branch-name

# Delete branch
git branch -d branch-name
```

## Health Checks and Monitoring
```bash
# Check application health
curl http://localhost:8000/api/v1/health

# Check authentication health
curl http://localhost:8000/auth-health

# Test authentication setup
curl http://localhost:8000/auth-test

# Access API documentation
open http://localhost:8000/docs

# Access Keycloak admin console
open http://localhost:8080

# Check database connectivity
docker-compose exec db psql -U quantyfin -d quantyfin -c "SELECT 'Database is ready' as status;"

# Check Redis connectivity
docker-compose exec redis redis-cli ping

# Check Keycloak health
curl http://localhost:8080/health/ready
```

## Keycloak Management
```bash
# Access Keycloak admin console
open http://localhost:8080

# Keycloak admin credentials (default)
# Username: admin
# Password: admin123

# Access Keycloak database
docker-compose exec keycloak-db psql -U keycloak -d keycloak

# Check Keycloak logs
docker-compose logs -f keycloak

# Restart Keycloak
docker-compose restart keycloak
```

## Development Tools
```bash
# Run pre-commit hooks
poetry run pre-commit run --all-files

# Install pre-commit hooks
poetry run pre-commit install

# Run specific pre-commit checks
poetry run pre-commit run black --all-files
poetry run pre-commit run isort --all-files
poetry run pre-commit run flake8 --all-files
poetry run pre-commit run mypy --all-files

# Generate requirements.txt from pyproject.toml
poetry export -f requirements.txt --output requirements.txt --without-hashes

# Check dependency tree
poetry show --tree

# Update dependencies
poetry update

# Add new dependency
poetry add package-name
poetry add --group dev package-name
```

## Performance and Debugging
```bash
# Check application performance
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/api/v1/health

# Monitor database performance
docker-compose exec db psql -U quantyfin -d quantyfin -c "SELECT * FROM pg_stat_activity;"

# Check Redis performance
docker-compose exec redis redis-cli info memory

# Monitor container resource usage
docker stats

# Check container logs with timestamps
docker-compose logs --tail=100 -f app

# Debug container issues
docker-compose run --rm app /bin/bash
```

## Testing Database Operations
```bash
# Test database schema
docker-compose exec db psql -U quantyfin -d quantyfin -c "\dt"

# Test vector operations
docker-compose exec db psql -U quantyfin -d quantyfin -c "
SELECT * FROM information_schema.tables WHERE table_schema = 'public';
"

# Test connection pooling
docker-compose exec db psql -U quantyfin -d quantyfin -c "SELECT count(*) FROM pg_stat_activity;"
```

## Environment Management
```bash
# Copy environment template
cp .env.example .env

# Edit environment file
nano .env
# or
vim .env

# Validate environment configuration
poetry run python -c "from config.settings import get_settings; print('Configuration loaded successfully')"
```

## Backup and Recovery
```bash
# Backup database
docker-compose exec db pg_dump -U quantyfin -d quantyfin > backup.sql

# Restore database
docker-compose exec -i db psql -U quantyfin -d quantyfin < backup.sql

# Backup Redis data
docker-compose exec redis redis-cli BGSAVE

# Copy data volumes
docker cp quantyfin-db:/var/lib/postgresql/data ./backup/postgres_data
docker cp quantyfin-redis:/data ./backup/redis_data
```