# AI Agents: Roles and Responsibilities

The QuantyFinAI Agent system is built upon a multi-agent architecture, where each AI agent is specialized for a particular task, collaborating to achieve comprehensive financial analysis and stock prediction. The agents are orchestrated using LangGraph.

## 1. Guard Agent

**Role:** Acts as the primary security layer for the application and other agents.

**Responsibilities:**
*   **Prompt Injection Prevention:** Protects against malicious user inputs that attempt to manipulate agent behavior.
*   **User Input Validation:** Ensures user inputs are safe and conform to expected formats.

## 2. Embedding Agent

**Role:** Responsible for generating vector embeddings from various financial and economic documents.

**Responsibilities:**
*   **Vector Embedding Creation:** Generates embeddings for financial reports, stock information, company data, industry data, and market information.
*   **Vector Database Storage:** Stores these embeddings, along with relevant metadata, into the Postgres Vector Database.

## 3. Aggregator Agent

**Role:** The central coordinator and synthesizer of information, ensuring efficient workflow and coherent final responses.

**Responsibilities:**
*   **Coordination and Flow Management:** Directs the processing flow among other agents, acting as a control hub.
*   **Routing:** Decides which agent should be activated next based on user input and current graph state.
*   **State Management:** Tracks and updates the overall process state.
*   **Information Synthesis:** Collects and integrates outputs from various agents (e.g., Retrieval Agent, Analytics Agent).
*   **Information Curation:** Removes duplicate, conflicting, or irrelevant information.
*   **Final Answer Generation:** Uses a Large Language Model (LLM) to convert synthesized information into a coherent, user-friendly, and accurate final response.
*   **Quality Assurance:** Ensures the final answer meets quality requirements and is free from misinformation.
*   **Error Handling and Fallback:** Detects and handles errors (e.g., an agent failing to find information) and implements fallback mechanisms or informs the user.

## 4. Search Agent

**Role:** Specializes in searching and retrieving information from external sources.

**Responsibilities:**
*   **Query Analysis and Understanding:** Analyzes user queries to identify keywords, key concepts, and the underlying intent.
*   **Query Transformation:** Converts complex questions into effective search queries for external systems (e.g., vector databases, web search engines, APIs).
*   **Information Retrieval:** Selects and retrieves the most relevant text snippets, documents, or data.
*   **Data Preprocessing:** Cleans and normalizes retrieved data, potentially summarizing documents, and tagging important information for subsequent agents.

## 5. Retriever Agent

**Role:** Acts as an expert in querying and retrieving data from both structured and unstructured databases.

**Responsibilities:**
*   **Query Transformation:** Converts natural language requests into structured queries (e.g., SQL for PostgreSQL, vector queries for vector databases).
*   **Query Embedding Generation:** Generates embedding vectors from natural language queries for semantic search in vector databases.
*   **Database Interaction:** Connects and interacts with specified databases, executing SQL queries for structured data (PostgreSQL) and vector queries for semantic data (Postgres Vector Database).
*   **Data Selection and Filtering:** Filters out irrelevant data, ranks results by relevance, and selects the most pertinent documents or data points.
*   **Error Handling:** Manages scenarios where data is not found or database connection errors occur.

## 6. Analyze Agent

**Role:** Specializes in processing raw documents and data to extract structured, valuable, and easily interpretable insights.

**Responsibilities:**
*   **Financial Report Analysis:** Extracts key financial metrics (revenue, profit, cash flow, debt) and calculates financial ratios (P/E, ROE, ROA, debt ratios).
*   **Trend Analysis:** Identifies growth or decline trends by comparing metrics across reporting periods.
*   **News and Media Analysis:** Summarizes articles, performs sentiment analysis (positive, negative, neutral), and identifies entities (companies, people, events).
*   **Regulatory and Legal Analysis:** Extracts relevant clauses from legal texts and assesses the impact of new policies on industries or companies.
*   **Stock Information Analysis:** Processes stock data (open/close prices, volume, price movements) and identifies price patterns, support, and resistance levels.
*   **Industry and Market Analysis:** Determines industry trends, competitive factors, market size, and growth potential from research reports.

## 7. Predict Agent

**Role:** Utilizes machine learning models and data analysis to forecast future trends based on aggregated and analyzed information.

**Responsibilities:**
*   **Input Data Analysis:** Processes structured and qualitative data from other agents (especially Analyze Agent) to identify key predictive factors.
*   **Model Selection and Training:** Selects and trains appropriate machine learning models (e.g., time-series models like ARIMA/LSTM for stock prices, regression models for economic indicators).
*   **Prediction Generation:** Generates specific predictions, including future stock price trends, forecasts for company revenues/profits, and industry/market development trends.
*   **Model Evaluation and Optimization:** Assesses prediction accuracy and adjusts model parameters or selects alternative models to improve performance.
