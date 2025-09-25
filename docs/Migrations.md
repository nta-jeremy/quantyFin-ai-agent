# Database Migrations

This document outlines the database migration system for the QuantyFinAI Agent project. The migration system ensures consistent database schema evolution across different environments.

## Migration Files

### Core Schema Migrations

#### 001_initial_schema.sql
- **Purpose**: Create initial database schema with core tables
- **Tables Created**:
  - `roles`: User roles for RBAC system
  - `users`: User authentication and profile information
- **Features**:
  - UUID primary keys for better scalability
  - Automatic timestamp triggers for `updated_at` fields
  - Default role seeding (admin, analyst, viewer, api_user)
  - Performance indexes on frequently queried columns

#### 003_vector_database.sql
- **Purpose**: Setup vector database for RAG system with pgvector extension
- **Tables Created**:
  - `document_embeddings`: Vector embeddings for semantic search
  - `document_sources`: Original document metadata
  - `user_queries`: User interaction tracking
  - `query_embeddings`: Query vectors for similarity search
- **Features**:
  - HNSW indexes for efficient vector similarity search
  - Support for multiple distance metrics (cosine, L2, inner product)
  - Hybrid search functions combining vector and text search
  - Automatic cleanup functions for old embeddings

## Migration Utilities

### Migration Runner (`migration_runner.py`)
A Python script for managing database migrations with the following features:

- **Commands**:
  - `migrate`: Run pending migrations
  - `status`: Show migration status
  - `rollback`: Rollback specific migration (future feature)
- **Features**:
  - Automatic migration tracking
  - Checksum validation
  - Transaction safety
  - Detailed logging
  - Target version support

### Database Initialization (`init_db.py`)
A comprehensive database setup script that:

- Creates database if it doesn't exist
- Sets up required PostgreSQL extensions
- Runs all migrations
- Seeds initial data
- Provides command-line options for customization

## Usage

### Running Migrations

```bash
# Run all pending migrations
python scripts/migrations/migration_runner.py migrate --database-url "postgresql://user:pass@localhost/dbname"

# Check migration status
python scripts/migrations/migration_runner.py status --database-url "postgresql://user:pass@localhost/dbname"

# Run migrations up to specific version
python scripts/migrations/migration_runner.py migrate --database-url "postgresql://user:pass@localhost/dbname" --target-version "002_financial_data"
```

### Database Initialization

```bash
# Full database initialization
python scripts/init_db.py --database-url "postgresql://user:pass@localhost/dbname"

# Skip migrations (if already run)
python scripts/init_db.py --database-url "postgresql://user:pass@localhost/dbname" --skip-migrations

# Skip initial data seeding
python scripts/init_db.py --database-url "postgresql://user:pass@localhost/dbname" --skip-seed
```

## Database Extensions

The migration system automatically installs the following PostgreSQL extensions:

- **uuid-ossp**: For UUID generation
- **vector**: For vector similarity search (pgvector)
- **pg_trgm**: For text search and similarity

## Migration Best Practices

1. **Always backup** the database before running migrations in production
2. **Test migrations** in a development environment first
3. **Use transactions** - migrations are wrapped in transactions for safety
4. **Version control** - all migration files are versioned and tracked
5. **Rollback planning** - consider rollback strategies for complex migrations
6. **Performance testing** - test migration performance on large datasets

## Troubleshooting

### Common Issues

1. **Extension not found**: Ensure PostgreSQL has the required extensions installed
2. **Permission denied**: Check database user permissions
3. **Migration already applied**: Use `status` command to check current state
4. **Checksum mismatch**: Re-download migration files or check for corruption

### Recovery

If a migration fails:
1. Check the error logs for specific issues
2. Fix the underlying problem
3. Re-run the migration
4. If necessary, manually update the `schema_migrations` table

## Future Enhancements

- [ ] Automated rollback scripts
- [ ] Migration dependency management
- [ ] Parallel migration execution
- [ ] Migration performance metrics
- [ ] Automated testing of migrations
