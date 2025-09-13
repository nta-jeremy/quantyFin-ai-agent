"""
Database Migration Package for QuantyFinAI Agent

This package contains database migration scripts and utilities for managing
database schema changes in the QuantyFinAI Agent system.

Migration Files:
- 001_initial_schema.sql: Core tables (users, roles, companies)
- 002_financial_data.sql: Financial data tables (reports, stock data)
- 003_vector_database.sql: Vector database setup for RAG system

Utilities:
- migration_runner.py: Python script for running migrations
- init_db.py: Database initialization script
"""

__version__ = "1.0.0"
__author__ = "QuantyFinAI Team"
