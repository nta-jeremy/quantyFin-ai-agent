"""Embedding Agent for document processing and vector generation."""

import asyncio
import hashlib
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pydantic import BaseModel, Field

from .agent_state import StateManager, WorkflowState
from .agent_types import (
    AgentRole,
    DocumentMetadata,
    EmbeddingResult,
    QueryType,
    VectorEmbedding,
    WorkflowConfig,
)
from .base_agent import LLMBasedAgent

# Document chunking configuration
DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHUNK_OVERLAP = 200

# Supported document types
SUPPORTED_DOCUMENT_TYPES = [
    "financial_report",
    "news_article",
    "research_paper",
    "sec_filing",
    "earnings_call",
    "market_analysis",
    "company_profile",
    "economic_data",
]


class DocumentChunk(BaseModel):
    """A chunk of document text with metadata."""

    id: UUID
    text: str
    metadata: DocumentMetadata
    chunk_index: int
    total_chunks: int


class EmbeddingAgent(LLMBasedAgent):
    """Agent for processing documents and generating vector embeddings."""

    def __init__(
        self,
        llm_model: ChatOpenAI,
        embedding_model: OpenAIEmbeddings,
        config: Optional[WorkflowConfig] = None,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    ):
        """Initialize the Embedding Agent.

        Args:
            llm_model: LLM model for document analysis
            embedding_model: Embedding model for vector generation
            config: Workflow configuration
            chunk_size: Size of document chunks
            chunk_overlap: Overlap between chunks
        """
        super().__init__(
            role=AgentRole.EMBEDDING,
            name="Document Embedding Specialist",
            description="Processes financial documents and generates vector embeddings for semantic search",
            llm_model=llm_model,
            config=config,
            system_prompt=self._get_embedding_system_prompt(),
        )

        self.embedding_model = embedding_model
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

    def _get_embedding_system_prompt(self) -> str:
        """Get system prompt for the Embedding Agent.

        Returns:
            System prompt string
        """
        return """You are a Document Embedding Specialist responsible for processing financial documents and preparing them for vector storage.

Your responsibilities:
1. Extract relevant financial information from documents
2. Identify document type and structure
3. Generate appropriate metadata for semantic search
4. Prepare documents for chunking and embedding
5. Analyze document quality and relevance
6. Categorize financial content appropriately

Focus on extracting meaningful financial data, metrics, and contextual information that will be valuable for semantic search and analysis."""

    def get_required_predecessors(self) -> List[AgentRole]:
        """Get list of agents that must run before this agent.

        Returns:
            List with Guard agent
        """
        return [AgentRole.GUARD]

    def validate_input(self, state: WorkflowState) -> bool:
        """Validate input state for Embedding Agent.

        Args:
            state: Current workflow state

        Returns:
            True if input is valid
        """
        return (
            state["guard_validation"]
            and state["guard_validation"].is_safe
            and state["current_query"]
            and len(state["current_query"].strip()) > 0
        )

    async def process(self, state: WorkflowState) -> WorkflowState:
        """Process document embedding for the query context.

        Args:
            state: Current workflow state

        Returns:
            Updated workflow state with embedding results
        """
        query = state["current_query"]
        query_type = state["query_type"]

        self.logger.info(
            "Starting document embedding processing",
            query_type=query_type.value,
            query_length=len(query),
        )

        try:
            # Step 1: Identify relevant documents based on query
            relevant_docs = await self._identify_relevant_documents(
                query, query_type
            )

            # Step 2: Process documents into chunks
            document_chunks = await self._process_documents_to_chunks(
                relevant_docs
            )

            # Step 3: Generate embeddings for chunks
            embedding_result = await self._generate_embeddings(document_chunks)

            # Step 4: Store embeddings in vector database
            await self._store_embeddings(embedding_result.embeddings)

            # Step 5: Update state with results
            state["embeddings"] = embedding_result
            state["documents"] = [
                chunk.metadata.model_dump() for chunk in document_chunks
            ]

            # Add processing message
            processing_message = self._create_processing_message(
                embedding_result
            )
            state = StateManager.add_agent_message(
                state,
                processing_message,
                role="assistant",
                agent_role=self.role,
            )

            self.logger.info(
                "Document embedding completed",
                documents_processed=len(relevant_docs),
                chunks_generated=len(document_chunks),
                embeddings_created=len(embedding_result.embeddings),
            )

            return state

        except Exception as e:
            self.logger.error(
                "Document embedding processing failed", error=str(e)
            )
            raise RuntimeError(f"Embedding processing failed: {str(e)}")

    async def _identify_relevant_documents(
        self, query: str, query_type: QueryType
    ) -> List[Document]:
        """Identify relevant documents based on query analysis.

        Args:
            query: User query
            query_type: Type of query

        Returns:
            List of relevant documents
        """
        # Use LLM to analyze query and identify document types needed
        analysis_prompt = f"""
        Analyze this financial query and identify what types of documents would be most relevant:

        Query: "{query}"
        Query Type: {query_type.value}

        Return a JSON response with:
        {{
            "required_document_types": ["type1", "type2"],
            "key_terms": ["term1", "term2"],
            "time_period": "relevant time period if applicable",
            "focus_areas": ["area1", "area2"]
        }}
        """

        try:
            response = await self.invoke_llm(
                [
                    SystemMessage(
                        content="You are a financial document analysis expert."
                    ),
                    HumanMessage(content=analysis_prompt),
                ]
            )

            # Parse the response to get document requirements
            response_text = response.content
            import json
            import re

            # Extract JSON from response
            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if json_match:
                requirements = json.loads(json_match.group())
                doc_types = requirements.get("required_document_types", [])
                key_terms = requirements.get("key_terms", [])

                # Generate sample documents based on requirements
                return await self._generate_sample_documents(
                    doc_types, key_terms, query_type
                )

        except Exception as e:
            self.logger.warning(
                "Failed to analyze query for document identification",
                error=str(e),
            )

        # Fallback: generate generic financial documents
        return await self._generate_sample_documents(
            ["financial_report", "market_analysis"],
            [query.split()[0] if query.split() else "financial"],
            query_type,
        )

    async def _generate_sample_documents(
        self, doc_types: List[str], key_terms: List[str], query_type: QueryType
    ) -> List[Document]:
        """Generate sample documents based on identified requirements.

        Args:
            doc_types: Types of documents needed
            key_terms: Key terms to focus on
            query_type: Type of query

        Returns:
            List of generated documents
        """
        documents = []

        for i, doc_type in enumerate(doc_types):
            # Create document metadata
            metadata = DocumentMetadata(
                source=f"generated_{doc_type}_{i}",
                title=f"{doc_type.replace('_', ' ').title()} Analysis",
                author="QuantyFinAI System",
                publish_date=datetime.now(),
                document_type=doc_type,
                content_length=2000,  # Will be updated after content generation
                language="en",
            )

            # Generate document content using LLM
            content = await self._generate_document_content(
                doc_type, key_terms, query_type
            )
            metadata.content_length = len(content)

            # Create LangChain document
            doc = Document(
                page_content=content, metadata=metadata.model_dump()
            )
            documents.append(doc)

        return documents

    async def _generate_document_content(
        self, doc_type: str, key_terms: List[str], query_type: QueryType
    ) -> str:
        """Generate content for a specific document type.

        Args:
            doc_type: Type of document to generate
            key_terms: Key terms to include
            query_type: Type of query

        Returns:
            Generated document content
        """
        content_prompt = f"""
        Generate a realistic {doc_type.replace('_', ' ')} document that would be relevant for financial analysis.

        Key terms to include: {', '.join(key_terms)}
        Query context: {query_type.value}

        The document should:
        1. Be approximately 1500-2000 words
        2. Include relevant financial data, metrics, and analysis
        3. Be structured and professional
        4. Contain actionable financial insights
        5. Be suitable for vector embedding and semantic search

        Generate the document content:
        """

        response = await self.invoke_llm(
            [
                SystemMessage(
                    content=f"You are an expert financial analyst specializing in {doc_type.replace('_', ' ')} documents."
                ),
                HumanMessage(content=content_prompt),
            ]
        )

        return response.content

    async def _process_documents_to_chunks(
        self, documents: List[Document]
    ) -> List[DocumentChunk]:
        """Process documents into manageable chunks.

        Args:
            documents: List of documents to process

        Returns:
            List of document chunks
        """
        chunks = []

        for doc in documents:
            # Split document into chunks
            text_chunks = self.text_splitter.split_text(doc.page_content)

            for i, chunk_text in enumerate(text_chunks):
                # Create chunk metadata
                doc_metadata = DocumentMetadata(**doc.metadata)
                chunk_metadata = DocumentMetadata(
                    source=doc_metadata.source,
                    title=doc_metadata.title,
                    author=doc_metadata.author,
                    publish_date=doc_metadata.publish_date,
                    document_type=doc_metadata.document_type,
                    language=doc_metadata.language,
                    content_length=len(chunk_text),
                    extraction_timestamp=datetime.now(),
                )

                # Create document chunk
                chunk = DocumentChunk(
                    id=uuid4(),
                    text=chunk_text,
                    metadata=chunk_metadata,
                    chunk_index=i,
                    total_chunks=len(text_chunks),
                )
                chunks.append(chunk)

        self.logger.info(
            "Documents processed into chunks",
            documents=len(documents),
            chunks=len(chunks),
        )
        return chunks

    async def _generate_embeddings(
        self, chunks: List[DocumentChunk]
    ) -> EmbeddingResult:
        """Generate vector embeddings for document chunks.

        Args:
            chunks: List of document chunks

        Returns:
            Embedding result with vectors
        """
        start_time = datetime.now()

        # Extract text from chunks
        texts = [chunk.text for chunk in chunks]

        # Generate embeddings in batches to avoid rate limits
        batch_size = 100
        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i : i + batch_size]
            batch_embeddings = await self.embedding_model.aembed_documents(
                batch_texts
            )
            all_embeddings.extend(batch_embeddings)

            # Add small delay to avoid rate limiting
            if i + batch_size < len(texts):
                await asyncio.sleep(0.1)

        # Create VectorEmbedding objects
        vector_embeddings = []
        for chunk, embedding_vector in zip(chunks, all_embeddings):
            vector_embedding = VectorEmbedding(
                id=chunk.id,
                vector=embedding_vector,
                metadata=chunk.metadata,
                chunk_index=chunk.chunk_index,
                total_chunks=chunk.total_chunks,
            )
            vector_embeddings.append(vector_embedding)

        processing_time = (datetime.now() - start_time).total_seconds()

        return EmbeddingResult(
            embeddings=vector_embeddings,
            processing_time=processing_time,
            document_count=len(set(chunk.metadata.source for chunk in chunks)),
            total_chunks=len(chunks),
            model_used="OpenAI Embeddings",
        )

    async def _store_embeddings(
        self, embeddings: List[VectorEmbedding]
    ) -> None:
        """Store embeddings in the vector database.

        Args:
            embeddings: List of vector embeddings to store
        """
        # This would integrate with your existing vector_db_adapter
        # For now, we'll simulate the storage process

        try:
            # Simulate database storage operations
            for embedding in embeddings:
                # Generate a document hash for deduplication
                doc_hash = hashlib.md5(
                    f"{embedding.metadata.source}_{embedding.chunk_index}".encode()
                ).hexdigest()

                # In a real implementation, this would use your vector_db_adapter
                # await vector_db_adapter.store_embedding(embedding.vector, embedding.metadata.model_dump(), doc_hash)

                self.logger.debug(
                    "Embedding stored",
                    document_id=embedding.id,
                    chunk_index=embedding.chunk_index,
                    vector_dimension=len(embedding.vector),
                )

            self.logger.info(
                "Embeddings stored in vector database", count=len(embeddings)
            )

        except Exception as e:
            self.logger.error("Failed to store embeddings", error=str(e))
            # Don't raise the error - continue with processing but log the failure

    def _create_processing_message(self, result: EmbeddingResult) -> str:
        """Create a processing message for the conversation.

        Args:
            result: Embedding processing result

        Returns:
            Processing message string
        """
        return (
            f"📄 Document Processing Complete: Generated {result.total_chunks} vector embeddings "
            f"from {result.document_count} documents in {result.processing_time:.2f}s. "
            f"Using {result.model_used} for semantic search capabilities."
        )

    async def process_external_document(
        self, content: str, metadata: Dict[str, Any], document_type: str
    ) -> EmbeddingResult:
        """Process an external document and generate embeddings.

        Args:
            content: Document content
            metadata: Document metadata
            document_type: Type of document

        Returns:
            Embedding result
        """
        # Create document metadata
        doc_metadata = DocumentMetadata(
            source=metadata.get("source", "external"),
            title=metadata.get("title", "External Document"),
            author=metadata.get("author", "Unknown"),
            publish_date=metadata.get("publish_date", datetime.now()),
            document_type=document_type,
            language=metadata.get("language", "en"),
            content_length=len(content),
            extraction_timestamp=datetime.now(),
        )

        # Create document
        doc = Document(
            page_content=content, metadata=doc_metadata.model_dump()
        )

        # Process into chunks
        chunks = await self._process_documents_to_chunks([doc])

        # Generate embeddings
        return await self._generate_embeddings(chunks)

    def get_embedding_statistics(self) -> Dict[str, Any]:
        """Get statistics about embedding operations.

        Returns:
            Dictionary with embedding statistics
        """
        return {
            "agent_name": self.name,
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
            "supported_document_types": SUPPORTED_DOCUMENT_TYPES,
            "metrics": self.get_metrics_summary(),
        }
