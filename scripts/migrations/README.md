# Database Migrations

> **QuantyFinAI Agent** - Database migration system for AI-powered financial analysis and stock prediction platform.

This directory contains the complete database migration system for the QuantyFinAI Agent project, including schema definitions, data seeding, and migration management utilities.

## 📋 Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Migration Files](#migration-files)
- [Environment Configuration](#environment-configuration)
- [Command Reference](#command-reference)
- [Troubleshooting](#troubleshooting)
- [Development Guidelines](#development-guidelines)

## 🚀 Overview

The migration system provides:

- **Versioned Schema Management**: Sequential SQL migrations with tracking
- **Data Seeding**: Initial data setup for development and testing
- **Rollback Support**: Safe migration reversal capabilities
- **Checksum Validation**: Integrity verification for migration files
- **Environment Flexibility**: Support for multiple deployment environments

## ⚡ Quick Start

### Prerequisites

- **PostgreSQL 12+** with required extensions
- **Python 3.12+** (as specified in pyproject.toml)
- **Required Extensions**: `uuid-ossp`, `vector`, `pg_trgm`

### Installation

1. **Install project dependencies**:
   ```bash
   # Using Poetry (recommended)
   poetry install
   
   # Or using pip
   pip install -e .
   ```

2. **Set up environment variables**:
   ```bash
   export DATABASE_URL="postgresql://username:password@localhost:5432/quantyfin_db"
   export MIGRATIONS_DIR="scripts/migrations"
   export RETENTION_DAYS=30
   ```

3. **Initialize database**:
   ```bash
   python scripts/migrations/init_db.py --database-url "$DATABASE_URL"
   ```

4. **Run migrations**:
   ```bash
   python scripts/migrations/migration_runner.py migrate --database-url "$DATABASE_URL"
   ```

## 📁 Migration Files

| File | Description | Dependencies |
|------|-------------|--------------|
| `001_initial_schema.sql` | Core application tables (users, roles, companies, sessions) | PostgreSQL 12+ |
| `002_financial_data.sql` | Financial data tables (stocks, market data, indicators) | `001_initial_schema.sql` |
| `003_vector_database.sql` | Vector database setup for RAG and AI embeddings | `002_financial_data.sql` |
| `004_analytics_tables.sql` | Analytics, monitoring, and reporting tables | `003_vector_database.sql` |

### Migration Dependencies

```mermaid
graph TD
    A[001_initial_schema.sql] --> B[002_financial_data.sql]
    B --> C[003_vector_database.sql]
    C --> D[004_analytics_tables.sql]
```

## 🔧 Environment Configuration

### Required Environment Variables

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `DATABASE_URL` | PostgreSQL connection string | *Required* | `postgresql://user:pass@localhost:5432/db` |
| `MIGRATIONS_DIR` | Path to migrations directory | `scripts/migrations` | `/path/to/migrations` |
| `RETENTION_DAYS` | Data retention period for cleanup | `30` | `90` |

### Database Extensions

Ensure the following PostgreSQL extensions are installed:

```sql
-- Required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
```

## 📖 Command Reference

### Migration Runner

The `migration_runner.py` script provides comprehensive migration management:

#### Run Migrations
```bash
# Run all pending migrations
python scripts/migrations/migration_runner.py migrate --database-url "$DATABASE_URL"

# Run migrations up to specific version
python scripts/migrations/migration_runner.py migrate \
  --database-url "$DATABASE_URL" \
  --target-version "002_financial_data"

# Use custom migrations directory
python scripts/migrations/migration_runner.py migrate \
  --database-url "$DATABASE_URL" \
  --migrations-dir "/custom/path"
```

#### Check Status
```bash
# Show migration status
python scripts/migrations/migration_runner.py status --database-url "$DATABASE_URL"
```

#### Rollback (Future Feature)
```bash
# Rollback specific migration
python scripts/migrations/migration_runner.py rollback \
  --database-url "$DATABASE_URL" \
  --version "002_financial_data"
```

### Database Initialization

The `init_db.py` script handles complete database setup:

#### Full Initialization
```bash
# Complete setup with migrations and seeding
python scripts/migrations/init_db.py --database-url "$DATABASE_URL"
```

#### Selective Initialization
```bash
# Skip migrations (schema only)
python scripts/migrations/init_db.py \
  --database-url "$DATABASE_URL" \
  --skip-migrations

# Skip data seeding
python scripts/migrations/init_db.py \
  --database-url "$DATABASE_URL" \
  --skip-seed

# Dry run (preview only)
python scripts/migrations/init_db.py \
  --database-url "$DATABASE_URL" \
  --dry-run
```

## 🛠️ Troubleshooting

### Common Issues

#### Connection Errors
```bash
# Verify database connectivity
psql "$DATABASE_URL" -c "SELECT version();"

# Check if database exists
psql "$DATABASE_URL" -c "\l"
```

#### Migration Failures
```bash
# Check migration status
python scripts/migrations/migration_runner.py status --database-url "$DATABASE_URL"

# Verify migration file syntax
psql "$DATABASE_URL" -f scripts/migrations/001_initial_schema.sql --dry-run
```

#### Extension Issues
```sql
-- Check installed extensions
SELECT * FROM pg_extension WHERE extname IN ('uuid-ossp', 'vector', 'pg_trgm');

-- Install missing extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
```

### Logging

Migration operations are logged with timestamps and detailed error information:

```bash
# Enable debug logging
export PYTHONPATH=.
python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
# Run your migration command
"
```

## 👨‍💻 Development Guidelines

### Creating New Migrations

1. **Naming Convention**: Use sequential numbering with descriptive names
   ```
   005_new_feature.sql
   006_another_feature.sql
   ```

2. **File Structure**:
   ```sql
   -- Migration: 005_new_feature
   -- Description: Add new feature tables
   -- Dependencies: 004_analytics_tables
   -- Created: 2024-01-15
   
   BEGIN;
   
   -- Your migration SQL here
   
   COMMIT;
   ```

3. **Best Practices**:
   - Always use transactions (`BEGIN`/`COMMIT`)
   - Include rollback instructions in comments
   - Test migrations on development database first
   - Validate data integrity after migration

### Testing Migrations

```bash
# Test migration on development database
export DATABASE_URL="postgresql://user:pass@localhost:5432/quantyfin_dev"
python scripts/migrations/migration_runner.py migrate --database-url "$DATABASE_URL"

# Verify schema changes
psql "$DATABASE_URL" -c "\dt"
psql "$DATABASE_URL" -c "\d+ table_name"
```

### Code Quality

The migration system follows the project's code quality standards:

- **Type Hints**: All Python code uses strict typing
- **Error Handling**: Comprehensive error handling with specific exceptions
- **Logging**: Structured logging with appropriate levels
- **Documentation**: Clear docstrings and comments

## 📚 Additional Resources

- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [pgvector Extension](https://github.com/pgvector/pgvector)
- [Project Architecture](../docs/System%20Architecture.md)
- [Database Schemas](../docs/Database%20Schemas.md)

---

**Note**: This migration system is designed for the QuantyFinAI Agent project. For questions or issues, please refer to the project documentation or create an issue in the repository.