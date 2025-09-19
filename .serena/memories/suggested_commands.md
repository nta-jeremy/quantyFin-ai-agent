# Development Commands - QuantyFinAI Agent

## Environment Setup
```bash
# Install dependencies with Poetry
poetry install

# Install development dependencies
poetry install --with=dev,lint,test

# Start local development environment
docker-compose up -d

# Start with hot reload
docker-compose --profile dev up -d
```

## Database Setup
```bash
# Build pgvector database
docker-compose build db

# Start database
docker-compose up -d db

# Verify pgvector installation
docker-compose exec db psql -U quantyfin -d quantyfin -c "SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';"

# Initialize database schema
poetry run python scripts/init_db.py
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

# Run specific test categories
poetry run pytest -m "unit"
poetry run pytest -m "integration"
poetry run pytest -m "e2e"

# Run specific test file
poetry run pytest tests/test_specific.py
```

## Running the Application
```bash
# Development with uvicorn
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# With Poetry
poetry run python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# With Docker
docker-compose up app
```

## Database Operations
```bash
# Check database health
docker-compose exec db psql -U quantyfin -d quantyfin -c "SELECT 'Database is ready' as status;"

# Run migrations
poetry run python scripts/migrations/migration_runner.py

# Test vector operations
docker-compose exec db psql -U quantyfin -d quantyfin -c "CREATE EXTENSION IF NOT EXISTS vector; CREATE TABLE test_vectors (id SERIAL PRIMARY KEY, embedding VECTOR(3) NOT NULL); INSERT INTO test_vectors (embedding) VALUES ('[1,2,3]'), ('[4,5,6]'); SELECT id, embedding, embedding <-> '[0,0,0]' as distance FROM test_vectors ORDER BY distance;"
```

## Docker Management
```bash
# View all service logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f app
docker-compose logs -f db

# Clean rebuild
docker-compose down -v
docker system prune -f
docker-compose build
docker-compose up -d
```

## API Documentation
- **API Docs**: http://localhost:8000/docs
- **OpenAPI Schema**: http://localhost:8000/openapi.json
- **Health Check**: http://localhost:8000/api/v1/health
- **Keycloak Admin**: http://localhost:8080 (admin/admin123)

## Git Operations
```bash
# Check git status
git status

# View staged and unstaged changes
git --no-pager diff

# Add files and commit
git add .
git commit -m "$(printf "Commit message\n\n- Point 1\n- Point 2")"

# Push changes
git push origin main
```