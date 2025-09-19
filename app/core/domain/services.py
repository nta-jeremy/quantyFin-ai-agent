"""
Domain service interfaces for QuantyFinAI Agent.

This module defines the abstract interfaces (ports) for domain services
following hexagonal architecture principles.
"""

from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, Dict, List, Optional
from uuid import UUID

from .models import (
    Company,
    DocumentEmbedding,
    FinancialMetrics,
    FinancialReport,
    Prediction,
    Query,
    QueryResult,
    Role,
    SentimentAnalysis,
    StockData,
    User,
)


class UserRepository(ABC):
    """Abstract repository interface for User operations."""

    @abstractmethod
    async def create(self, user: User) -> User:
        """Create a new user."""
        pass

    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        """Get user by ID."""
        pass

    @abstractmethod
    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        pass

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        pass

    @abstractmethod
    async def update(self, user: User) -> User:
        """Update an existing user."""
        pass

    @abstractmethod
    async def delete(self, user_id: UUID) -> bool:
        """Delete a user."""
        pass

    @abstractmethod
    async def list_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        """List all users with pagination."""
        pass


class RoleRepository(ABC):
    """Abstract repository interface for Role operations."""

    @abstractmethod
    async def get_by_id(self, role_id: int) -> Optional[Role]:
        """Get role by ID."""
        pass

    @abstractmethod
    async def get_by_name(self, name: str) -> Optional[Role]:
        """Get role by name."""
        pass

    @abstractmethod
    async def list_all(self) -> List[Role]:
        """List all roles."""
        pass


class CompanyRepository(ABC):
    """Abstract repository interface for Company operations."""

    @abstractmethod
    async def create(self, company: Company) -> Company:
        """Create a new company."""
        pass

    @abstractmethod
    async def get_by_id(self, company_id: UUID) -> Optional[Company]:
        """Get company by ID."""
        pass

    @abstractmethod
    async def get_by_ticker(self, ticker_symbol: str) -> Optional[Company]:
        """Get company by ticker symbol."""
        pass

    @abstractmethod
    async def update(self, company: Company) -> Company:
        """Update an existing company."""
        pass

    @abstractmethod
    async def list_all(self, skip: int = 0, limit: int = 100) -> List[Company]:
        """List all companies with pagination."""
        pass


class StockDataRepository(ABC):
    """Abstract repository interface for StockData operations."""

    @abstractmethod
    async def create(self, stock_data: StockData) -> StockData:
        """Create new stock data record."""
        pass

    @abstractmethod
    async def get_by_company_and_date(
        self, company_id: UUID, date: datetime
    ) -> Optional[StockData]:
        """Get stock data by company and date."""
        pass

    @abstractmethod
    async def get_company_history(
        self, company_id: UUID, start_date: datetime, end_date: datetime
    ) -> List[StockData]:
        """Get stock price history for a company."""
        pass

    @abstractmethod
    async def create_batch(
        self, stock_data_list: List[StockData]
    ) -> List[StockData]:
        """Create multiple stock data records."""
        pass


class FinancialReportRepository(ABC):
    """Abstract repository interface for FinancialReport operations."""

    @abstractmethod
    async def create(self, report: FinancialReport) -> FinancialReport:
        """Create a new financial report."""
        pass

    @abstractmethod
    async def get_by_id(self, report_id: UUID) -> Optional[FinancialReport]:
        """Get financial report by ID."""
        pass

    @abstractmethod
    async def get_company_reports(
        self, company_id: UUID, report_type: Optional[str] = None
    ) -> List[FinancialReport]:
        """Get financial reports for a company."""
        pass


class DocumentEmbeddingRepository(ABC):
    """Abstract repository interface for DocumentEmbedding operations."""

    @abstractmethod
    async def create_embedding(
        self, embedding: DocumentEmbedding
    ) -> DocumentEmbedding:
        """Create a new document embedding."""
        pass

    @abstractmethod
    async def search_similar(
        self,
        query_embedding: List[float],
        limit: int = 10,
        threshold: float = 0.7,
    ) -> List[DocumentEmbedding]:
        """Search for similar documents using vector similarity."""
        pass

    @abstractmethod
    async def create_batch(
        self, embeddings: List[DocumentEmbedding]
    ) -> List[DocumentEmbedding]:
        """Create multiple document embeddings."""
        pass

    @abstractmethod
    async def delete_by_source(
        self, source_type: str, source_id: Optional[UUID] = None
    ) -> int:
        """Delete embeddings by source."""
        pass


class QueryRepository(ABC):
    """Abstract repository interface for Query operations."""

    @abstractmethod
    async def create_query(self, query: Query) -> Query:
        """Create a new query."""
        pass

    @abstractmethod
    async def get_by_id(self, query_id: UUID) -> Optional[Query]:
        """Get query by ID."""
        pass

    @abstractmethod
    async def get_user_queries(
        self, user_id: UUID, limit: int = 50
    ) -> List[Query]:
        """Get queries for a user."""
        pass

    @abstractmethod
    async def update_query(self, query_id: UUID, **kwargs) -> Optional[Query]:
        """Update a query."""
        pass


class PredictionRepository(ABC):
    """Abstract repository interface for Prediction operations."""

    @abstractmethod
    async def create_prediction(self, prediction: Prediction) -> Prediction:
        """Create a new prediction."""
        pass

    @abstractmethod
    async def get_by_id(self, prediction_id: UUID) -> Optional[Prediction]:
        """Get prediction by ID."""
        pass

    @abstractmethod
    async def get_company_predictions(
        self, company_id: UUID, prediction_type: Optional[str] = None
    ) -> List[Prediction]:
        """Get predictions for a company."""
        pass

    @abstractmethod
    async def update_actual_value(
        self, prediction_id: UUID, actual_value: float
    ) -> bool:
        """Update the actual value of a prediction."""
        pass


class FinancialMetricsRepository(ABC):
    """Abstract repository interface for FinancialMetrics operations."""

    @abstractmethod
    async def save_metrics(
        self, metrics: FinancialMetrics
    ) -> FinancialMetrics:
        """Save financial metrics."""
        pass

    @abstractmethod
    async def get_company_metrics(
        self, company_id: UUID, period_end: datetime
    ) -> Optional[FinancialMetrics]:
        """Get financial metrics for a company and period."""
        pass

    @abstractmethod
    async def get_metrics_history(
        self, company_id: UUID, start_date: datetime, end_date: datetime
    ) -> List[FinancialMetrics]:
        """Get historical financial metrics for a company."""
        pass


class SentimentAnalysisRepository(ABC):
    """Abstract repository interface for SentimentAnalysis operations."""

    @abstractmethod
    async def save_analysis(
        self, analysis: SentimentAnalysis
    ) -> SentimentAnalysis:
        """Save sentiment analysis."""
        pass

    @abstractmethod
    async def get_by_id(
        self, analysis_id: UUID
    ) -> Optional[SentimentAnalysis]:
        """Get sentiment analysis by ID."""
        pass

    @abstractmethod
    async def get_source_analysis(
        self, source_type: str, source_id: str
    ) -> List[SentimentAnalysis]:
        """Get sentiment analysis for a source."""
        pass


class DatabaseConnection(ABC):
    """Abstract interface for database connection management."""

    @abstractmethod
    async def connect(self) -> None:
        """Establish database connection."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Close database connection."""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check database health."""
        pass


class VectorDatabaseConnection(ABC):
    """Abstract interface for vector database operations."""

    @abstractmethod
    async def connect(self) -> None:
        """Establish vector database connection."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Close vector database connection."""
        pass

    @abstractmethod
    async def search(
        self,
        query_vector: List[float],
        limit: int = 10,
        threshold: float = 0.7,
    ) -> List[Dict[str, Any]]:
        """Search vector database."""
        pass

    @abstractmethod
    async def insert(self, vectors: List[Dict[str, Any]]) -> bool:
        """Insert vectors into database."""
        pass
