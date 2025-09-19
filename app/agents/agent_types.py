"""Type definitions for agent communication and data structures."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, TypedDict, Union
from uuid import UUID

from pydantic import BaseModel, Field


class AgentRole(str, Enum):
    """Enumeration of agent roles in the system."""

    GUARD = "guard"
    EMBEDDING = "embedding"
    RETRIEVER = "retriever"
    SEARCH = "search"
    ANALYZE = "analyze"
    PREDICT = "predict"
    AGGREGATOR = "aggregator"


class QueryType(str, Enum):
    """Types of financial queries the system can handle."""

    STOCK_ANALYSIS = "stock_analysis"
    MARKET_RESEARCH = "market_research"
    COMPANY_FINANCIALS = "company_financials"
    NEWS_SENTIMENT = "news_sentiment"
    PORTFOLIO_ANALYSIS = "portfolio_analysis"
    GENERAL_FINANCE = "general_finance"


class AgentStatus(str, Enum):
    """Status of agent execution."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


class SecurityLevel(str, Enum):
    """Security levels for input validation."""

    SAFE = "safe"
    WARNING = "warning"
    CRITICAL = "critical"


class DocumentMetadata(BaseModel):
    """Metadata for processed documents."""

    source: str
    title: Optional[str] = None
    author: Optional[str] = None
    publish_date: Optional[datetime] = None
    document_type: str
    language: str = "en"
    content_length: int
    extraction_timestamp: datetime = Field(default_factory=datetime.now)


class VectorEmbedding(BaseModel):
    """Vector embedding with metadata."""

    id: UUID
    vector: List[float]
    metadata: DocumentMetadata
    chunk_index: int
    total_chunks: int


class SearchQuery(BaseModel):
    """Structured search query."""

    query_text: str
    query_type: QueryType
    filters: Dict[str, Any] = Field(default_factory=dict)
    limit: int = 10
    offset: int = 0
    include_context: bool = True


class SearchResult(BaseModel):
    """Single search result with metadata."""

    id: UUID
    content: str
    score: float
    metadata: DocumentMetadata
    source_type: str  # "database", "vector", "web", "api"
    relevance_score: float = Field(ge=0.0, le=1.0)


class AnalysisResult(BaseModel):
    """Result from financial analysis."""

    analysis_type: str
    insights: List[str]
    metrics: Dict[str, float]
    confidence_score: float = Field(ge=0.0, le=1.0)
    processing_time: float
    data_sources: List[str]


class PredictionResult(BaseModel):
    """Prediction from ML models."""

    prediction_type: str
    predicted_value: float
    confidence_interval: Optional[tuple[float, float]] = None
    confidence_score: float = Field(ge=0.0, le=1.0)
    model_used: str
    features_used: List[str]
    prediction_date: datetime = Field(default_factory=datetime.now)


class AgentMessage(TypedDict):
    """Message structure for agent communication."""

    sender: AgentRole
    recipient: Optional[AgentRole]
    message_type: str
    content: Dict[str, Any]
    timestamp: datetime
    message_id: UUID
    parent_message_id: Optional[UUID] = None


class GuardValidationResult(BaseModel):
    """Result from guard agent validation."""

    is_safe: bool
    security_level: SecurityLevel
    risk_factors: List[str]
    sanitized_query: str
    confidence_score: float = Field(ge=0.0, le=1.0)


class EmbeddingResult(BaseModel):
    """Result from embedding generation."""

    embeddings: List[VectorEmbedding]
    processing_time: float
    document_count: int
    total_chunks: int
    model_used: str


class RetrievalResult(BaseModel):
    """Result from data retrieval."""

    results: List[SearchResult]
    query_type: QueryType
    sources_used: List[str]
    total_results: int
    processing_time: float


class ExternalSearchResult(BaseModel):
    """Result from external API/web search."""

    results: List[SearchResult]
    api_sources: List[str]
    web_sources: List[str]
    processing_time: float
    rate_limit_info: Optional[Dict[str, Any]] = None


class AgentContext(TypedDict):
    """Context information passed between agents."""

    original_query: str
    current_query: str
    user_id: Optional[UUID]
    session_id: Optional[str]
    query_type: QueryType
    security_level: SecurityLevel
    metadata: Dict[str, Any]


class AgentState(TypedDict):
    """State maintained across agent executions."""

    messages: List[AgentMessage]
    context: AgentContext
    guard_result: Optional[GuardValidationResult]
    embedding_results: Optional[EmbeddingResult]
    retrieval_results: Optional[RetrievalResult]
    search_results: Optional[ExternalSearchResult]
    analysis_results: List[AnalysisResult]
    prediction_results: List[PredictionResult]
    current_agent: AgentRole
    execution_status: AgentStatus
    error_count: int
    start_time: Optional[datetime]
    end_time: Optional[datetime]


class WorkflowConfig(BaseModel):
    """Configuration for agent workflow."""

    max_retries: int = 3
    timeout_per_agent: float = 30.0
    enable_parallel_search: bool = True
    cache_results: bool = True
    log_level: str = "INFO"
    enable_streaming: bool = True


class AgentMetrics(BaseModel):
    """Performance metrics for agents."""

    agent_name: AgentRole
    execution_count: int
    average_execution_time: float
    success_rate: float
    error_count: int
    last_execution: Optional[datetime] = None


class WorkflowResult(BaseModel):
    """Final result from the complete workflow."""

    query: str
    response: str
    sources_used: List[str]
    processing_time: float
    agents_executed: List[AgentRole]
    confidence_score: float = Field(ge=0.0, le=1.0)
    metadata: Dict[str, Any]
    success: bool
    error_message: Optional[str] = None
