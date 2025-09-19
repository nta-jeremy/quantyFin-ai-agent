"""LangGraph workflow orchestration for multi-agent system."""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

import structlog
from langchain_core.messages import BaseMessage
from langgraph.graph import END, START, StateGraph
from langgraph.types import Send

from .agent_state import StateManager, WorkflowState
from .agent_types import (
    AgentRole,
    AgentStatus,
    QueryType,
    SecurityLevel,
    WorkflowConfig,
    WorkflowResult,
)
from .aggregator_agent import AggregatorAgent
from .analyze_agent import AnalyzeAgent
from .base_agent import BaseAgent
from .embedding_agent import EmbeddingAgent
from .guard_agent import GuardAgent
from .predict_agent import PredictAgent
from .retriever_agent import RetrieverAgent
from .search_agent import SearchAgent

logger = structlog.get_logger(__name__)


class LangGraphWorkflowOrchestrator:
    """Main orchestrator for the multi-agent LangGraph workflow."""

    def __init__(
        self, agents: List[BaseAgent], config: Optional[WorkflowConfig] = None
    ):
        """Initialize the workflow orchestrator.

        Args:
            agents: List of agent instances
            config: Workflow configuration
        """
        self.agents = {agent.role: agent for agent in agents}
        self.config = config or WorkflowConfig()
        self.logger = logger.bind(component="LangGraphWorkflow")

        # Build the workflow graph
        self.graph = self._build_workflow_graph()

    def _build_workflow_graph(self) -> StateGraph:
        """Build the LangGraph workflow graph.

        Returns:
            Compiled StateGraph
        """
        # Create state graph
        workflow = StateGraph(WorkflowState)

        # Add all agent nodes
        for agent_role in AgentRole:
            if agent_role in self.agents:
                workflow.add_node(
                    agent_role.value, self._create_agent_node(agent_role)
                )

        # Define workflow edges
        workflow.add_edge(START, AgentRole.GUARD.value)

        # Add conditional edges for agent routing
        workflow.add_conditional_edges(
            AgentRole.GUARD.value,
            self._route_from_guard,
            {"embedding": AgentRole.EMBEDDING.value, "end": END},
        )

        workflow.add_edge(AgentRole.EMBEDDING.value, AgentRole.RETRIEVER.value)

        # Parallel execution for retrieval and search
        if self.config.enable_parallel_search:
            workflow.add_edge(AgentRole.RETRIEVER.value, "parallel_search")
            workflow.add_edge("parallel_search", AgentRole.ANALYZE.value)
            workflow.add_node("parallel_search", self._parallel_search_node)
        else:
            workflow.add_edge(
                AgentRole.RETRIEVER.value, AgentRole.SEARCH.value
            )
            workflow.add_edge(AgentRole.SEARCH.value, AgentRole.ANALYZE.value)

        workflow.add_edge(AgentRole.ANALYZE.value, AgentRole.PREDICT.value)
        workflow.add_edge(AgentRole.PREDICT.value, AgentRole.AGGREGATOR.value)
        workflow.add_edge(AgentRole.AGGREGATOR.value, END)

        return workflow.compile()

    def _create_agent_node(self, agent_role: AgentRole):
        """Create a node function for an agent.

        Args:
            agent_role: Role of the agent

        Returns:
            Node function for the agent
        """

        async def agent_node(state: WorkflowState) -> WorkflowState:
            agent = self.agents[agent_role]

            if agent.should_execute(state):
                return await agent.execute(state)
            else:
                self.logger.info(
                    "Agent execution skipped",
                    agent=agent_role.value,
                    reason="Should not execute based on current state",
                )
                return state

        return agent_node

    async def _parallel_search_node(
        self, state: WorkflowState
    ) -> WorkflowState:
        """Execute retrieval and search agents in parallel.

        Args:
            state: Current workflow state

        Returns:
            Updated state
        """
        self.logger.info("Starting parallel search execution")

        # Create tasks for parallel execution
        tasks = []

        # Add retrieval task if needed
        retriever_agent = self.agents.get(AgentRole.RETRIEVER)
        if retriever_agent and retriever_agent.should_execute(state):
            tasks.append(retriever_agent.execute(state))

        # Add search task if needed
        search_agent = self.agents.get(AgentRole.SEARCH)
        if search_agent and search_agent.should_execute(state):
            tasks.append(search_agent.execute(state))

        if not tasks:
            self.logger.info("No search tasks to execute in parallel")
            return state

        # Execute tasks in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        updated_state = state
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(
                    "Parallel search task failed",
                    task_index=i,
                    error=str(result),
                )
                updated_state = StateManager.handle_error(
                    updated_state,
                    f"Parallel search task failed: {str(result)}",
                )
            elif isinstance(result, WorkflowState):
                # Merge the results from parallel execution
                updated_state = self._merge_states(updated_state, result)

        return updated_state

    def _merge_states(
        self, state1: WorkflowState, state2: WorkflowState
    ) -> WorkflowState:
        """Merge two workflow states.

        Args:
            state1: First state
            state2: Second state to merge into first

        Returns:
            Merged state
        """
        # This is a simplified merge - in practice, you'd need more sophisticated
        # state merging logic depending on your specific use case
        merged_state = state1.copy()

        # Merge messages
        if "messages" in state2:
            merged_state["messages"] = state1["messages"] + state2["messages"]

        # Merge execution order
        if "agent_execution_order" in state2:
            merged_state["agent_execution_order"] = list(
                set(
                    state1["agent_execution_order"]
                    + state2["agent_execution_order"]
                )
            )

        # Merge results (this would need more sophisticated logic in practice)
        for key in [
            "retrieval_results",
            "search_results",
            "analysis_results",
            "prediction_results",
        ]:
            if key in state2 and state2[key]:
                if key not in merged_state or not merged_state[key]:
                    merged_state[key] = state2[key]
                else:
                    # For lists, extend them
                    if isinstance(state2[key], list):
                        merged_state[key].extend(state2[key])

        return merged_state

    def _route_from_guard(
        self, state: WorkflowState
    ) -> Literal["embedding", "end"]:
        """Route from guard agent based on validation results.

        Args:
            state: Current workflow state

        Returns:
            Next node to execute
        """
        guard_result = state.get("guard_validation")

        if not guard_result:
            self.logger.warning("No guard validation result found")
            return "end"

        if guard_result.is_safe:
            self.logger.info(
                "Query validated as safe, proceeding to embedding"
            )
            return "embedding"
        else:
            self.logger.warning(
                "Query validation failed",
                security_level=guard_result.security_level.value,
                risk_factors=guard_result.risk_factors,
            )

            # Set final response with security warning
            warning_message = (
                f"Security Alert: Your query was flagged as {guard_result.security_level.value}. "
                f"Risk factors: {', '.join(guard_result.risk_factors)}. "
                "Please modify your query and try again."
            )

            final_state = StateManager.finalize_workflow(
                state, warning_message, success=False
            )
            return "end"

    async def process_query(
        self,
        query: str,
        query_type: QueryType = QueryType.GENERAL_FINANCE,
        user_context: Optional[Dict[str, Any]] = None,
        session_metadata: Optional[Dict[str, Any]] = None,
    ) -> WorkflowResult:
        """Process a user query through the multi-agent workflow.

        Args:
            query: User query to process
            query_type: Type of query
            user_context: User context information
            session_metadata: Session metadata

        Returns:
            Workflow result with response and metadata
        """
        workflow_id = f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        self.logger.info(
            "Starting workflow execution",
            workflow_id=workflow_id,
            query=query,
            query_type=query_type.value,
        )

        try:
            # Create initial state
            initial_state = StateManager.create_initial_state(
                query=query,
                query_type=query_type,
                user_context=user_context,
                session_metadata=session_metadata,
                max_retries=self.config.max_retries,
            )

            # Execute workflow
            if self.config.enable_streaming:
                result = await self._execute_with_streaming(initial_state)
            else:
                result = await self.graph.ainvoke(initial_state)

            # Create workflow result
            workflow_result = WorkflowResult(
                query=query,
                response=result.get("final_response", "No response generated"),
                sources_used=result.get("sources_used", []),
                processing_time=result.get("processing_metadata", {}).get(
                    "total_execution_time", 0.0
                ),
                agents_executed=result.get("agent_execution_order", []),
                confidence_score=result.get("confidence_score", 0.0),
                metadata={
                    "workflow_id": workflow_id,
                    "execution_summary": StateManager.get_execution_summary(
                        result
                    ),
                    "processing_metadata": result.get(
                        "processing_metadata", {}
                    ),
                },
                success=result.get("execution_status")
                == AgentStatus.COMPLETED,
                error_message=None,
            )

            self.logger.info(
                "Workflow execution completed",
                workflow_id=workflow_id,
                success=workflow_result.success,
                processing_time=workflow_result.processing_time,
                agents_executed=[
                    agent.value for agent in workflow_result.agents_executed
                ],
            )

            return workflow_result

        except Exception as e:
            self.logger.error(
                "Workflow execution failed",
                workflow_id=workflow_id,
                error=str(e),
            )

            return WorkflowResult(
                query=query,
                response=f"I apologize, but I encountered an error while processing your request: {str(e)}",
                sources_used=[],
                processing_time=0.0,
                agents_executed=[],
                confidence_score=0.0,
                metadata={"workflow_id": workflow_id, "error": str(e)},
                success=False,
                error_message=str(e),
            )

    async def _execute_with_streaming(
        self, initial_state: WorkflowState
    ) -> WorkflowState:
        """Execute workflow with streaming support.

        Args:
            initial_state: Initial workflow state

        Returns:
            Final workflow state
        """
        final_state = None

        async for chunk in self.graph.astream(initial_state):
            # Process streaming chunks
            for node_name, node_state in chunk.items():
                self.logger.debug(
                    "Streaming chunk received",
                    node=node_name,
                    state_keys=list(node_state.keys()),
                )

                # Keep track of the latest state
                final_state = node_state

        return final_state or initial_state

    def get_workflow_status(self) -> Dict[str, Any]:
        """Get workflow status and metrics.

        Returns:
            Dictionary with workflow status and metrics
        """
        agent_metrics = {}
        for agent in self.agents.values():
            agent_metrics[agent.role.value] = agent.get_metrics_summary()

        return {
            "workflow_config": {
                "max_retries": self.config.max_retries,
                "timeout_per_agent": self.config.timeout_per_agent,
                "enable_parallel_search": self.config.enable_parallel_search,
                "cache_results": self.config.cache_results,
                "enable_streaming": self.config.enable_streaming,
            },
            "registered_agents": list(self.agents.keys()),
            "agent_metrics": agent_metrics,
            "graph_nodes": (
                list(self.graph.nodes.keys())
                if hasattr(self.graph, "nodes")
                else []
            ),
        }


def create_default_workflow(
    llm_model: Any,
    embedding_model: Any,
    config: Optional[WorkflowConfig] = None,
) -> LangGraphWorkflowOrchestrator:
    """Create a default workflow with all agents.

    Args:
        llm_model: LLM model for agents
        embedding_model: Embedding model for document processing
        config: Workflow configuration

    Returns:
        Configured workflow orchestrator
    """
    # Import agent classes here to avoid circular imports

    agents = [
        GuardAgent(llm_model, config),
        EmbeddingAgent(llm_model, embedding_model, config),
        RetrieverAgent(llm_model, config),
        SearchAgent(llm_model, config),
        AnalyzeAgent(llm_model, config),
        PredictAgent(llm_model, config),
        AggregatorAgent(llm_model, config),
    ]

    return LangGraphWorkflowOrchestrator(agents, config)
