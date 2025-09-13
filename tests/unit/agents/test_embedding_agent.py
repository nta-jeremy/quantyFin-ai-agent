"""Unit tests for Embedding Agent."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.documents import Document

from app.agents.embedding_agent import EmbeddingAgent
from app.agents.agent_types import VectorEmbedding, QueryType
from app.agents.agent_state import WorkflowState


class TestEmbeddingAgent:
    """Test cases for Embedding Agent functionality."""

    @pytest.fixture
    def mock_llm(self):
        """Create a mock LLM for testing."""
        llm = MagicMock(spec=ChatOpenAI)
        llm.ainvoke = AsyncMock()
        return llm

    @pytest.fixture
    def mock_embeddings(self):
        """Create a mock embeddings model for testing."""
        embeddings = MagicMock(spec=OpenAIEmbeddings)
        embeddings.embed_documents = AsyncMock(return_value=[[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]])
        embeddings.embed_query = AsyncMock(return_value=[0.7, 0.8, 0.9])
        return embeddings

    @pytest.fixture
    def embedding_agent(self, mock_llm, mock_embeddings):
        """Create an Embedding Agent instance for testing."""
        return EmbeddingAgent(llm_model=mock_llm, embeddings_model=mock_embeddings)

    @pytest.fixture
    def sample_state(self):
        """Create a sample workflow state for testing."""
        return WorkflowState(
            workflow_id="test-workflow-123",
            original_query="Analyze Apple's financial performance",
            current_query="Analyze Apple's financial performance",
            query_type=QueryType.FINANCIAL_ANALYSIS
        )

    @pytest.mark.asyncio
    async def test_process_with_documents(self, embedding_agent, mock_embeddings, sample_state):
        """Test processing documents and generating embeddings."""
        # Add documents to state
        documents = [
            Document(
                page_content="Apple reported strong quarterly earnings with revenue growth of 15%",
                metadata={"source": "earnings_report", "date": "2024-01-01"}
            ),
            Document(
                page_content="Apple's iPhone sales exceeded expectations in the last quarter",
                metadata={"source": "sales_report", "date": "2024-01-15"}
            )
        ]
        sample_state.documents = documents

        result_state = await embedding_agent.process(sample_state)

        # Verify embeddings were generated
        assert result_state.documents is not None
        assert len(result_state.documents) == 2
        assert result_state.documents[0].embedding is not None
        assert result_state.documents[1].embedding is not None
        assert len(result_state.documents[0].embedding) == 3
        assert len(result_state.documents[1].embedding) == 3

        # Verify metadata is preserved
        assert result_state.documents[0].metadata["source"] == "earnings_report"
        assert result_state.documents[1].metadata["source"] == "sales_report"

        # Verify embeddings model was called
        mock_embeddings.embed_documents.assert_called_once()
        call_args = mock_embeddings.embed_documents.call_args[0][0]
        assert len(call_args) == 2
        assert "Apple reported strong quarterly earnings" in call_args[0]
        assert "Apple's iPhone sales exceeded" in call_args[1]

    @pytest.mark.asyncio
    async def test_process_without_documents(self, embedding_agent, sample_state):
        """Test processing when no documents are provided."""
        result_state = await embedding_agent.process(sample_state)

        # Should handle gracefully without documents
        assert result_state.documents == []
        assert result_state.workflow_id == sample_state.workflow_id

    @pytest.mark.asyncio
    async def test_chunk_long_document(self, embedding_agent, mock_embeddings, sample_state):
        """Test chunking of long documents."""
        # Create a long document
        long_text = "This is a test sentence. " * 100  # 100 sentences
        long_document = Document(
            page_content=long_text,
            metadata={"source": "long_document"}
        )
        sample_state.documents = [long_document]

        result_state = await embedding_agent.process(sample_state)

        # Verify document was chunked
        assert result_state.documents is not None
        assert len(result_state.documents) > 1  # Should be chunked

        # Verify all chunks have embeddings
        for doc in result_state.documents:
            assert doc.embedding is not None
            assert len(doc.embedding) == 3

    @pytest.mark.asyncio
    async def test_metadata_enhancement(self, embedding_agent, mock_embeddings, sample_state):
        """Test metadata enhancement with embedding info."""
        document = Document(
            page_content="Test content",
            metadata={"source": "test"}
        )
        sample_state.documents = [document]

        result_state = await embedding_agent.process(sample_state)

        # Verify metadata was enhanced
        assert "embedding_model" in result_state.documents[0].metadata
        assert "embedding_dimension" in result_state.documents[0].metadata
        assert "chunk_index" in result_state.documents[0].metadata
        assert "total_chunks" in result_state.documents[0].metadata

    @pytest.mark.asyncio
    async def test_embeddings_error_handling(self, embedding_agent, mock_embeddings, sample_state):
        """Test error handling when embeddings model fails."""
        # Mock embeddings to raise an exception
        mock_embeddings.embed_documents.side_effect = Exception("Embeddings service unavailable")

        document = Document(
            page_content="Test content",
            metadata={"source": "test"}
        )
        sample_state.documents = [document]

        result_state = await embedding_agent.process(sample_state)

        # Should handle error gracefully
        assert result_state.documents is not None
        assert len(result_state.documents) == 1
        assert "error" in result_state.documents[0].metadata
        assert result_state.documents[0].metadata["error"] == "Embeddings service unavailable"

    @pytest.mark.asyncio
    async def test_empty_document_handling(self, embedding_agent, sample_state):
        """Test handling of empty documents."""
        empty_document = Document(
            page_content="",
            metadata={"source": "empty"}
        )
        sample_state.documents = [empty_document]

        result_state = await embedding_agent.process(sample_state)

        # Should filter out empty documents
        assert result_state.documents == []

    @pytest.mark.asyncio
    async def test_duplicate_document_removal(self, embedding_agent, mock_embeddings, sample_state):
        """Test removal of duplicate documents."""
        duplicate_content = "This is duplicate content"
        documents = [
            Document(
                page_content=duplicate_content,
                metadata={"source": "source1"}
            ),
            Document(
                page_content=duplicate_content,
                metadata={"source": "source2"}
            ),
            Document(
                page_content="Unique content",
                metadata={"source": "source3"}
            )
        ]
        sample_state.documents = documents

        result_state = await embedding_agent.process(sample_state)

        # Should remove duplicates (keeping first occurrence)
        assert len(result_state.documents) == 2
        assert result_state.documents[0].page_content == duplicate_content
        assert result_state.documents[1].page_content == "Unique content"

    @pytest.mark.asyncio
    async def test_query_embedding_generation(self, embedding_agent, mock_embeddings, sample_state):
        """Test query embedding generation."""
        result_state = await embedding_agent.process(sample_state)

        # Verify query embedding was generated
        assert result_state.query_embedding is not None
        assert len(result_state.query_embedding) == 3
        assert result_state.query_embedding == [0.7, 0.8, 0.9]

        # Verify query embeddings model was called
        mock_embeddings.embed_query.assert_called_once()
        call_args = mock_embeddings.embed_query.call_args[0][0]
        assert call_args == "Analyze Apple's financial performance"

    @pytest.mark.asyncio
    async def test_state_preservation(self, embedding_agent, mock_embeddings, sample_state):
        """Test that other state fields are preserved during processing."""
        # Add additional state fields
        sample_state.metadata = {"test": "value"}
        sample_state.agent_states = {"previous_agent": "completed"}
        sample_state.messages = ["Previous message"]

        document = Document(
            page_content="Test content",
            metadata={"source": "test"}
        )
        sample_state.documents = [document]

        result_state = await embedding_agent.process(sample_state)

        # Verify other fields are preserved
        assert result_state.workflow_id == sample_state.workflow_id
        assert result_state.original_query == sample_state.original_query
        assert result_state.query_type == sample_state.query_type
        assert result_state.metadata == sample_state.metadata
        assert result_state.agent_states == sample_state.agent_states
        assert result_state.messages == sample_state.messages

    @pytest.mark.asyncio
    async def test_concurrent_document_processing(self, embedding_agent, mock_embeddings, sample_state):
        """Test concurrent processing of multiple documents."""
        # Create multiple documents
        documents = [
            Document(
                page_content=f"Document content {i}",
                metadata={"source": f"source_{i}"}
            )
            for i in range(5)
        ]
        sample_state.documents = documents

        result_state = await embedding_agent.process(sample_state)

        # Verify all documents were processed
        assert len(result_state.documents) == 5
        for i, doc in enumerate(result_state.documents):
            assert doc.embedding is not None
            assert f"Document content {i}" in doc.page_content

        # Verify embeddings were generated in batches
        mock_embeddings.embed_documents.assert_called_once()
        call_args = mock_embeddings.embed_documents.call_args[0][0]
        assert len(call_args) == 5

    @pytest.mark.asyncio
    async def test_chunking_strategy_validation(self, embedding_agent, sample_state):
        """Test validation of chunking strategy."""
        # Test with different chunk sizes
        long_text = " ".join([f"Word {i}" for i in range(1000)])
        document = Document(
            page_content=long_text,
            metadata={"source": "long_document"}
        )
        sample_state.documents = [document]

        result_state = await embedding_agent.process(sample_state)

        # Verify reasonable chunking
        assert result_state.documents is not None
        assert len(result_state.documents) > 1

        # Verify chunks are not too small
        for doc in result_state.documents:
            assert len(doc.page_content.split()) >= 50  # Minimum words per chunk

        # Verify chunks are not too large
        for doc in result_state.documents:
            assert len(doc.page_content.split()) <= 500  # Maximum words per chunk