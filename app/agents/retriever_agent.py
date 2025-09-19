"""Retriever Agent for query transformation and data retrieval."""

import json
import re
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from .agent_state import StateManager, WorkflowState
from .agent_types import (
    AgentRole,
    DocumentMetadata,
    QueryType,
    RetrievalResult,
    SearchResult,
    WorkflowConfig,
)
from .base_agent import LLMBasedAgent


class SQLQueryTemplate(BaseModel):
    """Template for SQL query generation."""

    query_template: str
    parameters: List[str]
    description: str
    query_type: QueryType


class VectorSearchQuery(BaseModel):
    """Configuration for vector similarity search."""

    query_text: str
    search_type: str = "similarity"
    limit: int = 10
    score_threshold: float = 0.7
    filters: Dict[str, Any] = Field(default_factory=dict)


class RetrieverAgent(LLMBasedAgent):
    """Agent for query transformation and data retrieval from databases."""

    def __init__(
        self, llm_model: ChatOpenAI, config: Optional[WorkflowConfig] = None
    ):
        """Initialize the Retriever Agent.

        Args:
            llm_model: LLM model for query transformation
            config: Workflow configuration
        """
        super().__init__(
            role=AgentRole.RETRIEVER,
            name="Data Retrieval Specialist",
            description="Transforms natural language queries into database queries and retrieves relevant financial data",
            llm_model=llm_model,
            config=config,
            system_prompt=self._get_retriever_system_prompt(),
        )

        # Initialize SQL query templates
        self.sql_templates = self._initialize_sql_templates()

        # Initialize search configurations
        self.search_configs = {
            "stock_data": {"limit": 20, "time_range": "1y"},
            "company_financials": {"limit": 10, "time_range": "5y"},
            "market_data": {"limit": 50, "time_range": "6m"},
            "news_sentiment": {"limit": 30, "time_range": "3m"},
        }

    def _get_retriever_system_prompt(self) -> str:
        """Get system prompt for the Retriever Agent.

        Returns:
            System prompt string
        """
        return """You are a Data Retrieval Specialist responsible for transforming natural language queries into structured database queries.

Your responsibilities:
1. Analyze user queries to understand information requirements
2. Transform natural language into appropriate SQL queries
3. Generate vector search queries for semantic similarity
4. Determine optimal retrieval strategies for different query types
5. Combine structured and unstructured data retrieval
6. Optimize queries for performance and relevance

Focus on extracting the key entities, timeframes, and data types needed for effective financial data retrieval."""

    def get_required_predecessors(self) -> List[AgentRole]:
        """Get list of agents that must run before this agent.

        Returns:
            List with Guard and Embedding agents
        """
        return [AgentRole.GUARD, AgentRole.EMBEDDING]

    def validate_input(self, state: WorkflowState) -> bool:
        """Validate input state for Retriever Agent.

        Args:
            state: Current workflow state

        Returns:
            True if input is valid
        """
        return (
            state["guard_validation"]
            and state["guard_validation"].is_safe
            and state["embeddings"] is not None
            and state["current_query"]
            and len(state["current_query"].strip()) > 0
        )

    async def process(self, state: WorkflowState) -> WorkflowState:
        """Process query transformation and data retrieval.

        Args:
            state: Current workflow state

        Returns:
            Updated workflow state with retrieval results
        """
        query = state["current_query"]
        query_type = state["query_type"]

        self.logger.info(
            "Starting data retrieval processing",
            query_type=query_type.value,
            query_length=len(query),
        )

        try:
            # Step 1: Analyze and transform the query
            transformed_query = await self._transform_query(query, query_type)

            # Step 2: Execute structured data retrieval (SQL)
            sql_results = await self._execute_sql_retrieval(transformed_query)

            # Step 3: Execute vector similarity search
            vector_results = await self._execute_vector_search(
                transformed_query
            )

            # Step 4: Combine and rank results
            combined_results = await self._combine_results(
                sql_results, vector_results
            )

            # Step 5: Create retrieval result
            retrieval_result = RetrievalResult(
                results=combined_results,
                query_type=query_type,
                sources_used=transformed_query.get("sources_used", []),
                total_results=len(combined_results),
                processing_time=0.0,  # Will be calculated
            )

            # Calculate processing time
            retrieval_result.processing_time = state[
                "processing_metadata"
            ].get("retriever_processing_time", 0.0)

            # Update state with results
            state["retrieval_results"] = retrieval_result

            # Add processing message
            processing_message = self._create_processing_message(
                retrieval_result
            )
            state = StateManager.add_agent_message(
                state,
                processing_message,
                role="assistant",
                agent_role=self.role,
            )

            self.logger.info(
                "Data retrieval completed",
                total_results=len(combined_results),
                sql_results=len(sql_results),
                vector_results=len(vector_results),
            )

            return state

        except Exception as e:
            self.logger.error("Data retrieval processing failed", error=str(e))
            raise RuntimeError(f"Retrieval processing failed: {str(e)}")

    def _initialize_sql_templates(
        self,
    ) -> Dict[QueryType, List[SQLQueryTemplate]]:
        """Initialize SQL query templates for different query types.

        Returns:
            Dictionary mapping query types to SQL templates
        """
        return {
            QueryType.STOCK_ANALYSIS: [
                SQLQueryTemplate(
                    query_template="""
                        SELECT symbol, price, volume, market_cap, pe_ratio, dividend_yield
                        FROM stock_data
                        WHERE symbol = $1
                        ORDER BY date DESC
                        LIMIT $2
                    """,
                    parameters=["symbol", "limit"],
                    description="Get current stock data",
                    query_type=QueryType.STOCK_ANALYSIS,
                ),
                SQLQueryTemplate(
                    query_template="""
                        SELECT date, open_price, close_price, high_price, low_price, volume
                        FROM stock_prices
                        WHERE symbol = $1 AND date BETWEEN $2 AND $3
                        ORDER BY date
                    """,
                    parameters=["symbol", "start_date", "end_date"],
                    description="Get historical stock prices",
                    query_type=QueryType.STOCK_ANALYSIS,
                ),
            ],
            QueryType.COMPANY_FINANCIALS: [
                SQLQueryTemplate(
                    query_template="""
                        SELECT company_name, revenue, net_income, total_assets, total_liabilities,
                               operating_cash_flow, free_cash_flow, eps, roe, debt_to_equity
                        FROM financial_statements
                        WHERE company_id = $1 AND fiscal_year = $2
                    """,
                    parameters=["company_id", "fiscal_year"],
                    description="Get company financial statements",
                    query_type=QueryType.COMPANY_FINANCIALS,
                ),
                SQLQueryTemplate(
                    query_template="""
                        SELECT metric_name, metric_value, period, comparison_period
                        FROM financial_metrics
                        WHERE company_id = $1 AND metric_name IN ($2, $3, $4)
                        ORDER BY period DESC
                    """,
                    parameters=["company_id", "metric1", "metric2", "metric3"],
                    description="Get specific financial metrics",
                    query_type=QueryType.COMPANY_FINANCIALS,
                ),
            ],
            QueryType.MARKET_RESEARCH: [
                SQLQueryTemplate(
                    query_template="""
                        SELECT sector_name, avg_pe_ratio, avg_roe, market_cap_weight, performance_ytd
                        FROM sector_analysis
                        WHERE market = $1
                        ORDER BY market_cap_weight DESC
                    """,
                    parameters=["market"],
                    description="Get sector analysis",
                    query_type=QueryType.MARKET_RESEARCH,
                )
            ],
        }

    async def _transform_query(
        self, query: str, query_type: QueryType
    ) -> Dict[str, Any]:
        """Transform natural language query into structured queries.

        Args:
            query: Natural language query
            query_type: Type of query

        Returns:
            Transformed query with structured components
        """
        transformation_prompt = f"""
        Transform this financial query into structured retrieval components:

        Original Query: "{query}"
        Query Type: {query_type.value}

        Extract and return JSON with:
        {{
            "entities": {{"companies": ["company1"], "symbols": ["SYMBOL1"], "sectors": ["sector1"]}},
            "time_range": {{"start": "2024-01-01", "end": "2024-12-31"}},
            "metrics": ["revenue", "profit", "growth"],
            "data_sources": ["structured_db", "vector_db"],
            "query_strategy": "hybrid",
            "sql_queries": [
                {{"template": "SELECT ...", "parameters": ["value1", "value2"]}}
            ],
            "vector_query": {{"query_text": "expanded query text", "filters": {{}}}}
        }}
        """

        try:
            response = await self.invoke_llm(
                [
                    SystemMessage(
                        content="You are a query transformation expert for financial databases."
                    ),
                    HumanMessage(content=transformation_prompt),
                ]
            )

            # Parse the response
            response_text = response.content
            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if json_match:
                transformed = json.loads(json_match.group())
                return transformed
            else:
                # Fallback to basic transformation
                return await self._basic_query_transformation(
                    query, query_type
                )

        except Exception as e:
            self.logger.warning(
                "Query transformation failed, using fallback", error=str(e)
            )
            return await self._basic_query_transformation(query, query_type)

    async def _basic_query_transformation(
        self, query: str, query_type: QueryType
    ) -> Dict[str, Any]:
        """Basic query transformation when LLM transformation fails.

        Args:
            query: Natural language query
            query_type: Type of query

        Returns:
            Basic transformed query
        """
        # Extract basic entities using simple patterns
        entities = {
            "companies": self._extract_companies(query),
            "symbols": self._extract_symbols(query),
            "sectors": self._extract_sectors(query),
        }

        # Default time range (last year)
        time_range = {"start": "2023-01-01", "end": "2024-12-31"}

        return {
            "entities": entities,
            "time_range": time_range,
            "metrics": ["revenue", "profit", "growth"],
            "data_sources": ["structured_db", "vector_db"],
            "query_strategy": "hybrid",
            "sql_queries": [],
            "vector_query": {"query_text": query, "filters": {}},
            "sources_used": ["database", "vector_search"],
        }

    def _extract_companies(self, query: str) -> List[str]:
        """Extract company names from query.

        Args:
            query: Query text

        Returns:
            List of company names
        """
        # Simple pattern matching for common companies
        common_companies = [
            "Apple",
            "Microsoft",
            "Google",
            "Amazon",
            "Tesla",
            "Meta",
            "Netflix",
            "NVIDIA",
            "AMD",
            "Intel",
            "IBM",
            "Oracle",
            "Salesforce",
        ]

        found = []
        for company in common_companies:
            if company.lower() in query.lower():
                found.append(company)

        return found

    def _extract_symbols(self, query: str) -> List[str]:
        """Extract stock symbols from query.

        Args:
            query: Query text

        Returns:
            List of stock symbols
        """
        # Look for ticker symbols (1-5 capital letters)
        symbol_pattern = r"\b[A-Z]{1,5}\b"
        symbols = re.findall(symbol_pattern, query)

        # Filter out common words
        common_words = {
            "THE",
            "AND",
            "OR",
            "FOR",
            "WITH",
            "FROM",
            "THAT",
            "THIS",
            "HAVE",
        }
        return [s for s in symbols if s not in common_words]

    def _extract_sectors(self, query: str) -> List[str]:
        """Extract sector names from query.

        Args:
            query: Query text

        Returns:
            List of sector names
        """
        common_sectors = [
            "Technology",
            "Healthcare",
            "Financial",
            "Energy",
            "Consumer",
            "Industrial",
            "Real Estate",
            "Utilities",
            "Communications",
            "Materials",
        ]

        found = []
        for sector in common_sectors:
            if sector.lower() in query.lower():
                found.append(sector)

        return found

    async def _execute_sql_retrieval(
        self, transformed_query: Dict[str, Any]
    ) -> List[SearchResult]:
        """Execute SQL queries for structured data retrieval.

        Args:
            transformed_query: Transformed query with SQL components

        Returns:
            List of search results from SQL queries
        """
        results = []

        try:
            # Get SQL queries from transformed query
            sql_queries = transformed_query.get("sql_queries", [])

            # If no SQL queries in transformed query, use templates
            if not sql_queries:
                query_type = transformed_query.get(
                    "query_type", QueryType.GENERAL_FINANCE
                )
                templates = self.sql_templates.get(query_type, [])

                for template in templates:
                    # In a real implementation, you would execute these SQL queries
                    # using your postgres_adapter
                    sql_result = await self._simulate_sql_execution(
                        template, transformed_query
                    )
                    results.extend(sql_result)

            # Execute provided SQL queries
            for sql_query in sql_queries:
                template = sql_query.get("template")
                parameters = sql_query.get("parameters", [])

                if template:
                    sql_template = SQLQueryTemplate(
                        query_template=template,
                        parameters=parameters,
                        description="Generated SQL query",
                        query_type=QueryType.GENERAL_FINANCE,
                    )
                    sql_result = await self._simulate_sql_execution(
                        sql_template, transformed_query
                    )
                    results.extend(sql_result)

        except Exception as e:
            self.logger.error("SQL retrieval failed", error=str(e))

        return results

    async def _simulate_sql_execution(
        self, template: SQLQueryTemplate, transformed_query: Dict[str, Any]
    ) -> List[SearchResult]:
        """Simulate SQL execution (replace with actual database calls).

        Args:
            template: SQL query template
            transformed_query: Transformed query with parameters

        Returns:
            List of search results
        """
        # In a real implementation, this would execute actual SQL queries
        # using your postgres_adapter

        # Simulate some results based on the template description
        results = []

        # Generate mock data based on template description
        if "stock data" in template.description.lower():
            symbols = transformed_query.get("entities", {}).get(
                "symbols", ["AAPL"]
            )
            for symbol in symbols[:3]:  # Limit to 3 symbols
                result = SearchResult(
                    id=UUID(int=int.from_bytes(symbol.encode(), "big")),
                    content=f"Stock data for {symbol}: Price $150.25, Volume 1.2M, Market Cap $2.5T",
                    score=0.85,
                    metadata=DocumentMetadata(
                        source="structured_database",
                        title=f"Stock Data: {symbol}",
                        document_type="stock_data",
                        content_length=100,
                        extraction_timestamp=datetime.now(),
                    ),
                    source_type="database",
                    relevance_score=0.85,
                )
                results.append(result)

        elif "financial statements" in template.description.lower():
            companies = transformed_query.get("entities", {}).get(
                "companies", ["Apple Inc"]
            )
            for company in companies[:2]:
                result = SearchResult(
                    id=UUID(int=int.from_bytes(company.encode(), "big")),
                    content=f"Financial statement for {company}: Revenue $394.3B, Net Income $99.8B, Assets $382.9B",
                    score=0.90,
                    metadata=DocumentMetadata(
                        source="structured_database",
                        title=f"Financial Statement: {company}",
                        document_type="financial_statement",
                        content_length=120,
                        extraction_timestamp=datetime.now(),
                    ),
                    source_type="database",
                    relevance_score=0.90,
                )
                results.append(result)

        return results

    async def _execute_vector_search(
        self, transformed_query: Dict[str, Any]
    ) -> List[SearchResult]:
        """Execute vector similarity search.

        Args:
            transformed_query: Transformed query with vector components

        Returns:
            List of search results from vector search
        """
        results = []

        try:
            vector_query = transformed_query.get("vector_query", {})
            query_text = vector_query.get(
                "query_text", transformed_query.get("original_query", "")
            )

            # Create vector search configuration
            search_config = VectorSearchQuery(
                query_text=query_text,
                limit=10,
                score_threshold=0.6,
                filters=vector_query.get("filters", {}),
            )

            # In a real implementation, this would use your vector_db_adapter
            vector_results = await self._simulate_vector_search(search_config)
            results.extend(vector_results)

        except Exception as e:
            self.logger.error("Vector search failed", error=str(e))

        return results

    async def _simulate_vector_search(
        self, search_config: VectorSearchQuery
    ) -> List[SearchResult]:
        """Simulate vector search (replace with actual vector database calls).

        Args:
            search_config: Vector search configuration

        Returns:
            List of search results
        """
        # In a real implementation, this would query your vector database
        # using your vector_db_adapter

        # Simulate vector search results
        results = []

        # Generate mock semantic search results
        query_terms = search_config.query_text.lower().split()
        relevant_topics = [
            "financial performance analysis",
            "market trends and outlook",
            "investment strategy recommendations",
            "risk assessment and mitigation",
            "economic indicators analysis",
        ]

        for i, topic in enumerate(relevant_topics[: search_config.limit]):
            # Check if topic is relevant to query
            relevance = (
                sum(1 for term in query_terms if term in topic.lower())
                / len(query_terms)
                if query_terms
                else 0.5
            )

            if relevance >= 0.3:  # Minimum relevance threshold
                result = SearchResult(
                    id=UUID(int=i),
                    content=f"Relevant document about {topic}. Contains comprehensive analysis and insights related to the query.",
                    score=relevance * 0.9,  # Scale to 0-1 range
                    metadata=DocumentMetadata(
                        source="vector_database",
                        title=f"Analysis: {topic}",
                        document_type="financial_analysis",
                        content_length=800,
                        extraction_timestamp=datetime.now(),
                    ),
                    source_type="vector",
                    relevance_score=relevance,
                )
                results.append(result)

        # Sort by relevance score
        results.sort(key=lambda x: x.relevance_score, reverse=True)

        return results[: search_config.limit]

    async def _combine_results(
        self,
        sql_results: List[SearchResult],
        vector_results: List[SearchResult],
    ) -> List[SearchResult]:
        """Combine and rank results from different sources.

        Args:
            sql_results: Results from SQL queries
            vector_results: Results from vector search

        Returns:
            Combined and ranked results
        """
        all_results = sql_results + vector_results

        # Deduplicate results based on content similarity
        unique_results = []
        seen_content = set()

        for result in all_results:
            # Simple content-based deduplication
            content_hash = hash(result.content[:100])  # Hash first 100 chars
            if content_hash not in seen_content:
                unique_results.append(result)
                seen_content.add(content_hash)

        # Rank by relevance score with slight preference for structured data
        for result in unique_results:
            if result.source_type == "database":
                result.relevance_score *= 1.1  # Boost structured data slightly

        # Sort by final relevance score
        unique_results.sort(key=lambda x: x.relevance_score, reverse=True)

        # Limit total results
        return unique_results[:20]

    def _create_processing_message(self, result: RetrievalResult) -> str:
        """Create a processing message for the conversation.

        Args:
            result: Retrieval processing result

        Returns:
            Processing message string
        """
        source_types = set(result.source_type for result in result.results)
        return (
            f"🔍 Data Retrieval Complete: Found {len(result.results)} relevant results "
            f"from {len(source_types)} sources ({', '.join(source_types)}) "
            f"in {result.processing_time:.2f}s. Query type: {result.query_type.value}."
        )

    async def explain_retrieval_strategy(
        self, query: str, query_type: QueryType
    ) -> str:
        """Explain the retrieval strategy for a given query.

        Args:
            query: User query
            query_type: Type of query

        Returns:
            Explanation of retrieval strategy
        """
        explanation_prompt = f"""
        Explain the data retrieval strategy for this financial query:

        Query: "{query}"
        Query Type: {query_type.value}

        Provide a detailed explanation of:
        1. What types of data would be most relevant
        2. How the query would be transformed for database search
        3. What SQL queries might be generated
        4. How vector similarity search would be used
        5. How results would be combined and ranked
        """

        response = await self.invoke_llm(
            [
                SystemMessage(
                    content="You are a data retrieval strategy expert."
                ),
                HumanMessage(content=explanation_prompt),
            ]
        )

        return response.content

    def get_retrieval_statistics(self) -> Dict[str, Any]:
        """Get statistics about retrieval operations.

        Returns:
            Dictionary with retrieval statistics
        """
        return {
            "agent_name": self.name,
            "sql_templates_count": sum(
                len(templates) for templates in self.sql_templates.values()
            ),
            "search_configs": list(self.search_configs.keys()),
            "supported_query_types": [qt.value for qt in QueryType],
            "metrics": self.get_metrics_summary(),
        }
