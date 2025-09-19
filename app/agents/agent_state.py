"""State management models and utilities for agent workflows."""

from datetime import datetime
from enum import Enum
from typing import Annotated, Any, Dict, List, Optional, TypedDict
from uuid import UUID, uuid4

from langchain_core.documents import Document
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
)
from pydantic import BaseModel, Field

from .agent_types import (
    AgentContext,
    AgentMessage,
    AgentRole,
    AgentStatus,
    AnalysisResult,
    EmbeddingResult,
    ExternalSearchResult,
    GuardValidationResult,
    PredictionResult,
    QueryType,
    RetrievalResult,
    SecurityLevel,
)


class WorkflowState(TypedDict):
    """Main state object for LangGraph workflow."""

    # Core workflow information
    workflow_id: str
    original_query: str
    current_query: str
    query_type: QueryType

    # Message history
    messages: Annotated[List[BaseMessage], lambda x, y: x + y]

    # Agent execution tracking
    current_agent: Optional[AgentRole]
    agent_execution_order: List[AgentRole]
    execution_status: AgentStatus

    # Security and validation
    security_level: SecurityLevel
    guard_validation: Optional[GuardValidationResult]
    error_count: int
    max_retries: int

    # Data processing results
    documents: List[Document]
    embeddings: Optional[EmbeddingResult]
    retrieval_results: Optional[RetrievalResult]
    search_results: Optional[ExternalSearchResult]
    analysis_results: List[AnalysisResult]
    prediction_results: List[PredictionResult]

    # Context and metadata
    user_context: Dict[str, Any]
    session_metadata: Dict[str, Any]
    processing_metadata: Dict[str, Any]

    # Timing and performance
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    current_agent_start_time: Optional[datetime]

    # Final results
    final_response: Optional[str]
    confidence_score: float
    sources_used: List[str]


class AgentExecutionState(TypedDict):
    """State for individual agent execution."""

    agent_id: str
    agent_role: AgentRole
    input_data: Dict[str, Any]
    output_data: Dict[str, Any]
    execution_time: float
    status: AgentStatus
    error_message: Optional[str]
    retry_count: int


class StateManager:
    """Utility class for managing workflow state."""

    @staticmethod
    def create_initial_state(
        query: str,
        query_type: QueryType = QueryType.GENERAL_FINANCE,
        user_context: Optional[Dict[str, Any]] = None,
        session_metadata: Optional[Dict[str, Any]] = None,
        max_retries: int = 3,
    ) -> WorkflowState:
        """Create initial workflow state."""

        workflow_id = str(uuid4())
        current_time = datetime.now()

        return WorkflowState(
            workflow_id=workflow_id,
            original_query=query,
            current_query=query,
            query_type=query_type,
            messages=[HumanMessage(content=query)],
            current_agent=None,
            agent_execution_order=[],
            execution_status=AgentStatus.PENDING,
            security_level=SecurityLevel.SAFE,
            guard_validation=None,
            error_count=0,
            max_retries=max_retries,
            documents=[],
            embeddings=None,
            retrieval_results=None,
            search_results=None,
            analysis_results=[],
            prediction_results=[],
            user_context=user_context or {},
            session_metadata=session_metadata or {},
            processing_metadata={},
            start_time=current_time,
            end_time=None,
            current_agent_start_time=None,
            final_response=None,
            confidence_score=0.0,
            sources_used=[],
        )

    @staticmethod
    def add_agent_message(
        state: WorkflowState,
        content: str,
        role: str = "assistant",
        agent_role: Optional[AgentRole] = None,
    ) -> WorkflowState:
        """Add a message to the conversation history."""

        if role == "assistant":
            message = AIMessage(content=content)
        elif role == "user":
            message = HumanMessage(content=content)
        elif role == "system":
            message = SystemMessage(content=content)
        else:
            message = AIMessage(content=content)

        # Add agent role metadata if provided
        if agent_role:
            if not hasattr(message, "additional_kwargs"):
                message.additional_kwargs = {}
            message.additional_kwargs["agent_role"] = agent_role.value

        state["messages"] = state["messages"] + [message]
        return state

    @staticmethod
    def update_agent_execution(
        state: WorkflowState, agent_role: AgentRole, status: AgentStatus
    ) -> WorkflowState:
        """Update agent execution tracking."""

        current_time = datetime.now()

        if agent_role not in state["agent_execution_order"]:
            state["agent_execution_order"].append(agent_role)

        state["current_agent"] = agent_role
        state["execution_status"] = status

        if status == AgentStatus.RUNNING:
            state["current_agent_start_time"] = current_time
        elif status in [AgentStatus.COMPLETED, AgentStatus.FAILED]:
            if state["current_agent_start_time"]:
                execution_time = (
                    current_time - state["current_agent_start_time"]
                ).total_seconds()

                # Track execution time in processing metadata
                agent_key = f"{agent_role.value}_execution_time"
                if agent_key not in state["processing_metadata"]:
                    state["processing_metadata"][agent_key] = []
                state["processing_metadata"][agent_key].append(execution_time)

            state["current_agent_start_time"] = None

        return state

    @staticmethod
    def handle_error(
        state: WorkflowState,
        error_message: str,
        agent_role: Optional[AgentRole] = None,
    ) -> WorkflowState:
        """Handle errors in agent execution."""

        state["error_count"] += 1

        # Add error to processing metadata
        if "errors" not in state["processing_metadata"]:
            state["processing_metadata"]["errors"] = []

        error_info = {
            "timestamp": datetime.now(),
            "message": error_message,
            "agent": agent_role.value if agent_role else "unknown",
            "error_count": state["error_count"],
        }

        state["processing_metadata"]["errors"].append(error_info)

        # Add error message to conversation
        error_content = f"Error encountered: {error_message}"
        state = StateManager.add_agent_message(
            state, error_content, role="system", agent_role=agent_role
        )

        return state

    @staticmethod
    def should_retry(state: WorkflowState, agent_role: AgentRole) -> bool:
        """Determine if agent execution should be retried."""

        agent_error_key = f"{agent_role.value}_error_count"
        current_agent_errors = state["processing_metadata"].get(
            agent_error_key, 0
        )

        return (
            state["error_count"] < state["max_retries"]
            and current_agent_errors < state["max_retries"]
        )

    @staticmethod
    def calculate_confidence_score(state: WorkflowState) -> float:
        """Calculate overall confidence score based on agent results."""

        scores = []

        # Add guard validation confidence
        if state["guard_validation"]:
            scores.append(state["guard_validation"].confidence_score)

        # Add analysis result confidence scores
        for analysis in state["analysis_results"]:
            scores.append(analysis.confidence_score)

        # Add prediction result confidence scores
        for prediction in state["prediction_results"]:
            scores.append(prediction.confidence_score)

        # Add retrieval result confidence scores
        if state["retrieval_results"]:
            retrieval_scores = [
                result.relevance_score
                for result in state["retrieval_results"].results
            ]
            if retrieval_scores:
                scores.append(sum(retrieval_scores) / len(retrieval_scores))

        # Calculate weighted average
        if scores:
            # Weight more recent results higher
            weights = [i + 1 for i in range(len(scores))]
            weighted_sum = sum(
                score * weight for score, weight in zip(scores, weights)
            )
            total_weight = sum(weights)
            return weighted_sum / total_weight

        return 0.5  # Default confidence if no scores available

    @staticmethod
    def finalize_workflow(
        state: WorkflowState, final_response: str, success: bool = True
    ) -> WorkflowState:
        """Finalize workflow execution."""

        current_time = datetime.now()

        state["end_time"] = current_time
        state["final_response"] = final_response
        state["execution_status"] = (
            AgentStatus.COMPLETED if success else AgentStatus.FAILED
        )
        state["confidence_score"] = StateManager.calculate_confidence_score(
            state
        )

        # Calculate total processing time
        if state["start_time"]:
            total_time = (current_time - state["start_time"]).total_seconds()
            state["processing_metadata"]["total_execution_time"] = total_time

        # Add final response to messages
        state = StateManager.add_agent_message(
            state,
            final_response,
            role="assistant",
            agent_role=AgentRole.AGGREGATOR,
        )

        return state

    @staticmethod
    def get_execution_summary(state: WorkflowState) -> Dict[str, Any]:
        """Generate execution summary for logging and monitoring."""

        summary = {
            "workflow_id": state["workflow_id"],
            "original_query": state["original_query"],
            "query_type": state["query_type"].value,
            "execution_status": state["execution_status"].value,
            "agents_executed": [
                agent.value for agent in state["agent_execution_order"]
            ],
            "error_count": state["error_count"],
            "confidence_score": state["confidence_score"],
            "sources_used": len(state["sources_used"]),
            "total_messages": len(state["messages"]),
        }

        if state["start_time"] and state["end_time"]:
            summary["execution_time"] = (
                state["end_time"] - state["start_time"]
            ).total_seconds()

        if state["processing_metadata"]:
            summary["processing_metadata"] = state["processing_metadata"]

        return summary
