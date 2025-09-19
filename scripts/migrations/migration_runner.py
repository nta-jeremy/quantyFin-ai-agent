#!/usr/bin/env python3
"""
Migration Runner for QuantyFinAI Agent Database
Handles database migrations with proper error handling and rollback capabilities.
"""

import argparse
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MigrationRunner:
    """Handles database migrations with rollback support."""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.connection = None
        self.migrations_table = "schema_migrations"
    
    def connect(self) -> None:
        """Establish database connection."""
        try:
            self.connection = psycopg2.connect(self.database_url)
            self.connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            logger.info("Database connection established")
        except psycopg2.Error as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    def disconnect(self) -> None:
        """Close database connection."""
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed")
    
    def create_migrations_table(self) -> None:
        """Create migrations tracking table if it doesn't exist."""
        cursor = self.connection.cursor()
        try:
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.migrations_table} (
                    id SERIAL PRIMARY KEY,
                    version VARCHAR(50) UNIQUE NOT NULL,
                    filename VARCHAR(255) NOT NULL,
                    applied_at TIMESTAMP DEFAULT NOW(),
                    checksum VARCHAR(64)
                )
            """)
            logger.info("Migrations table created/verified")
        except psycopg2.Error as e:
            logger.error(f"Failed to create migrations table: {e}")
            raise
        finally:
            cursor.close()
    
    def get_applied_migrations(self) -> List[str]:
        """Get list of already applied migrations."""
        cursor = self.connection.cursor()
        try:
            cursor.execute(f"SELECT version FROM {self.migrations_table} ORDER BY version")
            return [row[0] for row in cursor.fetchall()]
        except psycopg2.Error as e:
            logger.error(f"Failed to get applied migrations: {e}")
            raise
        finally:
            cursor.close()
    
    def get_migration_files(self, migrations_dir: str) -> List[Path]:
        """Get list of migration files sorted by version."""
        migrations_path = Path(migrations_dir)
        if not migrations_path.exists():
            raise FileNotFoundError(f"Migrations directory not found: {migrations_dir}")
        
        migration_files = list(migrations_path.glob("*.sql"))
        migration_files.sort(key=lambda x: x.stem)
        return migration_files
    
    def calculate_checksum(self, file_path: Path) -> str:
        """Calculate MD5 checksum of migration file."""
        import hashlib
        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    
    def apply_migration(self, migration_file: Path) -> bool:
        """Apply a single migration file."""
        version = migration_file.stem
        checksum = self.calculate_checksum(migration_file)
        
        cursor = self.connection.cursor()
        try:
            # Read migration file
            with open(migration_file, 'r', encoding='utf-8') as f:
                migration_sql = f.read()
            
            # Execute migration
            cursor.execute(migration_sql)
            
            # Record migration
            cursor.execute(f"""
                INSERT INTO {self.migrations_table} (version, filename, checksum)
                VALUES (%s, %s, %s)
            """, (version, migration_file.name, checksum))
            
            logger.info(f"Applied migration: {version}")
            return True
            
        except psycopg2.Error as e:
            logger.error(f"Failed to apply migration {version}: {e}")
            return False
        finally:
            cursor.close()
    
    def rollback_migration(self, version: str) -> bool:
        """Rollback a specific migration (if rollback SQL exists)."""
        # This is a simplified implementation
        # In production, you'd want to maintain rollback scripts
        logger.warning(f"Rollback not implemented for version: {version}")
        return False
    
    def run_migrations(self, migrations_dir: str, target_version: Optional[str] = None) -> bool:
        """Run all pending migrations."""
        try:
            self.connect()
            self.create_migrations_table()
            
            applied_migrations = set(self.get_applied_migrations())
            migration_files = self.get_migration_files(migrations_dir)
            
            success_count = 0
            total_pending = 0
            
            for migration_file in migration_files:
                version = migration_file.stem
                
                if version in applied_migrations:
                    logger.info(f"Migration {version} already applied, skipping")
                    continue
                
                if target_version and version > target_version:
                    logger.info(f"Reached target version {target_version}, stopping")
                    break
                
                total_pending += 1
                if self.apply_migration(migration_file):
                    success_count += 1
                else:
                    logger.error(f"Failed to apply migration {version}, stopping")
                    break
            
            logger.info(f"Migration completed: {success_count}/{total_pending} migrations applied")
            return success_count == total_pending
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            return False
        finally:
            self.disconnect()
    
    def status(self, migrations_dir: str) -> None:
        """Show migration status."""
        try:
            self.connect()
            self.create_migrations_table()
            
            applied_migrations = set(self.get_applied_migrations())
            migration_files = self.get_migration_files(migrations_dir)
            
            print("\nMigration Status:")
            print("=" * 50)
            
            for migration_file in migration_files:
                version = migration_file.stem
                status = "APPLIED" if version in applied_migrations else "PENDING"
                print(f"{version:<20} {status}")
            
            print("=" * 50)
            
        except Exception as e:
            logger.error(f"Failed to get migration status: {e}")
        finally:
            self.disconnect()


def main():
    """Main entry point for migration runner."""
    parser = argparse.ArgumentParser(description="QuantyFinAI Database Migration Runner")
    parser.add_argument("command", choices=["migrate", "status", "rollback"], 
                       help="Migration command to execute")
    parser.add_argument("--database-url", required=True,
                       help="Database connection URL")
    parser.add_argument("--migrations-dir", default="scripts/migrations",
                       help="Directory containing migration files")
    parser.add_argument("--target-version", 
                       help="Target migration version (for migrate command)")
    parser.add_argument("--version", 
                       help="Version to rollback (for rollback command)")
    
    args = parser.parse_args()
    
    runner = MigrationRunner(args.database_url)
    
    if args.command == "migrate":
        success = runner.run_migrations(args.migrations_dir, args.target_version)
        sys.exit(0 if success else 1)
    elif args.command == "status":
        runner.status(args.migrations_dir)
    elif args.command == "rollback":
        if not args.version:
            logger.error("Version required for rollback command")
            sys.exit(1)
        success = runner.rollback_migration(args.version)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
