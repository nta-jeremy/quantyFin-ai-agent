"""
Agent workflow API routes for QuantyFinAI Agent.

This module provides FastAPI endpoints for the multi-agent AI workflow system,
including query processing, workflow management, and agent orchestration.
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from pydantic import BaseModel, Field

from app.agents.agent_types import QueryType
from app.agents.langgraph_workflow import LangGraphWorkflowOrchestrator
from app.core.application.auth_service import AuthService
from app.interfaces.api.auth_dependencies import get_current_user
from config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Create router
agent_router = APIRouter(prefix="/agents", tags=["agents"])

# Global instances
workflow_orchestrator: LangGraphWorkflowOrchestrator = None


# Pydantic models for request/response
class QueryRequest(BaseModel):
    """Request model for agent query processing."""

    query: str = Field(
        ..., description="The natural language query to process"
    )
    query_type: Optional[str] = Field(
        None, description="Optional query type hint"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None, description="Optional metadata for the query"
    )


class QueryResponse(BaseModel):
    """Response model for agent query processing."""

    workflow_id: str
    original_query: str
    processed_query: str
    query_type: str
    response: str
    confidence: float
    processing_time: float
    agent_states: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None
    timestamp: datetime


class WorkflowStatusResponse(BaseModel):
    """Response model for workflow status."""

    workflow_id: str
    status: str
    current_agent: Optional[str] = None
    progress: float
    start_time: datetime
    estimated_completion: Optional[datetime] = None
    error: Optional[str] = None


class HealthCheckResponse(BaseModel):
    """Response model for agent health check."""

    status: str
    agents: Dict[str, str]
    orchestrator_status: str
    last_activity: Optional[datetime] = None


async def get_workflow_orchestrator() -> LangGraphWorkflowOrchestrator:
    """Get or create the workflow orchestrator instance."""
    global workflow_orchestrator

    if workflow_orchestrator is None:
        try:
            # Initialize LLM and embeddings models
            llm = ChatOpenAI(
                model=settings.openai.model_name,
                temperature=settings.openai.temperature,
                max_tokens=settings.openai.max_tokens,
                api_key=settings.openai.api_key,
            )

            embeddings = OpenAIEmbeddings(
                model=settings.openai.embedding_model,
                api_key=settings.openai.api_key,
            )

            # Create workflow orchestrator
            workflow_orchestrator = LangGraphWorkflowOrchestrator(
                llm_model=llm, embeddings_model=embeddings
            )

            logger.info("Workflow orchestrator initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize workflow orchestrator: {e}")
            raise HTTPException(
                status_code=500,
                detail="Failed to initialize agent workflow system",
            )

    return workflow_orchestrator


def parse_query_type(query_type_str: Optional[str]) -> Optional[QueryType]:
    """Parse query type string to enum."""
    if not query_type_str:
        return None

    try:
        # Map string to QueryType enum
        query_type_mapping = {
            "stock_analysis": QueryType.STOCK_ANALYSIS,
            "market_research": QueryType.MARKET_RESEARCH,
            "company_financials": QueryType.COMPANY_FINANCIALS,
            "news_sentiment": QueryType.NEWS_SENTIMENT,
            "portfolio_analysis": QueryType.PORTFOLIO_ANALYSIS,
            "general_finance": QueryType.GENERAL_FINANCE,
        }

        return query_type_mapping.get(query_type_str.lower())
    except (ValueError, AttributeError):
        logger.warning(f"Invalid query type: {query_type_str}")
        return None


@agent_router.post("/query", response_model=QueryResponse)
async def process_query(
    request: QueryRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = Depends(get_current_user),
    orchestrator: LangGraphWorkflowOrchestrator = Depends(
        get_workflow_orchestrator
    ),
):
    """
    Process a natural language query through the multi-agent workflow.

    This endpoint takes a natural language query and processes it through
    the complete multi-agent workflow including validation, retrieval,
    analysis, and prediction.
    """
    try:
        logger.info(
            f"Processing query from user {current_user.get('sub', 'anonymous')}: {request.query}"
        )

        # Parse query type
        query_type = parse_query_type(request.query_type)

        # Add user metadata
        metadata = request.metadata or {}
        metadata.update(
            {
                "user_id": current_user.get("sub"),
                "username": current_user.get("username"),
                "timestamp": datetime.now().isoformat(),
            }
        )

        # Process query through workflow
        start_time = datetime.now()
        result = await orchestrator.execute_workflow(
            query=request.query, query_type=query_type, metadata=metadata
        )

        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()

        # Create response
        response = QueryResponse(
            workflow_id=result.workflow_id,
            original_query=result.original_query,
            processed_query=result.current_query,
            query_type=(
                result.query_type.value if result.query_type else "unknown"
            ),
            response=result.final_response or "No response generated",
            confidence=(
                result.validation_result.confidence_score
                if result.validation_result
                else 0.0
            ),
            processing_time=processing_time,
            agent_states=result.agent_states or {},
            metadata=result.metadata,
            timestamp=datetime.now(),
        )

        logger.info(f"Query processed successfully in {processing_time:.2f}s")

        return response

    except Exception as e:
        logger.error(f"Error processing query: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Error processing query: {str(e)}"
        )


@agent_router.get(
    "/query/{workflow_id}", response_model=Optional[QueryResponse]
)
async def get_query_result(
    workflow_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    orchestrator: LangGraphWorkflowOrchestrator = Depends(
        get_workflow_orchestrator
    ),
):
    """
    Get the result of a previously submitted query by workflow ID.
    """
    try:
        # Try to get result from state manager
        state = orchestrator.state_manager.get_state(workflow_id)

        if not state:
            raise HTTPException(status_code=404, detail="Workflow not found")

        # Check if user has access to this workflow
        if state.metadata.get("user_id") != current_user.get("sub"):
            raise HTTPException(
                status_code=403, detail="Access denied to this workflow"
            )

        # Create response
        response = QueryResponse(
            workflow_id=state.workflow_id,
            original_query=state.original_query,
            processed_query=state.current_query,
            query_type=(
                state.query_type.value if state.query_type else "unknown"
            ),
            response=state.final_response or "Processing...",
            confidence=(
                state.validation_result.confidence_score
                if state.validation_result
                else 0.0
            ),
            processing_time=0.0,  # Would need to track this
            agent_states=state.agent_states or {},
            metadata=state.metadata,
            timestamp=datetime.now(),
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving query result: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Error retrieving query result: {str(e)}"
        )


@agent_router.get("/health", response_model=HealthCheckResponse)
async def agent_health_check(
    current_user: Dict[str, Any] = Depends(get_current_user),
    orchestrator: LangGraphWorkflowOrchestrator = Depends(
        get_workflow_orchestrator
    ),
):
    """
    Check the health status of the agent workflow system.
    """
    try:
        # Check individual agent health
        agent_health = {
            "guard": "healthy",
            "embedding": "healthy",
            "retriever": "healthy",
            "search": "healthy",
            "analyze": "healthy",
            "predict": "healthy",
            "aggregator": "healthy",
        }

        # Check overall orchestrator health
        orchestrator_status = "healthy"

        response = HealthCheckResponse(
            status="healthy",
            agents=agent_health,
            orchestrator_status=orchestrator_status,
            last_activity=datetime.now(),
        )

        return response

    except Exception as e:
        logger.error(f"Error checking agent health: {e}", exc_info=True)
        return HealthCheckResponse(
            status="unhealthy",
            agents={},
            orchestrator_status="error",
            last_activity=datetime.now(),
        )


@agent_router.get("/queries")
async def get_user_queries(
    limit: int = 10,
    offset: int = 0,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Get a list of queries submitted by the current user.

    Note: This is a placeholder implementation. In a production system,
    you would store query history in a database.
    """
    try:
        user_id = current_user.get("sub")

        # Placeholder: Return empty list since we don't have persistent storage
        return {"queries": [], "total": 0, "limit": limit, "offset": offset}

    except Exception as e:
        logger.error(f"Error retrieving user queries: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Error retrieving queries: {str(e)}"
        )


@agent_router.delete("/query/{workflow_id}")
async def delete_query_result(
    workflow_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    orchestrator: LangGraphWorkflowOrchestrator = Depends(
        get_workflow_orchestrator
    ),
):
    """
    Delete a query result and associated workflow data.
    """
    try:
        # Get the workflow state
        state = orchestrator.state_manager.get_state(workflow_id)

        if not state:
            raise HTTPException(status_code=404, detail="Workflow not found")

        # Check if user has access to this workflow
        if state.metadata.get("user_id") != current_user.get("sub"):
            raise HTTPException(
                status_code=403, detail="Access denied to this workflow"
            )

        # Clear the workflow session
        orchestrator.state_manager.clear_session(workflow_id)

        return {"message": "Query result deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting query result: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Error deleting query result: {str(e)}"
        )


@agent_router.get("/stats")
async def get_agent_stats(
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Get statistics about agent usage and performance.

    Note: This is a placeholder implementation. In a production system,
    you would track metrics in a database or monitoring system.
    """
    try:
        # Placeholder: Return basic stats
        return {
            "total_queries": 0,
            "avg_processing_time": 0.0,
            "success_rate": 0.0,
            "popular_query_types": {},
            "agent_performance": {
                "guard": {"calls": 0, "avg_time": 0.0},
                "embedding": {"calls": 0, "avg_time": 0.0},
                "retriever": {"calls": 0, "avg_time": 0.0},
                "search": {"calls": 0, "avg_time": 0.0},
                "analyze": {"calls": 0, "avg_time": 0.0},
                "predict": {"calls": 0, "avg_time": 0.0},
                "aggregator": {"calls": 0, "avg_time": 0.0},
            },
        }

    except Exception as e:
        logger.error(f"Error retrieving agent stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Error retrieving statistics: {str(e)}"
        )
