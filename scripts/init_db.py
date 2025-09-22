#!/usr/bin/env python3
"""
Database Initialization Script for QuantyFinAI Agent
Creates database, extensions, and runs initial migrations.
"""

import argparse
import logging
import os
import sys
from pathlib import Path

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.migrations.migration_runner import MigrationRunner

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def create_database(database_url: str, database_name: str) -> bool:
    """Create database if it doesn't exist."""
    # Parse URL to get connection details
    from urllib.parse import urlparse

    parsed_url = urlparse(database_url)

    # Connect to postgres database to create target database
    admin_url = f"postgresql://{parsed_url.username}:{parsed_url.password}@{parsed_url.hostname}:{parsed_url.port}/postgres"

    try:
        conn = psycopg2.connect(admin_url)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()

        # Check if database exists
        cursor.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s", (database_name,)
        )
        exists = cursor.fetchone()

        if not exists:
            cursor.execute(f'CREATE DATABASE "{database_name}"')
            logger.info(f"Database '{database_name}' created successfully")
        else:
            logger.info(f"Database '{database_name}' already exists")

        cursor.close()
        conn.close()
        return True

    except psycopg2.Error as e:
        logger.error(f"Failed to create database: {e}")
        return False


def setup_extensions(database_url: str) -> bool:
    """Setup required PostgreSQL extensions."""
    try:
        conn = psycopg2.connect(database_url)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()

        # Enable required extensions
        extensions = [
            'CREATE EXTENSION IF NOT EXISTS "uuid-ossp";',
            "CREATE EXTENSION IF NOT EXISTS vector;",
            'CREATE EXTENSION IF NOT EXISTS "pg_trgm";',  # For text search
        ]

        for extension_sql in extensions:
            cursor.execute(extension_sql)
            logger.info(f"Extension setup: {extension_sql}")

        cursor.close()
        conn.close()
        return True

    except psycopg2.Error as e:
        logger.error(f"Failed to setup extensions: {e}")
        return False


def seed_initial_data(database_url: str) -> bool:
    """Seed database with initial data."""
    try:
        conn = psycopg2.connect(database_url)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()

        # Check if roles already exist
        cursor.execute("SELECT COUNT(*) FROM roles")
        role_count = cursor.fetchone()[0]

        if role_count == 0:
            # Insert default roles
            roles_data = [
                ("admin", "System administrator with full access"),
                (
                    "analyst",
                    "Financial analyst with read/write access to financial data",
                ),
                ("viewer", "Read-only access to financial data"),
                ("api_user", "API access for external integrations"),
            ]

            cursor.executemany(
                "INSERT INTO roles (name, description) VALUES (%s, %s)",
                roles_data,
            )
            logger.info("Default roles seeded")
        else:
            logger.info("Roles already exist, skipping seed")

        cursor.close()
        conn.close()
        return True

    except psycopg2.Error as e:
        logger.error(f"Failed to seed initial data: {e}")
        return False


def main():
    """Main initialization function."""
    parser = argparse.ArgumentParser(
        description="QuantyFinAI Database Initialization"
    )
    parser.add_argument(
        "--database-url", required=True, help="Database connection URL"
    )
    parser.add_argument(
        "--database-name",
        help="Database name (extracted from URL if not provided)",
    )
    parser.add_argument(
        "--skip-migrations",
        action="store_true",
        help="Skip running migrations",
    )
    parser.add_argument(
        "--skip-seed", action="store_true", help="Skip seeding initial data"
    )

    args = parser.parse_args()

    # Extract database name from URL if not provided
    if not args.database_name:
        from urllib.parse import urlparse

        parsed_url = urlparse(args.database_url)
        args.database_name = parsed_url.path.lstrip("/")

    logger.info("Starting database initialization...")

    # Step 1: Create database
    if not create_database(args.database_url, args.database_name):
        logger.error("Failed to create database")
        sys.exit(1)

    # Step 2: Setup extensions
    if not setup_extensions(args.database_url):
        logger.error("Failed to setup extensions")
        sys.exit(1)

    # Step 3: Run migrations
    if not args.skip_migrations:
        logger.info("Running migrations...")
        runner = MigrationRunner(args.database_url)
        if not runner.run_migrations("scripts/migrations"):
            logger.error("Failed to run migrations")
            sys.exit(1)

    # Step 4: Seed initial data
    if not args.skip_seed:
        logger.info("Seeding initial data...")
        if not seed_initial_data(args.database_url):
            logger.error("Failed to seed initial data")
            sys.exit(1)

    logger.info("Database initialization completed successfully!")


if __name__ == "__main__":
    main()
