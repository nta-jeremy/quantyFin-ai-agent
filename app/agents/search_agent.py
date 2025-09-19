"""Search Agent for external API integration and web search."""

import asyncio
import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from .agent_state import StateManager, WorkflowState
from .agent_types import (
    AgentRole,
    DocumentMetadata,
    ExternalSearchResult,
    QueryType,
    SearchResult,
    WorkflowConfig,
)
from .base_agent import LLMBasedAgent


class APISource(BaseModel):
    """Configuration for external API sources."""

    name: str
    base_url: str
    api_key: Optional[str] = None
    rate_limit: int = 60  # requests per minute
    enabled: bool = True


class SearchAgent(LLMBasedAgent):
    """Agent for external API integration and web search."""

    def __init__(
        self, llm_model: ChatOpenAI, config: Optional[WorkflowConfig] = None
    ):
        """Initialize the Search Agent.

        Args:
            llm_model: LLM model for search query generation
            config: Workflow configuration
        """
        super().__init__(
            role=AgentRole.SEARCH,
            name="External Search Specialist",
            description="Integrates external APIs and web search for comprehensive financial data retrieval",
            llm_model=llm_model,
            config=config,
            system_prompt=self._get_search_system_prompt(),
        )

        # Initialize API sources
        self.api_sources = self._initialize_api_sources()

        # Search configurations
        self.search_config = {
            "max_results_per_source": 10,
            "timeout_per_request": 10.0,
            "enable_rate_limiting": True,
        }

    def _get_search_system_prompt(self) -> str:
        """Get system prompt for the Search Agent.

        Returns:
            System prompt string
        """
        return """You are an External Search Specialist responsible for integrating external APIs and web search for comprehensive financial data retrieval.

Your responsibilities:
1. Analyze query requirements for external data sources
2. Generate effective search queries for different APIs
3. Coordinate multiple external data sources simultaneously
4. Filter and validate external search results
5. Integrate web search with financial APIs
6. Handle rate limiting and API errors gracefully

Focus on finding the most relevant and up-to-date financial information from reliable external sources."""

    def get_required_predecessors(self) -> List[AgentRole]:
        """Get list of agents that must run before this agent.

        Returns:
            List with Guard, Embedding, and Retriever agents
        """
        return [AgentRole.GUARD, AgentRole.EMBEDDING, AgentRole.RETRIEVER]

    def validate_input(self, state: WorkflowState) -> bool:
        """Validate input state for Search Agent.

        Args:
            state: Current workflow state

        Returns:
            True if input is valid
        """
        return (
            state["guard_validation"]
            and state["guard_validation"].is_safe
            and state["embeddings"] is not None
            and state["retrieval_results"] is not None
            and state["current_query"]
            and len(state["current_query"].strip()) > 0
        )

    async def process(self, state: WorkflowState) -> WorkflowState:
        """Process external API and web search.

        Args:
            state: Current workflow state

        Returns:
            Updated workflow state with search results
        """
        query = state["current_query"]
        query_type = state["query_type"]

        self.logger.info(
            "Starting external search processing",
            query_type=query_type.value,
            query_length=len(query),
        )

        try:
            # Step 1: Analyze search requirements
            search_requirements = await self._analyze_search_requirements(
                query, query_type
            )

            # Step 2: Generate search queries for different sources
            search_queries = await self._generate_search_queries(
                search_requirements
            )

            # Step 3: Execute external API searches
            api_results = await self._execute_api_searches(search_queries)

            # Step 4: Execute web search if needed
            web_results = await self._execute_web_search(search_queries)

            # Step 5: Combine and filter all search results
            combined_results = await self._combine_search_results(
                api_results, web_results
            )

            # Step 6: Create external search result
            external_search_result = ExternalSearchResult(
                results=combined_results,
                api_sources=list(search_requirements.get("api_sources", [])),
                web_sources=search_requirements.get("web_sources", []),
                processing_time=0.0,
                rate_limit_info={},
            )

            # Calculate processing time
            external_search_result.processing_time = state[
                "processing_metadata"
            ].get("search_processing_time", 0.0)

            # Update state with results
            state["search_results"] = external_search_result

            # Add processing message
            processing_message = self._create_processing_message(
                external_search_result
            )
            state = StateManager.add_agent_message(
                state,
                processing_message,
                role="assistant",
                agent_role=self.role,
            )

            self.logger.info(
                "External search completed",
                total_results=len(combined_results),
                api_sources=len(external_search_result.api_sources),
                web_sources=len(external_search_result.web_sources),
            )

            return state

        except Exception as e:
            self.logger.error(
                "External search processing failed", error=str(e)
            )
            raise RuntimeError(f"Search processing failed: {str(e)}")

    def _initialize_api_sources(self) -> Dict[str, APISource]:
        """Initialize external API sources.

        Returns:
            Dictionary of API sources
        """
        return {
            "financial_data": APISource(
                name="Financial Data API",
                base_url="https://api.financialdata.com",
                rate_limit=100,
            ),
            "market_data": APISource(
                name="Market Data API",
                base_url="https://api.marketdata.com",
                rate_limit=60,
            ),
            "news_api": APISource(
                name="Financial News API",
                base_url="https://api.newsapi.com",
                rate_limit=120,
            ),
            "economic_data": APISource(
                name="Economic Data API",
                base_url="https://api.economicdata.gov",
                rate_limit=30,
            ),
        }

    async def _analyze_search_requirements(
        self, query: str, query_type: QueryType
    ) -> Dict[str, Any]:
        """Analyze search requirements for the query.

        Args:
            query: User query
            query_type: Type of query

        Returns:
            Search requirements analysis
        """
        analysis_prompt = f"""
        Analyze this financial query to determine external data source requirements:

        Query: "{query}"
        Query Type: {query_type.value}

        Return JSON with:
        {{
            "required_data_types": ["real_time_prices", "historical_data", "news_sentiment"],
            "api_sources": ["financial_data", "market_data", "news_api"],
            "web_sources": ["financial_news", "company_reports", "market_analysis"],
            "search_timeframe": "1m",
            "priority_sources": ["real_time_data", "recent_news"],
            "filter_criteria": {{"min_relevance": 0.7, "max_age_days": 30}}
        }}
        """

        try:
            response = await self.invoke_llm(
                [
                    SystemMessage(
                        content="You are a financial data source analysis expert."
                    ),
                    HumanMessage(content=analysis_prompt),
                ]
            )

            response_text = response.content
            import json
            import re

            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if json_match:
                requirements = json.loads(json_match.group())
                return requirements
            else:
                return self._get_default_search_requirements(query_type)

        except Exception as e:
            self.logger.warning(
                "Search requirements analysis failed", error=str(e)
            )
            return self._get_default_search_requirements(query_type)

    def _get_default_search_requirements(
        self, query_type: QueryType
    ) -> Dict[str, Any]:
        """Get default search requirements for query type.

        Args:
            query_type: Type of query

        Returns:
            Default search requirements
        """
        requirements = {
            "required_data_types": ["market_data", "financial_news"],
            "api_sources": ["market_data", "news_api"],
            "web_sources": ["financial_news", "market_analysis"],
            "search_timeframe": "3m",
            "priority_sources": ["market_data"],
            "filter_criteria": {"min_relevance": 0.6, "max_age_days": 90},
        }

        # Customize based on query type
        if query_type == QueryType.STOCK_ANALYSIS:
            requirements["api_sources"].extend(["financial_data"])
            requirements["required_data_types"].extend(["real_time_prices"])
        elif query_type == QueryType.NEWS_SENTIMENT:
            requirements["api_sources"] = ["news_api"]
            requirements["required_data_types"] = [
                "news_sentiment",
                "social_media",
            ]
        elif query_type == QueryType.MARKET_RESEARCH:
            requirements["web_sources"].extend(
                ["research_reports", "industry_analysis"]
            )

        return requirements

    async def _generate_search_queries(
        self, requirements: Dict[str, Any]
    ) -> Dict[str, List[str]]:
        """Generate search queries for different sources.

        Args:
            requirements: Search requirements

        Returns:
            Dictionary mapping source types to search queries
        """
        query_generation_prompt = f"""
        Generate optimized search queries for these financial search requirements:

        Requirements: {json.dumps(requirements, indent=2)}

        Generate JSON with different query variations for each source type:
        {{
            "api_queries": {{"financial_data": ["query1", "query2"], "news_api": ["query3"]}},
            "web_search_queries": ["web_query1", "web_query2", "web_query3"],
            "query_variations": {{"broad": "broad search", "specific": "specific search"}}
        }}
        """

        try:
            response = await self.invoke_llm(
                [
                    SystemMessage(
                        content="You are a search query optimization expert."
                    ),
                    HumanMessage(content=query_generation_prompt),
                ]
            )

            response_text = response.content
            import json
            import re

            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if json_match:
                queries = json.loads(json_match.group())
                return queries
            else:
                return self._get_default_search_queries(requirements)

        except Exception as e:
            self.logger.warning("Search query generation failed", error=str(e))
            return self._get_default_search_queries(requirements)

    def _get_default_search_queries(
        self, requirements: Dict[str, Any]
    ) -> Dict[str, List[str]]:
        """Get default search queries.

        Args:
            requirements: Search requirements

        Returns:
            Default search queries
        """
        return {
            "api_queries": {
                "financial_data": ["financial market data", "stock prices"],
                "news_api": ["financial news", "market updates"],
                "market_data": ["market trends", "economic indicators"],
            },
            "web_search_queries": [
                "financial analysis",
                "market research",
                "investment insights",
            ],
            "query_variations": {
                "broad": "financial markets",
                "specific": "current financial analysis",
            },
        }

    async def _execute_api_searches(
        self, search_queries: Dict[str, List[str]]
    ) -> List[SearchResult]:
        """Execute searches through external APIs.

        Args:
            search_queries: Search queries for different sources

        Returns:
            List of search results from APIs
        """
        results = []
        api_queries = search_queries.get("api_queries", {})

        # Create tasks for parallel API execution
        tasks = []

        for api_name, queries in api_queries.items():
            if api_name in self.api_sources:
                api_source = self.api_sources[api_name]
                if api_source.enabled:
                    task = self._search_api_source(api_source, queries)
                    tasks.append(task)

        # Execute API searches in parallel
        if tasks:
            api_results_list = await asyncio.gather(
                *tasks, return_exceptions=True
            )

            # Process results
            for i, result in enumerate(api_results_list):
                if isinstance(result, Exception):
                    self.logger.error("API search failed", error=str(result))
                elif isinstance(result, list):
                    results.extend(result)

        return results

    async def _search_api_source(
        self, api_source: APISource, queries: List[str]
    ) -> List[SearchResult]:
        """Search a specific API source.

        Args:
            api_source: API source configuration
            queries: Search queries

        Returns:
            List of search results from the API
        """
        results = []

        try:
            # Simulate API calls (replace with actual API integration)
            for query in queries[:2]:  # Limit queries per source
                api_result = await self._simulate_api_call(api_source, query)
                results.extend(api_result)

                # Rate limiting
                if self.search_config["enable_rate_limiting"]:
                    await asyncio.sleep(60.0 / api_source.rate_limit)

        except Exception as e:
            self.logger.error(
                f"API search failed for {api_source.name}", error=str(e)
            )

        return results

    async def _simulate_api_call(
        self, api_source: APISource, query: str
    ) -> List[SearchResult]:
        """Simulate API call (replace with actual API integration).

        Args:
            api_source: API source configuration
            query: Search query

        Returns:
            List of search results from the API
        """
        # In a real implementation, this would make actual API calls
        # For now, simulate results based on API source type

        results = []

        # Generate mock API results
        result_count = min(5, self.search_config["max_results_per_source"])

        for i in range(result_count):
            result = SearchResult(
                id=uuid4(),
                content=f"API result from {api_source.name} for query '{query}': Contains relevant financial data and analysis.",
                score=0.7 + (i * 0.05),  # Decreasing score
                metadata=DocumentMetadata(
                    source=api_source.base_url,
                    title=f"{api_source.name} Result {i+1}",
                    document_type="api_data",
                    content_length=300,
                    extraction_timestamp=datetime.now(),
                ),
                source_type="api",
                relevance_score=0.7 + (i * 0.05),
            )
            results.append(result)

        return results

    async def _execute_web_search(
        self, search_queries: Dict[str, List[str]]
    ) -> List[SearchResult]:
        """Execute web search.

        Args:
            search_queries: Search queries

        Returns:
            List of search results from web search
        """
        results = []
        web_queries = search_queries.get("web_search_queries", [])

        for query in web_queries[:3]:  # Limit web queries
            try:
                # Simulate web search (replace with actual web search API)
                web_results = await self._simulate_web_search(query)
                results.extend(web_results)
            except Exception as e:
                self.logger.error(
                    "Web search failed", query=query, error=str(e)
                )

        return results

    async def _simulate_web_search(self, query: str) -> List[SearchResult]:
        """Simulate web search (replace with actual web search API).

        Args:
            query: Search query

        Returns:
            List of search results from web search
        """
        # In a real implementation, this would use a web search API
        # like Google Search API, Bing Search API, etc.

        results = []

        # Generate mock web search results
        result_count = min(8, self.search_config["max_results_per_source"])

        web_sources = [
            "financial-times.com",
            "bloomberg.com",
            "reuters.com",
            "wsj.com",
            "seekingalpha.com",
            "investopedia.com",
            "marketwatch.com",
            "yahoo.com",
        ]

        for i in range(result_count):
            source = web_sources[i % len(web_sources)]
            result = SearchResult(
                id=uuid4(),
                content=f"Web search result from {source} for '{query}': Comprehensive financial analysis and market insights.",
                score=0.6 + (i * 0.03),  # Decreasing score
                metadata=DocumentMetadata(
                    source=f"https://{source}",
                    title=f"Financial Analysis: {query.title()}",
                    document_type="web_content",
                    content_length=500,
                    extraction_timestamp=datetime.now(),
                ),
                source_type="web",
                relevance_score=0.6 + (i * 0.03),
            )
            results.append(result)

        return results

    async def _combine_search_results(
        self, api_results: List[SearchResult], web_results: List[SearchResult]
    ) -> List[SearchResult]:
        """Combine and filter search results from different sources.

        Args:
            api_results: Results from API searches
            web_results: Results from web search

        Returns:
            Combined and filtered search results
        """
        all_results = api_results + web_results

        # Remove duplicates based on content similarity
        unique_results = []
        seen_hashes = set()

        for result in all_results:
            content_hash = hash(result.content[:200])  # Hash first 200 chars
            if content_hash not in seen_hashes:
                unique_results.append(result)
                seen_hashes.add(content_hash)

        # Sort by relevance score with preference for API results
        for result in unique_results:
            if result.source_type == "api":
                result.relevance_score *= 1.2  # Boost API results
            elif result.source_type == "web":
                result.relevance_score *= 0.9  # Slightly reduce web results

        # Sort by final relevance score
        unique_results.sort(key=lambda x: x.relevance_score, reverse=True)

        # Limit total results
        return unique_results[:15]

    def _create_processing_message(self, result: ExternalSearchResult) -> str:
        """Create a processing message for the conversation.

        Args:
            result: External search result

        Returns:
            Processing message string
        """
        total_sources = len(result.api_sources) + len(result.web_sources)
        return (
            f"🌐 External Search Complete: Retrieved {len(result.results)} results "
            f"from {total_sources} external sources ({len(result.api_sources)} APIs, "
            f"{len(result.web_sources)} web sources) in {result.processing_time:.2f}s."
        )

    async def discover_relevant_sources(
        self, query: str, query_type: QueryType
    ) -> List[str]:
        """Discover relevant external sources for a query.

        Args:
            query: User query
            query_type: Type of query

        Returns:
            List of relevant source names
        """
        discovery_prompt = f"""
        Discover the most relevant external data sources for this financial query:

        Query: "{query}"
        Query Type: {query_type.value}

        Recommend specific APIs, websites, and data sources that would provide the most valuable information.
        Include both free and paid sources, and indicate their specialties.
        """

        response = await self.invoke_llm(
            [
                SystemMessage(
                    content="You are an expert in financial data sources and APIs."
                ),
                HumanMessage(content=discovery_prompt),
            ]
        )

        return response.content

    def get_search_statistics(self) -> Dict[str, Any]:
        """Get statistics about search operations.

        Returns:
            Dictionary with search statistics
        """
        return {
            "agent_name": self.name,
            "api_sources_count": len(self.api_sources),
            "enabled_api_sources": [
                name
                for name, source in self.api_sources.items()
                if source.enabled
            ],
            "search_config": self.search_config,
            "metrics": self.get_metrics_summary(),
        }
