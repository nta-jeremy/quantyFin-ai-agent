"""
PostgreSQL adapter implementation for QuantyFinAI Agent.

This module provides concrete implementations of database repositories
using PostgreSQL with asyncpg for high performance.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, AsyncGenerator, Dict, List, Optional
from uuid import UUID

import asyncpg
from asyncpg.exceptions import PostgresError

from app.core.domain.models import (
    Company,
    DocumentEmbedding,
    FinancialMetrics,
    FinancialReport,
    Prediction,
    Query,
    Role,
    SentimentAnalysis,
    StockData,
    User,
)
from app.core.domain.services import (
    CompanyRepository,
    DatabaseConnection,
    DocumentEmbeddingRepository,
    FinancialMetricsRepository,
    FinancialReportRepository,
    PredictionRepository,
    QueryRepository,
    RoleRepository,
    SentimentAnalysisRepository,
    StockDataRepository,
    UserRepository,
)
from config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class PostgreSQLConnection(DatabaseConnection):
    """PostgreSQL connection manager."""

    def __init__(self, database_url: str):
        self.database_url = database_url
        self.pool = None

    async def connect(self) -> None:
        """Establish PostgreSQL connection pool."""
        try:
            self.pool = await asyncpg.create_pool(
                self.database_url,
                min_size=5,
                max_size=20,
                command_timeout=60,
            )
            logger.info("PostgreSQL connection pool created successfully")
        except Exception as e:
            logger.error(f"Failed to create PostgreSQL connection pool: {e}")
            raise

    async def disconnect(self) -> None:
        """Close PostgreSQL connection pool."""
        if self.pool:
            await self.pool.close()
            logger.info("PostgreSQL connection pool closed")

    async def health_check(self) -> bool:
        """Check PostgreSQL connection health."""
        try:
            if not self.pool:
                return False

            async with self.pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"PostgreSQL health check failed: {e}")
            return False

    async def execute_query(self, query: str, *args) -> List[Dict[str, Any]]:
        """Execute a query and return results."""
        if not self.pool:
            raise RuntimeError("Database not connected")

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, *args)
            return [dict(row) for row in rows]

    async def execute_transaction(self, operations: List[tuple]) -> None:
        """Execute multiple operations in a transaction."""
        if not self.pool:
            raise RuntimeError("Database not connected")

        async with self.pool.acquire() as conn:
            async with conn.transaction():
                for query, *args in operations:
                    await conn.execute(query, *args)


class PostgreSQLUserRepository(UserRepository):
    """PostgreSQL implementation of UserRepository."""

    def __init__(self, db_connection: PostgreSQLConnection):
        self.db = db_connection

    async def create(self, user: User) -> User:
        """Create a new user."""
        query = """
        INSERT INTO users (id, username, email, password_hash, created_at, updated_at, role_id, is_active)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        RETURNING *
        """
        result = await self.db.execute_query(
            query,
            user.id,
            user.username,
            user.email,
            user.password_hash,
            user.created_at,
            user.updated_at,
            user.role_id,
            user.is_active,
        )
        return User(**result[0])

    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        """Get user by ID."""
        query = "SELECT * FROM users WHERE id = $1"
        result = await self.db.execute_query(query, user_id)
        return User(**result[0]) if result else None

    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        query = "SELECT * FROM users WHERE username = $1"
        result = await self.db.execute_query(query, username)
        return User(**result[0]) if result else None

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        query = "SELECT * FROM users WHERE email = $1"
        result = await self.db.execute_query(query, email)
        return User(**result[0]) if result else None

    async def update(self, user: User) -> User:
        """Update an existing user."""
        user.updated_at = datetime.now(timezone.utc)
        query = """
        UPDATE users
        SET username = $2, email = $3, password_hash = $4, updated_at = $5, role_id = $6, is_active = $7
        WHERE id = $1
        RETURNING *
        """
        result = await self.db.execute_query(
            query,
            user.id,
            user.username,
            user.email,
            user.password_hash,
            user.updated_at,
            user.role_id,
            user.is_active,
        )
        return User(**result[0])

    async def delete(self, user_id: UUID) -> bool:
        """Delete a user."""
        query = "DELETE FROM users WHERE id = $1"
        result = await self.db.execute_query(query, user_id)
        return len(result) > 0

    async def list_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        """List all users with pagination."""
        query = (
            "SELECT * FROM users ORDER BY created_at DESC LIMIT $1 OFFSET $2"
        )
        result = await self.db.execute_query(query, limit, skip)
        return [User(**row) for row in result]


class PostgreSQLRoleRepository(RoleRepository):
    """PostgreSQL implementation of RoleRepository."""

    def __init__(self, db_connection: PostgreSQLConnection):
        self.db = db_connection

    async def get_by_id(self, role_id: int) -> Optional[Role]:
        """Get role by ID."""
        query = "SELECT * FROM roles WHERE id = $1"
        result = await self.db.execute_query(query, role_id)
        return Role(**result[0]) if result else None

    async def get_by_name(self, name: str) -> Optional[Role]:
        """Get role by name."""
        query = "SELECT * FROM roles WHERE name = $1"
        result = await self.db.execute_query(query, name)
        return Role(**result[0]) if result else None

    async def list_all(self) -> List[Role]:
        """List all roles."""
        query = "SELECT * FROM roles ORDER BY id"
        result = await self.db.execute_query(query)
        return [Role(**row) for row in result]


class PostgreSQLCompanyRepository(CompanyRepository):
    """PostgreSQL implementation of CompanyRepository."""

    def __init__(self, db_connection: PostgreSQLConnection):
        self.db = db_connection

    async def create(self, company: Company) -> Company:
        """Create a new company."""
        query = """
        INSERT INTO companies (id, name, ticker_symbol, industry, country, founded_date, created_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        RETURNING *
        """
        result = await self.db.execute_query(
            query,
            company.id,
            company.name,
            company.ticker_symbol,
            company.industry,
            company.country,
            company.founded_date,
            company.created_at,
        )
        return Company(**result[0])

    async def get_by_id(self, company_id: UUID) -> Optional[Company]:
        """Get company by ID."""
        query = "SELECT * FROM companies WHERE id = $1"
        result = await self.db.execute_query(query, company_id)
        return Company(**result[0]) if result else None

    async def get_by_ticker(self, ticker_symbol: str) -> Optional[Company]:
        """Get company by ticker symbol."""
        query = "SELECT * FROM companies WHERE ticker_symbol = $1"
        result = await self.db.execute_query(query, ticker_symbol)
        return Company(**result[0]) if result else None

    async def update(self, company: Company) -> Company:
        """Update an existing company."""
        query = """
        UPDATE companies
        SET name = $2, ticker_symbol = $3, industry = $4, country = $5, founded_date = $6
        WHERE id = $1
        RETURNING *
        """
        result = await self.db.execute_query(
            query,
            company.id,
            company.name,
            company.ticker_symbol,
            company.industry,
            company.country,
            company.founded_date,
        )
        return Company(**result[0])

    async def list_all(self, skip: int = 0, limit: int = 100) -> List[Company]:
        """List all companies with pagination."""
        query = "SELECT * FROM companies ORDER BY name LIMIT $1 OFFSET $2"
        result = await self.db.execute_query(query, limit, skip)
        return [Company(**row) for row in result]


class PostgreSQLStockDataRepository(StockDataRepository):
    """PostgreSQL implementation of StockDataRepository."""

    def __init__(self, db_connection: PostgreSQLConnection):
        self.db = db_connection

    async def create(self, stock_data: StockData) -> StockData:
        """Create new stock data record."""
        query = """
        INSERT INTO stock_data (id, company_id, date, open_price, close_price, high_price, low_price, volume)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        RETURNING *
        """
        result = await self.db.execute_query(
            query,
            stock_data.id,
            stock_data.company_id,
            stock_data.date,
            stock_data.open_price,
            stock_data.close_price,
            stock_data.high_price,
            stock_data.low_price,
            stock_data.volume,
        )
        return StockData(**result[0])

    async def get_by_company_and_date(
        self, company_id: UUID, date: datetime
    ) -> Optional[StockData]:
        """Get stock data by company and date."""
        query = "SELECT * FROM stock_data WHERE company_id = $1 AND date = $2"
        result = await self.db.execute_query(query, company_id, date)
        return StockData(**result[0]) if result else None

    async def get_company_history(
        self, company_id: UUID, start_date: datetime, end_date: datetime
    ) -> List[StockData]:
        """Get stock price history for a company."""
        query = """
        SELECT * FROM stock_data
        WHERE company_id = $1 AND date BETWEEN $2 AND $3
        ORDER BY date ASC
        """
        result = await self.db.execute_query(
            query, company_id, start_date, end_date
        )
        return [StockData(**row) for row in result]

    async def create_batch(
        self, stock_data_list: List[StockData]
    ) -> List[StockData]:
        """Create multiple stock data records."""
        operations = []
        for stock_data in stock_data_list:
            query = """
            INSERT INTO stock_data (id, company_id, date, open_price, close_price, high_price, low_price, volume)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """
            operations.append(
                (
                    query,
                    stock_data.id,
                    stock_data.company_id,
                    stock_data.date,
                    stock_data.open_price,
                    stock_data.close_price,
                    stock_data.high_price,
                    stock_data.low_price,
                    stock_data.volume,
                )
            )

        await self.db.execute_transaction(operations)
        return stock_data_list


# Additional repository implementations would follow similar patterns
# For brevity, I'll show one more example


class PostgreSQLDocumentEmbeddingRepository(DocumentEmbeddingRepository):
    """PostgreSQL implementation of DocumentEmbeddingRepository."""

    def __init__(self, db_connection: PostgreSQLConnection):
        self.db = db_connection

    async def create_embedding(
        self, embedding: DocumentEmbedding
    ) -> DocumentEmbedding:
        """Create a new document embedding."""
        query = """
        INSERT INTO document_embeddings (id, source_type, source_id, content_chunk, embedding, created_at, metadata)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        RETURNING *
        """
        result = await self.db.execute_query(
            query,
            embedding.id,
            embedding.source_type,
            embedding.source_id,
            embedding.content_chunk,
            embedding.embedding,
            embedding.created_at,
            embedding.metadata,
        )
        return DocumentEmbedding(**result[0])

    async def search_similar(
        self,
        query_embedding: List[float],
        limit: int = 10,
        threshold: float = 0.7,
    ) -> List[DocumentEmbedding]:
        """Search for similar documents using vector similarity."""
        query = """
        SELECT *, embedding <=> $1 AS distance
        FROM document_embeddings
        WHERE embedding <=> $1 < $2
        ORDER BY distance
        LIMIT $3
        """
        result = await self.db.execute_query(
            query, query_embedding, 1 - threshold, limit
        )
        return [DocumentEmbedding(**row) for row in result]

    async def create_batch(
        self, embeddings: List[DocumentEmbedding]
    ) -> List[DocumentEmbedding]:
        """Create multiple document embeddings."""
        operations = []
        for embedding in embeddings:
            query = """
            INSERT INTO document_embeddings (id, source_type, source_id, content_chunk, embedding, created_at, metadata)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            """
            operations.append(
                (
                    query,
                    embedding.id,
                    embedding.source_type,
                    embedding.source_id,
                    embedding.content_chunk,
                    embedding.embedding,
                    embedding.created_at,
                    embedding.metadata,
                )
            )

        await self.db.execute_transaction(operations)
        return embeddings

    async def delete_by_source(
        self, source_type: str, source_id: Optional[UUID] = None
    ) -> int:
        """Delete embeddings by source."""
        if source_id:
            query = "DELETE FROM document_embeddings WHERE source_type = $1 AND source_id = $2"
            result = await self.db.execute_query(query, source_type, source_id)
        else:
            query = "DELETE FROM document_embeddings WHERE source_type = $1"
            result = await self.db.execute_query(query, source_type)
        return len(result)


class DatabaseManager:
    """Manages database connections and repositories."""

    def __init__(self, database_url: str):
        self.connection = PostgreSQLConnection(database_url)
        self.user_repo = PostgreSQLUserRepository(self.connection)
        self.role_repo = PostgreSQLRoleRepository(self.connection)
        self.company_repo = PostgreSQLCompanyRepository(self.connection)
        self.stock_data_repo = PostgreSQLStockDataRepository(self.connection)
        self.embedding_repo = PostgreSQLDocumentEmbeddingRepository(
            self.connection
        )

    async def initialize(self) -> None:
        """Initialize database connections."""
        await self.connection.connect()

    async def close(self) -> None:
        """Close database connections."""
        await self.connection.disconnect()

    async def health_check(self) -> bool:
        """Check database health."""
        return await self.connection.health_check()
