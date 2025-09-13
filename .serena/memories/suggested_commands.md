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
```