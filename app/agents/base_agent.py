"""Base agent class with common functionality for all agents."""

import asyncio
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Type, Union
from uuid import UUID, uuid4

import structlog
from langchain_core.documents import Document
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from .agent_state import StateManager, WorkflowState
from .agent_types import (
    AgentContext,
    AgentMetrics,
    AgentRole,
    AgentStatus,
    WorkflowConfig,
    WorkflowResult,
)

logger = structlog.get_logger(__name__)


class BaseAgent(ABC):
    """Abstract base class for all agents in the system."""

    def __init__(
        self,
        role: AgentRole,
        name: str,
        description: str,
        config: Optional[WorkflowConfig] = None,
    ):
        """Initialize the base agent.

        Args:
            role: The role of this agent in the system
            name: Human-readable name for the agent
            description: Description of the agent's purpose
            config: Configuration for the workflow
        """
        self.role = role
        self.name = name
        self.description = description
        self.config = config or WorkflowConfig()
        self.metrics = AgentMetrics(
            agent_name=role,
            execution_count=0,
            average_execution_time=0.0,
            success_rate=1.0,
            error_count=0,
        )
        self.logger = logger.bind(agent_name=name, agent_role=role.value)

    @abstractmethod
    async def process(self, state: WorkflowState) -> WorkflowState:
        """Process the agent's specific task.

        Args:
            state: Current workflow state

        Returns:
            Updated workflow state
        """
        pass

    @abstractmethod
    def validate_input(self, state: WorkflowState) -> bool:
        """Validate input state for this agent.

        Args:
            state: Current workflow state

        Returns:
            True if input is valid, False otherwise
        """
        pass

    @abstractmethod
    def get_required_predecessors(self) -> List[AgentRole]:
        """Get list of agents that must run before this agent.

        Returns:
            List of required predecessor agents
        """
        pass

    async def execute(self, state: WorkflowState) -> WorkflowState:
        """Execute the agent with error handling and metrics tracking.

        Args:
            state: Current workflow state

        Returns:
            Updated workflow state
        """
        start_time = datetime.now()
        execution_id = str(uuid4())

        self.logger.info(
            "Starting agent execution",
            execution_id=execution_id,
            workflow_id=state["workflow_id"],
        )

        try:
            # Update state to indicate agent is running
            state = StateManager.update_agent_execution(
                state, self.role, AgentStatus.RUNNING
            )

            # Add startup message
            startup_message = f"{self.name} is processing your request..."
            state = StateManager.add_agent_message(
                state, startup_message, role="assistant", agent_role=self.role
            )

            # Validate input
            if not self.validate_input(state):
                raise ValueError(f"Invalid input state for {self.name}")

            # Execute the agent's specific processing
            result_state = await self.process(state)

            # Update metrics
            execution_time = (datetime.now() - start_time).total_seconds()
            self._update_metrics(execution_time, success=True)

            # Update state to indicate completion
            result_state = StateManager.update_agent_execution(
                result_state, self.role, AgentStatus.COMPLETED
            )

            self.logger.info(
                "Agent execution completed successfully",
                execution_id=execution_id,
                execution_time=execution_time,
            )

            return result_state

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            self._update_metrics(execution_time, success=False)

            error_message = f"Error in {self.name}: {str(e)}"
            self.logger.error(
                "Agent execution failed",
                execution_id=execution_id,
                error=str(e),
                execution_time=execution_time,
            )

            # Handle error in state
            error_state = StateManager.handle_error(
                state, error_message, self.role
            )

            # Update state to indicate failure
            error_state = StateManager.update_agent_execution(
                error_state, self.role, AgentStatus.FAILED
            )

            # Check if we should retry
            if StateManager.should_retry(error_state, self.role):
                self.logger.info(
                    "Retrying agent execution", execution_id=execution_id
                )
                await asyncio.sleep(1.0)  # Brief delay before retry
                return await self.execute(state)

            return error_state

    def _update_metrics(self, execution_time: float, success: bool) -> None:
        """Update agent metrics.

        Args:
            execution_time: Time taken for execution
            success: Whether execution was successful
        """
        self.metrics.execution_count += 1
        self.metrics.last_execution = datetime.now()

        # Update average execution time
        if self.metrics.execution_count == 1:
            self.metrics.average_execution_time = execution_time
        else:
            self.metrics.average_execution_time = (
                self.metrics.average_execution_time
                * (self.metrics.execution_count - 1)
                + execution_time
            ) / self.metrics.execution_count

        # Update success rate
        if not success:
            self.metrics.error_count += 1

        self.metrics.success_rate = (
            self.metrics.execution_count - self.metrics.error_count
        ) / self.metrics.execution_count

    def should_execute(self, state: WorkflowState) -> bool:
        """Determine if this agent should execute based on current state.

        Args:
            state: Current workflow state

        Returns:
            True if agent should execute, False otherwise
        """
        # Check if agent has already been executed
        if self.role in state["agent_execution_order"]:
            return False

        # Check if required predecessors have completed
        required_predecessors = self.get_required_predecessors()
        for predecessor in required_predecessors:
            if predecessor not in state["agent_execution_order"]:
                return False

        # Check if workflow is still in a valid state
        if state["execution_status"] == AgentStatus.FAILED:
            return False

        # Check error count
        if state["error_count"] >= state["max_retries"]:
            return False

        return True

    def get_contextual_prompt(self, state: WorkflowState) -> str:
        """Generate a contextual prompt based on current state.

        Args:
            state: Current workflow state

        Returns:
            Contextual prompt string
        """
        prompt_parts = [
            f"You are {self.name}, {self.description}.",
            f"Current query: {state['current_query']}",
            f"Query type: {state['query_type'].value}",
        ]

        # Add context from previous agents
        if state["agent_execution_order"]:
            executed_agents = [
                agent.value for agent in state["agent_execution_order"]
            ]
            prompt_parts.append(
                f"Previously executed agents: {', '.join(executed_agents)}"
            )

        # Add relevant context from processing metadata
        if state["processing_metadata"]:
            relevant_metadata = {
                k: v
                for k, v in state["processing_metadata"].items()
                if not k.endswith("_execution_time") and k != "errors"
            }
            if relevant_metadata:
                prompt_parts.append(f"Additional context: {relevant_metadata}")

        return "\n".join(prompt_parts)

    async def handle_timeout(self, state: WorkflowState) -> WorkflowState:
        """Handle agent execution timeout.

        Args:
            state: Current workflow state

        Returns:
            Updated state with timeout error
        """
        error_message = f"{self.name} execution timed out after {self.config.timeout_per_agent} seconds"
        self.logger.warning("Agent execution timeout", error=error_message)

        return StateManager.handle_error(state, error_message, self.role)

    def get_relevant_messages(
        self, state: WorkflowState, limit: int = 10
    ) -> List[BaseMessage]:
        """Get relevant messages from conversation history.

        Args:
            state: Current workflow state
            limit: Maximum number of messages to return

        Returns:
            List of relevant messages
        """
        messages = state["messages"]

        # Get the most recent messages, prioritizing those with agent role metadata
        relevant_messages = []
        for message in reversed(messages):
            if len(relevant_messages) >= limit:
                break

            # Prioritize messages with agent metadata
            if (
                hasattr(message, "additional_kwargs")
                and "agent_role" in message.additional_kwargs
            ):
                relevant_messages.insert(0, message)
            else:
                relevant_messages.append(message)

        return relevant_messages[-limit:]

    def create_system_message(self, content: str) -> SystemMessage:
        """Create a system message with agent metadata.

        Args:
            content: System message content

        Returns:
            SystemMessage with agent metadata
        """
        message = SystemMessage(content=content)
        if not hasattr(message, "additional_kwargs"):
            message.additional_kwargs = {}
        message.additional_kwargs["agent_role"] = self.role.value
        return message

    def create_ai_message(self, content: str) -> AIMessage:
        """Create an AI message with agent metadata.

        Args:
            content: AI message content

        Returns:
            AIMessage with agent metadata
        """
        message = AIMessage(content=content)
        if not hasattr(message, "additional_kwargs"):
            message.additional_kwargs = {}
        message.additional_kwargs["agent_role"] = self.role.value
        return message

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of agent metrics.

        Returns:
            Dictionary with metrics summary
        """
        return {
            "agent_name": self.name,
            "role": self.role.value,
            "execution_count": self.metrics.execution_count,
            "average_execution_time": self.metrics.average_execution_time,
            "success_rate": self.metrics.success_rate,
            "error_count": self.metrics.error_count,
            "last_execution": (
                self.metrics.last_execution.isoformat()
                if self.metrics.last_execution
                else None
            ),
        }


class LLMBasedAgent(BaseAgent):
    """Base class for agents that use LLM models."""

    def __init__(
        self,
        role: AgentRole,
        name: str,
        description: str,
        llm_model: Any,  # LangChain LLM model
        config: Optional[WorkflowConfig] = None,
        system_prompt: Optional[str] = None,
    ):
        """Initialize LLM-based agent.

        Args:
            role: The role of this agent in the system
            name: Human-readable name for the agent
            description: Description of the agent's purpose
            llm_model: LangChain LLM model instance
            config: Configuration for the workflow
            system_prompt: System prompt for the LLM
        """
        super().__init__(role, name, description, config)
        self.llm_model = llm_model
        self.system_prompt = system_prompt or self._get_default_system_prompt()

    def _get_default_system_prompt(self) -> str:
        """Get default system prompt for this agent.

        Returns:
            Default system prompt string
        """
        return f"You are {self.name}, {self.description}."

    async def invoke_llm(self, messages: List[BaseMessage]) -> BaseMessage:
        """Invoke the LLM with the given messages.

        Args:
            messages: List of messages to send to LLM

        Returns:
            LLM response message
        """
        try:
            response = await asyncio.wait_for(
                self.llm_model.ainvoke(messages),
                timeout=self.config.timeout_per_agent,
            )
            return response
        except asyncio.TimeoutError:
            raise TimeoutError(
                f"LLM invocation timed out after {self.config.timeout_per_agent} seconds"
            )

    async def process_with_llm(self, state: WorkflowState, prompt: str) -> str:
        """Process with LLM using contextual prompt.

        Args:
            state: Current workflow state
            prompt: Specific prompt for this processing task

        Returns:
            LLM response text
        """
        # Build full context
        full_prompt = self.get_contextual_prompt(state)
        full_prompt += f"\n\nTask: {prompt}"

        # Create messages
        messages = [
            self.create_system_message(self.system_prompt),
            HumanMessage(content=full_prompt),
        ]

        # Add relevant conversation history
        relevant_messages = self.get_relevant_messages(state)
        if relevant_messages:
            messages.extend(relevant_messages)

        # Invoke LLM
        response = await self.invoke_llm(messages)

        if isinstance(response, AIMessage):
            return response.content
        else:
            return (
                str(response.content)
                if hasattr(response, "content")
                else str(response)
            )
