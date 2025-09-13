# Memory Management

The QuantyFinAI Agent system employs a dual-tiered memory strategy, combining short-term and long-term memory components to efficiently manage conversational context, user sessions, and a vast knowledge base. This approach ensures both responsiveness and comprehensive information retrieval for the AI agents.

## 1. Short-Term Memory: Redis

**Redis** is utilized for managing short-term memory, primarily focusing on session management and caching. This in-memory data store provides fast read/write operations, which are crucial for maintaining conversational flow and improving application performance.

### Key Uses for Redis:

*   **Session Management:** Stores active user sessions, including user authentication tokens, temporary states, and recent interactions. This allows the system to maintain context across multiple requests within a user's active session.
*   **Caching:** Caches frequently accessed data, intermediate processing results, or LLM responses to reduce latency and computational load on the backend and external API calls. This significantly speeds up response times for repetitive queries or common data lookups.

## 2. Long-Term Memory: Postgres Vector Database

The **Postgres Vector Database** (e.g., using the `pgvector` extension) serves as the long-term memory for the AI system. It stores vector embeddings of a wide array of documents and information, enabling semantic search and Retrieval-Augmented Generation (RAG) capabilities.

### Key Uses for Postgres Vector Database:

*   **Knowledge Base Storage:** Stores vector representations of all ingested documents, including:
    *   Corporate financial reports
    *   News articles and media content
    *   Regulatory and legal documents
    *   Economic data and reports
    *   Stock-specific information
    *   Industry and market analyses
*   **Semantic Search:** Allows AI agents (e.g., Retriever Agent, Search Agent) to perform semantic searches, finding documents or text chunks that are conceptually similar to a given query, rather than just keyword matching. This is fundamental for the RAG architecture.
*   **Contextual Retrieval:** Provides the necessary external knowledge base for LLMs to ground their responses, ensuring accuracy and reducing hallucinations by retrieving relevant, up-to-date information.

## Interaction between Memory Tiers

*   **Short-term context** from Redis can be used to refine queries sent to the long-term memory, making retrieval more precise.
*   **Retrieved information** from the Postgres Vector Database can be temporarily cached in Redis if it's likely to be accessed again soon within the same session or by other users.

This integrated memory approach allows the QuantyFinAI Agent to maintain a dynamic understanding of current interactions while drawing upon a vast, persistent knowledge base for deep financial analysis.
