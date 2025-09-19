"""Unit tests for agent types and state management."""

import pytest
from datetime import datetime
from typing import List, Dict, Any

from app.agents.agent_types import (
    AgentRole,
    QueryType,
    GuardValidationResult,
    VectorEmbedding,
    SearchResult,
    AnalysisResult,
    PredictionResult,
    AgentStatus,
    SecurityLevel
)
from app.agents.agent_state import WorkflowState, StateManager


class TestAgentTypes:
    """Test cases for agent type definitions."""

    def test_agent_role_enum(self):
        """Test AgentRole enum values."""
        assert AgentRole.GUARD == "guard"
        assert AgentRole.EMBEDDING == "embedding"
        assert AgentRole.RETRIEVER == "retriever"
        assert AgentRole.SEARCH == "search"
        assert AgentRole.ANALYZE == "analyze"
        assert AgentRole.PREDICT == "predict"
        assert AgentRole.AGGREGATOR == "aggregator"

    def test_query_type_enum(self):
        """Test QueryType enum values."""
        assert QueryType.STOCK_ANALYSIS == "stock_analysis"
        assert QueryType.MARKET_RESEARCH == "market_research"
        assert QueryType.COMPANY_FINANCIALS == "company_financials"
        assert QueryType.NEWS_SENTIMENT == "news_sentiment"
        assert QueryType.PORTFOLIO_ANALYSIS == "portfolio_analysis"
        assert QueryType.GENERAL_FINANCE == "general_finance"

    def test_guard_validation_result(self):
        """Test GuardValidationResult model."""
        result = GuardValidationResult(
            is_valid=True,
            confidence=0.95,
            reason="Query passes validation",
            risk_level="low",
            suggestions=None
        )

        assert result.is_valid is True
        assert result.confidence == 0.95
        assert result.reason == "Query passes validation"
        assert result.risk_level == "low"
        assert result.suggestions is None

    def test_vector_embedding(self):
        """Test VectorEmbedding model."""
        embedding = VectorEmbedding(
            text="Sample text",
            embedding=[0.1, 0.2, 0.3, 0.4],
            metadata={"source": "test", "timestamp": datetime.now()}
        )

        assert embedding.text == "Sample text"
        assert len(embedding.embedding) == 4
        assert embedding.metadata["source"] == "test"

    def test_search_result(self):
        """Test SearchResult model."""
        result = SearchResult(
            title="Test Result",
            content="Test content",
            url="https://example.com",
            source="web",
            relevance_score=0.85,
            metadata={"published_date": "2024-01-01"}
        )

        assert result.title == "Test Result"
        assert result.content == "Test content"
        assert result.url == "https://example.com"
        assert result.source == "web"
        assert result.relevance_score == 0.85

    def test_analysis_result(self):
        """Test AnalysisResult model."""
        result = AnalysisResult(
            analysis_type="financial",
            insights=["Insight 1", "Insight 2"],
            metrics={"pe_ratio": 25.5, "revenue_growth": 0.15},
            sentiment="positive",
            confidence=0.90,
            metadata={"timeframe": "1y"}
        )

        assert result.analysis_type == "financial"
        assert len(result.insights) == 2
        assert result.metrics["pe_ratio"] == 25.5
        assert result.sentiment == "positive"
        assert result.confidence == 0.90

    def test_prediction_result(self):
        """Test PredictionResult model."""
        result = PredictionResult(
            prediction_type="stock_price",
            prediction=150.0,
            confidence_interval=[140.0, 160.0],
            model_name="lstm_v1",
            features=["price", "volume", "market_cap"],
            performance_metrics={"mse": 0.01, "mae": 0.08},
            confidence=0.88,
            metadata={"prediction_date": datetime.now()}
        )

        assert result.prediction_type == "stock_price"
        assert result.prediction == 150.0
        assert len(result.confidence_interval) == 2
        assert result.model_name == "lstm_v1"
        assert result.confidence == 0.88


class TestWorkflowState:
    """Test cases for workflow state management."""

    def test_workflow_state_creation(self):
        """Test WorkflowState creation."""
        state = WorkflowState(
            workflow_id="test-workflow-123",
            original_query="What is the stock price of AAPL?",
            current_query="What is the stock price of AAPL?",
            query_type=QueryType.STOCK_ANALYSIS
        )

        assert state.workflow_id == "test-workflow-123"
        assert state.original_query == "What is the stock price of AAPL?"
        assert state.current_query == "What is the stock price of AAPL?"
        assert state.query_type == QueryType.STOCK_PREDICTION
        assert state.messages == []
        assert state.is_guard_validated is False
        assert state.validation_result is None

    def test_state_manager_create_state(self):
        """Test StateManager state creation."""
        manager = StateManager()
        state = manager.create_state(
            query="What is the stock price of AAPL?",
            query_type=QueryType.STOCK_ANALYSIS
        )

        assert state.workflow_id is not None
        assert len(state.workflow_id) > 0
        assert state.original_query == "What is the stock price of AAPL?"
        assert state.current_query == "What is the stock price of AAPL?"
        assert state.query_type == QueryType.STOCK_PREDICTION

    def test_state_manager_update_state(self):
        """Test StateManager state updates."""
        manager = StateManager()
        state = manager.create_state(
            query="Test query",
            query_type=QueryType.GENERAL_KNOWLEDGE
        )

        validation_result = GuardValidationResult(
            is_valid=True,
            confidence=0.95,
            reason="Valid query",
            risk_level="low"
        )

        updated_state = manager.update_state(
            state,
            validation_result=validation_result,
            is_guard_validated=True
        )

        assert updated_state.is_guard_validated is True
        assert updated_state.validation_result == validation_result
        assert updated_state.workflow_id == state.workflow_id

    def test_state_manager_clear_session(self):
        """Test StateManager session clearing."""
        manager = StateManager()
        state = manager.create_state("Test query", QueryType.GENERAL_FINANCE)

        manager.clear_session(state.workflow_id)

        with pytest.raises(KeyError):
            manager.get_state(state.workflow_id)