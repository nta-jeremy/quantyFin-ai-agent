# Agentic Pattern: Roles and Responsibilities

The QuantyFinAI Agent system employs a sophisticated multi-agent architecture, where specialized AI agents collaborate to achieve the overarching goal of financial analysis. Orchestration supports two engines (Google ADK and LangGraph) selected by configuration at runtime. In the MVP, prediction may be deferred to later sprints.

## 1. Guard Agent

**Role:** The primary security layer for the application and other agents.

**Responsibilities:**
*   **Prompt Injection Prevention:** Protects against malicious user inputs designed to manipulate agent behavior.
*   **Input Validation:** Validates user input to ensure it adheres to expected formats and safety guidelines.
*   **Security Filtering:** Filters out inappropriate or harmful content from user queries before they reach other agents.

## 2. Embedding Agent

**Role:** Responsible for transforming diverse documents and information into vector embeddings for efficient storage and semantic retrieval.

**Responsibilities:**
*   **Vector Embedding Generation:** Creates high-dimensional vector embeddings for various types of financial and economic documents, including:
    *   Corporate financial reports
    *   Stock-specific information
    *   Company profiles
    *   Industry and sector data
    *   National and global market information
*   **Vector Database Storage:** Stores the generated vector embeddings in the Postgres Vector Database, along with relevant metadata.
*   **Document Processing:** Handles the preprocessing of documents (e.g., chunking, cleaning) before embedding generation.

## 3. Aggregator Agent

**Role:** The central coordinator and synthesizer of information, ensuring efficient workflow and coherent final responses.

**Responsibilities:**
*   **Workflow Coordination:** Directs the flow of processing between different agents based on the current state and user input.
*   **Routing:** Determines which agent should be activated next (e.g., Search Agent, Analyze Agent, Predict Agent).
*   **State Management:** Tracks and updates the overall state of the process.
*   **Information Synthesis:** Collects and integrates outputs from various agents (e.g., retrieved documents, analytical results, predictions).
*   **Information Curation:** Eliminates redundant, conflicting, or irrelevant information.
*   **Final Answer Generation:** Uses an LLM to transform synthesized information into a coherent, user-friendly, and accurate final response.
*   **Quality Assurance:** Ensures the final answer meets quality requirements and is free from misinformation.
*   **Error Handling & Fallback:** Detects and handles errors (e.g., an agent failing to find information) and implements fallback mechanisms or informs the user.

## 4. Search Agent

**Role:** Specializes in understanding user queries and retrieving relevant information from external sources.

**Responsibilities:**
*   **Query Analysis:** Analyzes user queries to identify keywords, key concepts, and the user's true intent.
*   **Query Transformation:** Converts complex questions into effective search queries for external systems.
*   **External Source Querying:** Sends search requests to various external information sources (e.g., vector databases, web search engines, specific APIs).
*   **Information Retrieval:** Selects and retrieves the most relevant text snippets, documents, or data.
*   **Data Preprocessing:** Cleans and normalizes retrieved data, potentially summarizing documents, and tagging important information for subsequent agents.

## 5. Retriever Agent

**Role:** Focuses on querying and retrieving data from structured and unstructured databases, translating natural language requests into database-specific queries.

**Responsibilities:**
*   **Query Transformation:** Converts natural language requests into structured queries (e.g., SQL for PostgreSQL, vector queries for vector databases).
*   **Embedding Generation for Queries:** Generates embedding vectors from natural language queries for semantic search in vector databases.
*   **PostgreSQL Interaction:** Executes SQL queries to retrieve structured data (e.g., financial metrics, company details).
*   **Vector Database Interaction:** Sends embedding vectors to the vector database (e.g., `pgvector`) to find semantically similar documents or chunks.
*   **Data Filtering & Selection:** Filters out irrelevant data, ranks results by relevance, and selects the most pertinent documents or data points for further processing.
*   **Error Handling:** Manages scenarios where data is not found or database connection errors occur, providing appropriate feedback or fallback options.

## 6. Analyze Agent

**Role:** Specializes in processing raw documents and data to extract structured, valuable, and easily interpretable insights.

**Responsibilities:**
*   **Financial Report Analysis:** Extracts key financial figures (revenue, profit, cash flow, debt) from balance sheets, income statements, and cash flow statements.
*   **Financial Ratio Calculation:** Computes essential financial ratios (P/E, ROE, ROA, debt ratios) to assess financial health and performance.
*   **Trend Analysis:** Identifies growth or decline trends by comparing metrics across reporting periods.
*   **News and Media Analysis:** Summarizes articles, performs sentiment analysis (positive, negative, neutral), and identifies entities (companies, people, events).
*   **Regulatory and Legal Analysis:** Extracts relevant clauses from legal texts and assesses the impact of new policies on industries or companies.
*   **Stock Information Analysis:** Processes stock data (open/close prices, volume, price movements) and identifies price patterns, support, and resistance levels.
*   **Industry and Market Analysis:** Determines industry trends, competitive factors, market size, and growth potential from research reports.

## 7. Predict Agent

**Role:** Utilizes machine learning models and data analysis to forecast future trends based on aggregated and analyzed information.

**Responsibilities:**
*   **Input Data Analysis:** Processes structured and qualitative data from other agents (especially Analyze Agent) to identify key predictive factors.
*   **Model Selection & Training:** Selects and trains appropriate machine learning models (e.g., time-series models like ARIMA/LSTM for stock prices, regression models for economic indicators).
*   **Prediction Generation:** Generates specific predictions, including:
    *   Future stock price trends and potential reversal points.
    *   Forecasts for company revenues, profits, and other financial metrics.
    *   Predictions for industry and market development trends.
*   **Model Evaluation & Optimization:** Assesses prediction accuracy and adjusts model parameters or selects alternative models to improve performance.
