"""Analyze Agent for financial analysis and sentiment processing."""

import json
import re
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from .agent_state import StateManager, WorkflowState
from .agent_types import AgentRole, AnalysisResult, DocumentMetadata, QueryType
from .base_agent import LLMBasedAgent


class FinancialMetric(BaseModel):
    """Individual financial metric."""

    name: str
    value: float
    unit: Optional[str] = None
    timestamp: datetime
    confidence: float = Field(ge=0.0, le=1.0)


class SentimentAnalysis(BaseModel):
    """Sentiment analysis result."""

    sentiment: str  # "positive", "negative", "neutral"
    confidence: float = Field(ge=0.0, le=1.0)
    aspects: Dict[str, float] = Field(default_factory=dict)
    explanation: str


class AnalyzeAgent(LLMBasedAgent):
    """Agent for financial analysis and sentiment processing."""

    def __init__(
        self, llm_model: ChatOpenAI, config: Optional[WorkflowConfig] = None
    ):
        """Initialize the Analyze Agent.

        Args:
            llm_model: LLM model for financial analysis
            config: Workflow configuration
        """
        super().__init__(
            role=AgentRole.ANALYZE,
            name="Financial Analysis Specialist",
            description="Processes financial data and performs sentiment analysis for insights generation",
            llm_model=llm_model,
            config=config,
            system_prompt=self._get_analysis_system_prompt(),
        )

        # Analysis configurations
        self.analysis_config = {
            "sentiment_threshold": 0.6,
            "min_confidence": 0.5,
            "max_aspects": 10,
            "enable_risk_analysis": True,
        }

    def _get_analysis_system_prompt(self) -> str:
        """Get system prompt for the Analyze Agent.

        Returns:
            System prompt string
        """
        return """You are a Financial Analysis Specialist responsible for processing financial data and generating insights.

Your responsibilities:
1. Extract and calculate financial metrics from raw data
2. Perform sentiment analysis on news and financial content
3. Identify trends and patterns in financial data
4. Generate investment insights and risk assessments
5. Compare financial performance against benchmarks
6. Provide actionable recommendations based on analysis

Focus on delivering accurate, data-driven financial insights with clear confidence levels."""

    def get_required_predecessors(self) -> List[AgentRole]:
        """Get list of agents that must run before this agent.

        Returns:
            List with Guard, Embedding, Retriever, and Search agents
        """
        return [
            AgentRole.GUARD,
            AgentRole.EMBEDDING,
            AgentRole.RETRIEVER,
            AgentRole.SEARCH,
        ]

    def validate_input(self, state: WorkflowState) -> bool:
        """Validate input state for Analyze Agent.

        Args:
            state: Current workflow state

        Returns:
            True if input is valid
        """
        return (
            state["guard_validation"]
            and state["guard_validation"].is_safe
            and state["embeddings"] is not None
            and (
                state["retrieval_results"] is not None
                or state["search_results"] is not None
            )
            and state["current_query"]
            and len(state["current_query"].strip()) > 0
        )

    async def process(self, state: WorkflowState) -> WorkflowState:
        """Process financial analysis and sentiment analysis.

        Args:
            state: Current workflow state

        Returns:
            Updated workflow state with analysis results
        """
        query = state["current_query"]
        query_type = state["query_type"]

        self.logger.info(
            "Starting financial analysis processing",
            query_type=query_type.value,
            query_length=len(query),
        )

        try:
            # Step 1: Gather all available data
            available_data = self._gather_available_data(state)

            # Step 2: Determine analysis requirements
            analysis_requirements = (
                await self._determine_analysis_requirements(
                    query, query_type, available_data
                )
            )

            # Step 3: Perform financial metrics analysis
            metrics_results = await self._analyze_financial_metrics(
                analysis_requirements, available_data
            )

            # Step 4: Perform sentiment analysis
            sentiment_results = await self._analyze_sentiment(
                analysis_requirements, available_data
            )

            # Step 5: Generate insights and trends
            insights_results = await self._generate_insights(
                analysis_requirements, metrics_results, sentiment_results
            )

            # Step 6: Create comprehensive analysis result
            analysis_results = [
                metrics_results,
                sentiment_results,
                insights_results,
            ]

            # Update state with results
            state["analysis_results"] = analysis_results

            # Add processing message
            processing_message = self._create_processing_message(
                analysis_results
            )
            state = StateManager.add_agent_message(
                state,
                processing_message,
                role="assistant",
                agent_role=self.role,
            )

            self.logger.info(
                "Financial analysis completed",
                analysis_count=len(analysis_results),
                total_insights=len(insights_results.insights),
            )

            return state

        except Exception as e:
            self.logger.error(
                "Financial analysis processing failed", error=str(e)
            )
            raise RuntimeError(f"Analysis processing failed: {str(e)}")

    def _gather_available_data(self, state: WorkflowState) -> Dict[str, Any]:
        """Gather all available data from previous agents.

        Args:
            state: Current workflow state

        Returns:
            Dictionary with all available data
        """
        data = {
            "retrieval_results": state.get("retrieval_results"),
            "search_results": state.get("search_results"),
            "embeddings": state.get("embeddings"),
            "documents": state.get("documents"),
            "query_context": {
                "original_query": state["original_query"],
                "current_query": state["current_query"],
                "query_type": state["query_type"],
            },
        }

        return data

    async def _determine_analysis_requirements(
        self, query: str, query_type: QueryType, available_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Determine analysis requirements based on query and available data.

        Args:
            query: User query
            query_type: Type of query
            available_data: Available data from previous agents

        Returns:
            Analysis requirements
        """
        requirements_prompt = f"""
        Determine the required financial analysis for this query and available data:

        Query: "{query}"
        Query Type: {query_type.value}
        Available Data: {json.dumps(available_data.keys(), indent=2)}

        Return JSON with analysis requirements:
        {{
            "required_metrics": ["revenue_growth", "profit_margins", "stock_performance"],
            "sentiment_analysis_needed": true,
            "trend_analysis_needed": true,
            "comparative_analysis": true,
            "risk_assessment": true,
            "time_periods": ["1y", "3y", "5y"],
            "benchmark_indicators": ["sp500", "sector_average"],
            "analysis_depth": "comprehensive"
        }}
        """

        try:
            response = await self.invoke_llm(
                [
                    SystemMessage(
                        content="You are a financial analysis requirements expert."
                    ),
                    HumanMessage(content=requirements_prompt),
                ]
            )

            response_text = response.content
            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if json_match:
                requirements = json.loads(json_match.group())
                return requirements
            else:
                return self._get_default_analysis_requirements(query_type)

        except Exception as e:
            self.logger.warning(
                "Analysis requirements determination failed", error=str(e)
            )
            return self._get_default_analysis_requirements(query_type)

    def _get_default_analysis_requirements(
        self, query_type: QueryType
    ) -> Dict[str, Any]:
        """Get default analysis requirements for query type.

        Args:
            query_type: Type of query

        Returns:
            Default analysis requirements
        """
        requirements = {
            "required_metrics": ["revenue", "profit", "growth"],
            "sentiment_analysis_needed": True,
            "trend_analysis_needed": True,
            "comparative_analysis": False,
            "risk_assessment": True,
            "time_periods": ["1y"],
            "benchmark_indicators": [],
            "analysis_depth": "standard",
        }

        # Customize based on query type
        if query_type == QueryType.STOCK_ANALYSIS:
            requirements["required_metrics"].extend(
                ["pe_ratio", "dividend_yield", "market_cap"]
            )
            requirements["comparative_analysis"] = True
            requirements["benchmark_indicators"] = ["sp500"]
        elif query_type == QueryType.COMPANY_FINANCIALS:
            requirements["required_metrics"].extend(
                ["debt_to_equity", "roe", "current_ratio"]
            )
            requirements["analysis_depth"] = "detailed"
        elif query_type == QueryType.NEWS_SENTIMENT:
            requirements["sentiment_analysis_needed"] = True
            requirements["trend_analysis_needed"] = True

        return requirements

    async def _analyze_financial_metrics(
        self, requirements: Dict[str, Any], available_data: Dict[str, Any]
    ) -> AnalysisResult:
        """Analyze financial metrics from available data.

        Args:
            requirements: Analysis requirements
            available_data: Available data

        Returns:
            Financial metrics analysis result
        """
        start_time = datetime.now()

        # Extract financial data from available sources
        financial_data = self._extract_financial_data(available_data)

        # Analyze required metrics
        metrics = {}
        required_metrics = requirements.get("required_metrics", [])

        for metric in required_metrics:
            metric_value = await self._calculate_metric(metric, financial_data)
            if metric_value is not None:
                metrics[metric] = metric_value

        # Generate insights from metrics
        insights = await self._generate_metrics_insights(metrics, requirements)

        processing_time = (datetime.now() - start_time).total_seconds()

        return AnalysisResult(
            analysis_type="financial_metrics",
            insights=insights,
            metrics=metrics,
            confidence_score=self._calculate_analysis_confidence(metrics),
            processing_time=processing_time,
            data_sources=["financial_database", "market_data"],
        )

    def _extract_financial_data(
        self, available_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract financial data from available sources.

        Args:
            available_data: Available data sources

        Returns:
            Extracted financial data
        """
        financial_data = {}

        # Extract from retrieval results
        retrieval_results = available_data.get("retrieval_results")
        if retrieval_results and retrieval_results.results:
            for result in retrieval_results.results:
                if result.source_type == "database":
                    # Parse financial data from database results
                    parsed_data = self._parse_financial_content(result.content)
                    financial_data.update(parsed_data)

        # Extract from search results
        search_results = available_data.get("search_results")
        if search_results and search_results.results:
            for result in search_results.results:
                if result.source_type in ["api", "web"]:
                    # Parse financial data from API/web results
                    parsed_data = self._parse_financial_content(result.content)
                    financial_data.update(parsed_data)

        return financial_data

    def _parse_financial_content(self, content: str) -> Dict[str, Any]:
        """Parse financial data from content text.

        Args:
            content: Content text to parse

        Returns:
            Parsed financial data
        """
        # Simple financial data extraction (in real implementation, use more sophisticated parsing)
        data = {}

        # Look for common financial patterns
        import re

        # Extract monetary values
        monetary_pattern = r"\$([0-9,]+\.?[0-9]*)\s*(million|billion|M|B)?"
        matches = re.findall(monetary_pattern, content, re.IGNORECASE)

        # Extract percentage values
        percentage_pattern = r"([0-9]+\.?[0-9]*)%"
        percentage_matches = re.findall(percentage_pattern, content)

        if matches:
            data["monetary_values"] = matches
        if percentage_matches:
            data["percentage_values"] = [float(p) for p in percentage_matches]

        return data

    async def _calculate_metric(
        self, metric_name: str, financial_data: Dict[str, Any]
    ) -> Optional[float]:
        """Calculate a specific financial metric.

        Args:
            metric_name: Name of the metric
            financial_data: Available financial data

        Returns:
            Calculated metric value or None
        """
        # In a real implementation, this would perform actual calculations
        # For now, simulate metric calculations

        metric_calculations = {
            "revenue": lambda data: 150000000,  # Simulated revenue
            "profit": lambda data: 45000000,  # Simulated profit
            "growth": lambda data: 12.5,  # Simulated growth percentage
            "pe_ratio": lambda data: 22.3,  # Simulated P/E ratio
            "roe": lambda data: 18.7,  # Simulated ROE
            "debt_to_equity": lambda data: 0.65,  # Simulated debt-to-equity ratio
        }

        calculator = metric_calculations.get(metric_name)
        if calculator:
            return calculator(financial_data)

        return None

    async def _generate_metrics_insights(
        self, metrics: Dict[str, float], requirements: Dict[str, Any]
    ) -> List[str]:
        """Generate insights from financial metrics.

        Args:
            metrics: Calculated financial metrics
            requirements: Analysis requirements

        Returns:
            List of insights
        """
        if not metrics:
            return ["Insufficient data for financial metrics analysis"]

        insights_prompt = f"""
        Generate financial insights from these metrics:

        Metrics: {json.dumps(metrics, indent=2)}
        Analysis Requirements: {json.dumps(requirements, indent=2)}

        Provide 3-5 actionable insights about the financial performance, trends, and investment implications.
        Focus on key strengths, weaknesses, opportunities, and risks.
        """

        response = await self.invoke_llm(
            [
                SystemMessage(content="You are a financial insights expert."),
                HumanMessage(content=insights_prompt),
            ]
        )

        # Parse insights from response
        insights_text = response.content
        insights = [
            insight.strip()
            for insight in insights_text.split("\n")
            if insight.strip()
        ]

        return insights[:5]  # Limit to 5 insights

    async def _analyze_sentiment(
        self, requirements: Dict[str, Any], available_data: Dict[str, Any]
    ) -> AnalysisResult:
        """Perform sentiment analysis on available content.

        Args:
            requirements: Analysis requirements
            available_data: Available data

        Returns:
            Sentiment analysis result
        """
        start_time = datetime.now()

        if not requirements.get("sentiment_analysis_needed", False):
            return AnalysisResult(
                analysis_type="sentiment_analysis",
                insights=["Sentiment analysis not required for this query"],
                metrics={},
                confidence_score=1.0,
                processing_time=0.1,
                data_sources=[],
            )

        # Gather content for sentiment analysis
        content_for_analysis = self._gather_content_for_sentiment(
            available_data
        )

        # Perform sentiment analysis
        sentiment_results = await self._perform_sentiment_analysis(
            content_for_analysis
        )

        # Generate sentiment insights
        sentiment_insights = await self._generate_sentiment_insights(
            sentiment_results
        )

        processing_time = (datetime.now() - start_time).total_seconds()

        return AnalysisResult(
            analysis_type="sentiment_analysis",
            insights=sentiment_insights,
            metrics={
                "overall_sentiment": (
                    1.0
                    if sentiment_results.sentiment == "positive"
                    else (
                        0.0
                        if sentiment_results.sentiment == "neutral"
                        else -1.0
                    )
                ),
                "sentiment_confidence": sentiment_results.confidence,
            },
            confidence_score=sentiment_results.confidence,
            processing_time=processing_time,
            data_sources=[
                "news_content",
                "financial_reports",
                "market_commentary",
            ],
        )

    def _gather_content_for_sentiment(
        self, available_data: Dict[str, Any]
    ) -> List[str]:
        """Gather content for sentiment analysis.

        Args:
            available_data: Available data sources

        Returns:
            List of content strings for analysis
        """
        content = []

        # Extract from search results (news, web content)
        search_results = available_data.get("search_results")
        if search_results and search_results.results:
            for result in search_results.results:
                if result.source_type in ["web", "api"]:
                    content.append(result.content)

        # Extract from retrieval results
        retrieval_results = available_data.get("retrieval_results")
        if retrieval_results and retrieval_results.results:
            for result in retrieval_results.results:
                if (
                    result.source_type == "vector"
                ):  # Vector results often contain news/reports
                    content.append(result.content)

        return content[:10]  # Limit to 10 content pieces

    async def _perform_sentiment_analysis(
        self, content_list: List[str]
    ) -> SentimentAnalysis:
        """Perform sentiment analysis on content.

        Args:
            content_list: List of content strings

        Returns:
            Sentiment analysis result
        """
        if not content_list:
            return SentimentAnalysis(
                sentiment="neutral",
                confidence=0.5,
                explanation="No content available for sentiment analysis",
            )

        # Combine content for analysis
        combined_content = "\n\n".join(
            content_list[:5]
        )  # Limit content for LLM processing

        sentiment_prompt = f"""
        Analyze the sentiment of this financial content:

        Content:
        {combined_content}

        Return JSON with:
        {{
            "sentiment": "positive|negative|neutral",
            "confidence": 0.0-1.0,
            "aspects": {{"financial_performance": 0.8, "market_outlook": 0.6}},
            "explanation": "detailed explanation of sentiment analysis"
        }}
        """

        try:
            response = await self.invoke_llm(
                [
                    SystemMessage(
                        content="You are a financial sentiment analysis expert."
                    ),
                    HumanMessage(content=sentiment_prompt),
                ]
            )

            response_text = response.content
            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if json_match:
                sentiment_data = json.loads(json_match.group())
                return SentimentAnalysis(**sentiment_data)

        except Exception as e:
            self.logger.warning("Sentiment analysis failed", error=str(e))

        # Fallback sentiment analysis
        return SentimentAnalysis(
            sentiment="neutral",
            confidence=0.5,
            explanation="Automated sentiment analysis unavailable",
        )

    async def _generate_sentiment_insights(
        self, sentiment_results: SentimentAnalysis
    ) -> List[str]:
        """Generate insights from sentiment analysis.

        Args:
            sentiment_results: Sentiment analysis results

        Returns:
            List of sentiment insights
        """
        insights = []

        if sentiment_results.sentiment == "positive":
            insights.append(
                f"Positive sentiment detected with {sentiment_results.confidence:.1%} confidence"
            )
            if sentiment_results.aspects:
                top_aspect = max(
                    sentiment_results.aspects.items(), key=lambda x: x[1]
                )
                insights.append(
                    f"Most positive aspect: {top_aspect[0]} ({top_aspect[1]:.1%})"
                )
        elif sentiment_results.sentiment == "negative":
            insights.append(
                f"Negative sentiment detected with {sentiment_results.confidence:.1%} confidence"
            )
            if sentiment_results.aspects:
                weakest_aspect = min(
                    sentiment_results.aspects.items(), key=lambda x: x[1]
                )
                insights.append(
                    f"Weakest aspect: {weakest_aspect[0]} ({weakest_aspect[1]:.1%})"
                )
        else:
            insights.append(
                "Neutral sentiment detected, indicating balanced perspectives"
            )

        insights.append(
            f"Sentiment explanation: {sentiment_results.explanation}"
        )

        return insights

    async def _generate_insights(
        self,
        requirements: Dict[str, Any],
        metrics_results: AnalysisResult,
        sentiment_results: AnalysisResult,
    ) -> AnalysisResult:
        """Generate comprehensive insights and trends.

        Args:
            requirements: Analysis requirements
            metrics_results: Financial metrics analysis
            sentiment_results: Sentiment analysis results

        Returns:
            Comprehensive insights analysis result
        """
        start_time = datetime.now()

        # Combine all analysis results
        all_insights = metrics_results.insights + sentiment_results.insights

        # Generate additional trend and comparative insights
        if requirements.get("trend_analysis_needed", False):
            trend_insights = await self._analyze_trends(
                requirements, metrics_results
            )
            all_insights.extend(trend_insights)

        if requirements.get("comparative_analysis", False):
            comparative_insights = await self._perform_comparative_analysis(
                requirements, metrics_results
            )
            all_insights.extend(comparative_insights)

        if requirements.get("risk_assessment", False):
            risk_insights = await self._assess_risks(
                requirements, metrics_results, sentiment_results
            )
            all_insights.extend(risk_insights)

        processing_time = (datetime.now() - start_time).total_seconds()

        return AnalysisResult(
            analysis_type="comprehensive_insights",
            insights=all_insights,
            metrics={
                "total_insights": len(all_insights),
                "metrics_confidence": metrics_results.confidence_score,
                "sentiment_confidence": sentiment_results.confidence_score,
            },
            confidence_score=(
                metrics_results.confidence_score
                + sentiment_results.confidence_score
            )
            / 2,
            processing_time=processing_time,
            data_sources=metrics_results.data_sources
            + sentiment_results.data_sources,
        )

    async def _analyze_trends(
        self, requirements: Dict[str, Any], metrics_results: AnalysisResult
    ) -> List[str]:
        """Analyze trends in financial data.

        Args:
            requirements: Analysis requirements
            metrics_results: Financial metrics results

        Returns:
            List of trend insights
        """
        # Simulate trend analysis
        return [
            "Positive revenue growth trend observed over the past year",
            "Profit margins showing improvement with seasonal fluctuations",
            "Market performance above sector average in recent quarters",
        ]

    async def _perform_comparative_analysis(
        self, requirements: Dict[str, Any], metrics_results: AnalysisResult
    ) -> List[str]:
        """Perform comparative analysis against benchmarks.

        Args:
            requirements: Analysis requirements
            metrics_results: Financial metrics results

        Returns:
            List of comparative insights
        """
        # Simulate comparative analysis
        return [
            "Outperforming S&P 500 by 3.2% year-to-date",
            "Higher profit margins compared to industry average",
            "Stronger balance sheet than peer companies",
        ]

    async def _assess_risks(
        self,
        requirements: Dict[str, Any],
        metrics_results: AnalysisResult,
        sentiment_results: AnalysisResult,
    ) -> List[str]:
        """Assess investment and operational risks.

        Args:
            requirements: Analysis requirements
            metrics_results: Financial metrics results
            sentiment_results: Sentiment analysis results

        Returns:
            List of risk insights
        """
        # Simulate risk assessment
        return [
            "Moderate market risk due to economic uncertainty",
            "Strong operational risk management procedures in place",
            "Low financial risk with healthy cash reserves",
        ]

    def _calculate_analysis_confidence(
        self, metrics: Dict[str, float]
    ) -> float:
        """Calculate confidence score for analysis results.

        Args:
            metrics: Calculated metrics

        Returns:
            Confidence score between 0 and 1
        """
        if not metrics:
            return 0.3  # Low confidence with no metrics

        # Calculate confidence based on number and quality of metrics
        base_confidence = min(0.9, 0.5 + (len(metrics) * 0.1))
        return base_confidence

    def _create_processing_message(
        self, analysis_results: List[AnalysisResult]
    ) -> str:
        """Create a processing message for the conversation.

        Args:
            analysis_results: List of analysis results

        Returns:
            Processing message string
        """
        total_insights = sum(
            len(result.insights) for result in analysis_results
        )
        analysis_types = [
            result.analysis_type.replace("_", " ").title()
            for result in analysis_results
        ]

        return (
            f"📊 Financial Analysis Complete: Generated {total_insights} insights "
            f"across {len(analysis_types)} analysis types ({', '.join(analysis_types)}) "
            f"with average confidence {(sum(r.confidence_score for r in analysis_results) / len(analysis_results)):.1%}."
        )

    async def explain_analysis_methodology(
        self, query: str, query_type: QueryType
    ) -> str:
        """Explain the analysis methodology for a given query.

        Args:
            query: User query
            query_type: Type of query

        Returns:
            Explanation of analysis methodology
        """
        methodology_prompt = f"""
        Explain the financial analysis methodology for this query:

        Query: "{query}"
        Query Type: {query_type.value}

        Provide a detailed explanation of:
        1. What financial metrics would be analyzed
        2. How sentiment analysis would be performed
        3. What trends and patterns would be identified
        4. How comparative analysis would be conducted
        5. What risk factors would be assessed
        """

        response = await self.invoke_llm(
            [
                SystemMessage(
                    content="You are a financial analysis methodology expert."
                ),
                HumanMessage(content=methodology_prompt),
            ]
        )

        return response.content

    def get_analysis_statistics(self) -> Dict[str, Any]:
        """Get statistics about analysis operations.

        Returns:
            Dictionary with analysis statistics
        """
        return {
            "agent_name": self.name,
            "analysis_config": self.analysis_config,
            "supported_analysis_types": [
                "financial_metrics",
                "sentiment_analysis",
                "trend_analysis",
                "comparative_analysis",
                "risk_assessment",
            ],
            "metrics": self.get_metrics_summary(),
        }
