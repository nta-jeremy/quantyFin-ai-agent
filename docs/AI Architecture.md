# AI Architecture: Retrieval-Augmented Generation (RAG) and Multi-Agent System

The QuantyFinAI Agent system is built upon a sophisticated AI architecture that combines Retrieval-Augmented Generation (RAG) with a multi-agent framework. This design enables the system to perform complex financial analysis, synthesize information from diverse sources, and generate accurate, context-aware predictions.

## 1. Core Concept: Retrieval-Augmented Generation (RAG)

RAG is a powerful technique that enhances the capabilities of Large Language Models (LLMs) by allowing them to retrieve relevant information from an external knowledge base before generating a response. This approach addresses common LLM limitations such as factual inaccuracies and hallucinations.

### How RAG Works in QuantyFinAI Agent:

1.  **Query Processing:** A user query is received and processed by specialized agents.
2.  **Information Retrieval:** Relevant documents, data points, and facts are retrieved from a vast knowledge base (long-term memory, e.g., Postgres Vector Database) using semantic search.
3.  **Context Augmentation:** The retrieved information is then provided to an LLM as additional context alongside the original query.
4.  **Response Generation:** The LLM generates a response that is grounded in the retrieved facts, leading to more accurate, reliable, and up-to-date answers.

## 2. Multi-Agent System with Dual Engines (LangGraph & Google ADK)

The RAG process in QuantyFinAI Agent is orchestrated through a multi-agent system that supports two engines: **LangGraph** and **Google ADK**. This dual-engine design enables stateful, multi-actor applications with LLMs, where specialized agents collaborate and pass information between each other. The active engine is selected via configuration at runtime.

### Benefits of a Multi-Agent Architecture:

*   **Modularity:** Each agent is specialized for a particular task (e.g., searching, analyzing, predicting), making the system easier to develop, test, and maintain.
*   **Scalability:** Individual agents can be scaled independently based on their computational demands.
*   **Robustness:** The system can handle complex queries by breaking them down into sub-tasks managed by different agents.
*   **Improved Accuracy:** Specialized agents can perform their tasks more effectively than a single monolithic LLM, leading to higher quality outputs.
*   **Error Handling:** Agents can be designed with fallback mechanisms and error handling specific to their domain.

## 3. Integration of LLMs and Embedding Models

The AI architecture heavily relies on both Large Language Models (LLMs) and Embedding Models:

*   **LLMs (OpenAI, Anthropic, Gemini, DeepSeek):** Used by various agents for natural language understanding, summarization, generation, and complex reasoning tasks. The system is designed to be flexible, allowing integration with multiple LLM providers.
*   **Embedding Models (OpenAI, HuggingFace):** Essential for converting text data into high-dimensional vector embeddings. These embeddings are stored in the Postgres Vector Database and enable efficient semantic search and similarity comparisons, forming the backbone of the RAG system.

## 4. Knowledge Base

The knowledge base is a critical component, comprising diverse data sources:

*   **Structured Data:** Financial reports, stock prices, company profiles stored in PostgresDB.
*   **Unstructured Data:** News articles, legal documents, economic reports, and other textual content, converted into embeddings and stored in the Postgres Vector Database.
*   **Web Search (Later Stage):** Real-time web search can be added in later sprints.
*   **APIs (Later Stage):** External APIs for dynamic data retrieval are planned beyond MVP.

This AI architecture, combining RAG with a multi-agent system and dual-engine orchestration, positions QuantyFinAI Agent as a powerful tool for grounded financial analysis. In the MVP, prediction can be deferred, with a focus on retrieval, analysis, and cited answers.
