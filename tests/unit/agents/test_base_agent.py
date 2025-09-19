"""Unit tests for Base Agent and agent utilities."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from langchain_openai import ChatOpenAI

from app.agents.base_agent import BaseAgent, LLMBasedAgent
from app.agents.agent_types import AgentRole, WorkflowConfig
from app.agents.agent_state import WorkflowState, StateManager


class MockAgent(BaseAgent):
    """Mock agent for testing BaseAgent functionality."""

    def __init__(self, role: AgentRole, name: str, description: str):
        super().__init__(role, name, description)

    async def process(self, state: WorkflowState) -> WorkflowState:
        """Mock process method."""
        state.metadata = {"processed_by": self.name}
        return state


class TestBaseAgent:
    """Test cases for Base Agent functionality."""

    @pytest.fixture
    def mock_agent(self):
        """Create a mock agent instance."""
        return MockAgent(
            role=AgentRole.GUARD,
            name="Test Agent",
            description="Test agent for unit testing"
        )

    @pytest.fixture
    def sample_state(self):
        """Create a sample workflow state."""
        return WorkflowState(
            workflow_id="test-workflow-123",
            original_query="Test query",
            current_query="Test query",
            query_type="test"
        )

    def test_agent_initialization(self, mock_agent):
        """Test agent initialization."""
        assert mock_agent.role == AgentRole.GUARD
        assert mock_agent.name == "Test Agent"
        assert mock_agent.description == "Test agent for unit testing"

    @pytest.mark.asyncio
    async def test_agent_execute_success(self, mock_agent, sample_state):
        """Test successful agent execution."""
        result = await mock_agent.execute(sample_state)

        # Verify state is updated
        assert result.metadata == {"processed_by": "Test Agent"}
        assert result.workflow_id == sample_state.workflow_id
        assert result.original_query == sample_state.original_query

    @pytest.mark.asyncio
    async def test_agent_execute_with_error(self, mock_agent, sample_state):
        """Test agent execution with error."""
        # Mock process to raise an exception
        with patch.object(mock_agent, 'process', side_effect=Exception("Test error")):
            with pytest.raises(Exception) as exc_info:
                await mock_agent.execute(sample_state)

            assert "Test error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_agent_state_preservation(self, mock_agent, sample_state):
        """Test that agent preserves existing state."""
        sample_state.metadata = {"existing": "data"}
        sample_state.agent_states = {"previous": "completed"}

        result = await mock_agent.execute(sample_state)

        # Verify existing state is preserved
        assert "existing" in result.metadata
        assert result.metadata["existing"] == "data"
        assert "processed_by" in result.metadata
        assert result.agent_states == {"previous": "completed"}

    @pytest.mark.asyncio
    async def test_agent_workflow_id_preservation(self, mock_agent, sample_state):
        """Test that workflow ID is preserved."""
        result = await mock_agent.execute(sample_state)

        assert result.workflow_id == sample_state.workflow_id


class TestLLMBasedAgent:
    """Test cases for LLM-based Agent functionality."""

    @pytest.fixture
    def mock_llm(self):
        """Create a mock LLM for testing."""
        llm = MagicMock(spec=ChatOpenAI)
        llm.ainvoke = AsyncMock()
        return llm

    @pytest.fixture
    def llm_agent(self, mock_llm):
        """Create an LLM-based agent instance."""
        return LLMBasedAgent(
            role=AgentRole.ANALYZE,
            name="Test LLM Agent",
            description="Test LLM agent",
            llm_model=mock_llm,
            system_prompt="You are a helpful assistant."
        )

    @pytest.fixture
    def sample_state(self):
        """Create a sample workflow state."""
        return WorkflowState(
            workflow_id="test-workflow-456",
            original_query="Analyze this data",
            current_query="Analyze this data",
            query_type="analysis"
        )

    def test_llm_agent_initialization(self, llm_agent, mock_llm):
        """Test LLM-based agent initialization."""
        assert llm_agent.role == AgentRole.ANALYZE
        assert llm_agent.name == "Test LLM Agent"
        assert llm_agent.llm_model == mock_llm
        assert llm_agent.system_prompt == "You are a helpful assistant."
        assert llm_agent.config is not None

    @pytest.mark.asyncio
    async def test_llm_agent_process_with_system_prompt(self, llm_agent, mock_llm, sample_state):
        """Test LLM agent processing with system prompt."""
        # Mock LLM response
        mock_llm.ainvoke.return_value = MagicMock(content="Analysis complete")

        # Mock the abstract process method
        with patch.object(llm_agent, '_process_with_llm', return_value={"result": "test"}) as mock_process:
            result = await llm_agent.process(sample_state)

            # Verify process was called
            mock_process.assert_called_once_with(sample_state)

    @pytest.mark.asyncio
    async def test_llm_agent_configuration(self, llm_agent):
        """Test LLM agent configuration."""
        # Test with custom configuration
        custom_config = WorkflowConfig(
            max_tokens=2000,
            temperature=0.8,
            timeout=60
        )

        agent_with_config = LLMBasedAgent(
            role=AgentRole.PREDICT,
            name="Configured Agent",
            description="Agent with custom config",
            llm_model=mock_llm,
            config=custom_config,
            system_prompt="Custom prompt"
        )

        assert agent_with_config.config.max_tokens == 2000
        assert agent_with_config.config.temperature == 0.8
        assert agent_with_config.config.timeout == 60

    @pytest.mark.asyncio
    async def test_llm_agent_error_handling(self, llm_agent, mock_llm, sample_state):
        """Test LLM agent error handling."""
        # Mock LLM to raise an exception
        mock_llm.ainvoke.side_effect = Exception("LLM error")

        with patch.object(llm_agent, '_process_with_llm', side_effect=Exception("Processing error")):
            with pytest.raises(Exception) as exc_info:
                await llm_agent.process(sample_state)

            assert "Processing error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_llm_agent_state_update(self, llm_agent, mock_llm, sample_state):
        """Test LLM agent state updates."""
        # Add initial state
        sample_state.agent_states = {"previous_agent": "completed"}

        with patch.object(llm_agent, '_process_with_llm', return_value={"analysis": "completed"}) as mock_process:
            result = await llm_agent.process(sample_state)

            # Verify agent state is updated
            assert "analyze" in result.agent_states
            assert result.agent_states["analyze"] == "completed"
            # Verify previous states are preserved
            assert "previous_agent" in result.agent_states

    @pytest.mark.asyncio
    async def test_llm_agent_message_handling(self, llm_agent, mock_llm, sample_state):
        """Test LLM agent message handling."""
        # Add messages to state
        from langchain_core.messages import HumanMessage
        sample_state.messages = [HumanMessage(content="Previous message")]

        with patch.object(llm_agent, '_process_with_llm', return_value={"response": "test"}) as mock_process:
            result = await llm_agent.process(sample_state)

            # Verify messages are preserved
            assert len(result.messages) == 1
            assert result.messages[0].content == "Previous message"

    @pytest.mark.asyncio
    async def test_llm_agent_metadata_handling(self, llm_agent, mock_llm, sample_state):
        """Test LLM agent metadata handling."""
        # Add metadata to state
        sample_state.metadata = {"user_id": "test_user", "session_id": "test_session"}

        with patch.object(llm_agent, '_process_with_llm', return_value={"response": "test"}) as mock_process:
            result = await llm_agent.process(sample_state)

            # Verify metadata is preserved
            assert result.metadata == {"user_id": "test_user", "session_id": "test_session"}

    @pytest.mark.asyncio
    async def test_llm_agent_concurrent_execution(self, llm_agent, mock_llm):
        """Test concurrent execution of LLM agent."""
        states = [
            WorkflowState(
                workflow_id=f"workflow-{i}",
                original_query=f"Query {i}",
                current_query=f"Query {i}",
                query_type="test"
            )
            for i in range(3)
        ]

        with patch.object(llm_agent, '_process_with_llm', return_value={"response": f"test response"}) as mock_process:
            # Execute concurrently
            import asyncio
            results = await asyncio.gather(*[llm_agent.process(state) for state in states])

            # Verify all states were processed
            assert len(results) == 3
            for i, result in enumerate(results):
                assert result.workflow_id == f"workflow-{i}"

            # Verify process was called for each state
            assert mock_process.call_count == 3

    def test_agent_role_string_representation(self):
        """Test agent role string representation."""
        assert str(AgentRole.GUARD) == "guard"
        assert str(AgentRole.EMBEDDING) == "embedding"
        assert str(AgentRole.RETRIEVER) == "retriever"
        assert str(AgentRole.SEARCH) == "search"
        assert str(AgentRole.ANALYZE) == "analyze"
        assert str(AgentRole.PREDICT) == "predict"
        assert str(AgentRole.AGGREGATOR) == "aggregator"

    def test_workflow_config_creation(self):
        """Test workflow configuration creation."""
        config = WorkflowConfig()
        assert config.max_tokens == 4000
        assert config.temperature == 0.7
        assert config.timeout == 30

        custom_config = WorkflowConfig(
            max_tokens=2000,
            temperature=0.8,
            timeout=60
        )
        assert custom_config.max_tokens == 2000
        assert custom_config.temperature == 0.8
        assert custom_config.timeout == 60