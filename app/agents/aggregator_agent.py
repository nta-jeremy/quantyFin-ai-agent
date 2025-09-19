"""Aggregator Agent for workflow orchestration and response synthesis."""

import json
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from .agent_state import StateManager, WorkflowState
from .agent_types import AgentRole, DocumentMetadata, QueryType, WorkflowConfig
from .base_agent import LLMBasedAgent


class ResponseSection(BaseModel):
    """Individual section of the synthesized response."""

    title: str
    content: str
    confidence: float = Field(ge=0.0, le=1.0)
    sources: List[str]
    section_type: str  # "summary", "analysis", "prediction", "recommendation"


class AggregationStrategy(BaseModel):
    """Strategy for aggregating agent results."""

    prioritization: List[AgentRole]
    synthesis_method: str  # "comprehensive", "concise", "detailed"
    include_sources: bool
    include_confidence: bool
    include_risks: bool


class AggregatorAgent(LLMBasedAgent):
    """Agent for workflow orchestration and response synthesis."""

    def __init__(
        self, llm_model: ChatOpenAI, config: Optional[WorkflowConfig] = None
    ):
        """Initialize the Aggregator Agent.

        Args:
            llm_model: LLM model for response synthesis
            config: Workflow configuration
        """
        super().__init__(
            role=AgentRole.AGGREGATOR,
            name="Response Synthesis Specialist",
            description="Orchestrates agent workflows and synthesizes comprehensive final responses",
            llm_model=llm_model,
            config=config,
            system_prompt=self._get_aggregator_system_prompt(),
        )

        # Aggregation configurations
        self.aggregation_config = {
            "max_response_length": 2000,
            "min_confidence_threshold": 0.5,
            "enable_structured_output": True,
            "include_execution_summary": True,
        }

    def _get_aggregator_system_prompt(self) -> str:
        """Get system prompt for the Aggregator Agent.

        Returns:
            System prompt string
        """
        return """You are a Response Synthesis Specialist responsible for orchestrating multi-agent workflows and generating comprehensive final responses.

Your responsibilities:
1. Synthesize results from all previous agents into coherent responses
2. Prioritize and weight different information sources appropriately
3. Generate structured, actionable responses with clear sourcing
4. Include confidence assessments and risk disclosures
5. Provide follow-up recommendations and next steps
6. Maintain consistency with financial analysis best practices

Focus on delivering clear, well-structured responses that provide maximum value while being transparent about limitations and uncertainties."""

    def get_required_predecessors(self) -> List[AgentRole]:
        """Get list of agents that must run before this agent.

        Returns:
            List with all previous agents
        """
        return [
            AgentRole.GUARD,
            AgentRole.EMBEDDING,
            AgentRole.RETRIEVER,
            AgentRole.SEARCH,
            AgentRole.ANALYZE,
            AgentRole.PREDICT,
        ]

    def validate_input(self, state: WorkflowState) -> bool:
        """Validate input state for Aggregator Agent.

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
            and state["analysis_results"] is not None
            and state["current_query"]
            and len(state["current_query"].strip()) > 0
        )

    async def process(self, state: WorkflowState) -> WorkflowState:
        """Process response synthesis and final aggregation.

        Args:
            state: Current workflow state

        Returns:
            Updated workflow state with final response
        """
        query = state["current_query"]
        query_type = state["query_type"]

        self.logger.info(
            "Starting response synthesis processing",
            query_type=query_type.value,
            query_length=len(query),
        )

        try:
            # Step 1: Analyze workflow execution and available results
            workflow_analysis = self._analyze_workflow_execution(state)

            # Step 2: Determine aggregation strategy
            aggregation_strategy = await self._determine_aggregation_strategy(
                query, query_type, workflow_analysis
            )

            # Step 3: Extract and organize results from all agents
            organized_results = self._organize_agent_results(
                state, aggregation_strategy
            )

            # Step 4: Synthesize comprehensive response
            synthesized_response = await self._synthesize_response(
                query, organized_results, aggregation_strategy
            )

            # Step 5: Generate follow-up recommendations
            recommendations = await self._generate_recommendations(
                query, organized_results, synthesized_response
            )

            # Step 6: Create final structured response
            final_response = await self._create_final_response(
                synthesized_response, recommendations, aggregation_strategy
            )

            # Update state with final response
            final_state = StateManager.finalize_workflow(
                state, final_response, success=True
            )

            # Update sources used
            all_sources = self._extract_all_sources(organized_results)
            final_state["sources_used"] = all_sources

            self.logger.info(
                "Response synthesis completed",
                response_length=len(final_response),
                sources_count=len(all_sources),
                workflow_agents=len(final_state["agent_execution_order"]),
            )

            return final_state

        except Exception as e:
            self.logger.error(
                "Response synthesis processing failed", error=str(e)
            )
            # Create fallback response
            fallback_response = await self._create_fallback_response(
                query, str(e)
            )
            return StateManager.finalize_workflow(
                state, fallback_response, success=False
            )

    def _analyze_workflow_execution(
        self, state: WorkflowState
    ) -> Dict[str, Any]:
        """Analyze the execution of the workflow.

        Args:
            state: Current workflow state

        Returns:
            Workflow execution analysis
        """
        analysis = {
            "executed_agents": state["agent_execution_order"],
            "execution_order": [
                agent.value for agent in state["agent_execution_order"]
            ],
            "processing_metadata": state["processing_metadata"],
            "error_count": state["error_count"],
            "execution_time": None,
        }

        # Calculate total execution time
        if state["start_time"] and state["end_time"]:
            analysis["execution_time"] = (
                state["end_time"] - state["start_time"]
            ).total_seconds()

        # Analyze agent-specific processing times
        agent_times = {}
        for agent_role in state["agent_execution_order"]:
            time_key = f"{agent_role.value}_execution_time"
            if time_key in state["processing_metadata"]:
                times = state["processing_metadata"][time_key]
                if times:
                    agent_times[agent_role.value] = sum(times) / len(times)

        analysis["agent_processing_times"] = agent_times

        return analysis

    async def _determine_aggregation_strategy(
        self,
        query: str,
        query_type: QueryType,
        workflow_analysis: Dict[str, Any],
    ) -> AggregationStrategy:
        """Determine the best strategy for aggregating results.

        Args:
            query: User query
            query_type: Type of query
            workflow_analysis: Workflow execution analysis

        Returns:
            Aggregation strategy
        """
        strategy_prompt = f"""
        Determine the optimal aggregation strategy for synthesizing this financial query response:

        Query: "{query}"
        Query Type: {query_type.value}
        Executed Agents: {workflow_analysis['execution_order']}
        Processing Times: {workflow_analysis.get('agent_processing_times', {})}

        Consider:
        - Query complexity and information requirements
        - Quality and completeness of agent results
        - User's likely need for detail vs. conciseness
        - Type of financial analysis requested

        Return JSON with aggregation strategy:
        {{
            "prioritization": ["analysis", "prediction", "retrieval"],
            "synthesis_method": "comprehensive|concise|detailed",
            "include_sources": true,
            "include_confidence": true,
            "include_risks": true,
            "response_tone": "professional|educational|actionable"
        }}
        """

        try:
            response = await self.invoke_llm(
                [
                    SystemMessage(
                        content="You are a response aggregation strategy expert."
                    ),
                    HumanMessage(content=strategy_prompt),
                ]
            )

            response_text = response.content
            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if json_match:
                strategy_data = json.loads(json_match.group())
                return AggregationStrategy(**strategy_data)

        except Exception as e:
            self.logger.warning(
                "Aggregation strategy determination failed", error=str(e)
            )

        # Fallback strategy
        return AggregationStrategy(
            prioritization=[
                AgentRole.ANALYZE,
                AgentRole.PREDICT,
                AgentRole.RETRIEVER,
            ],
            synthesis_method="comprehensive",
            include_sources=True,
            include_confidence=True,
            include_risks=True,
        )

    def _organize_agent_results(
        self, state: WorkflowState, strategy: AggregationStrategy
    ) -> Dict[str, Any]:
        """Organize results from all agents based on strategy.

        Args:
            state: Current workflow state
            strategy: Aggregation strategy

        Returns:
            Organized agent results
        """
        organized = {
            "query_context": {
                "original_query": state["original_query"],
                "current_query": state["current_query"],
                "query_type": state["query_type"],
                "security_level": state["security_level"].value,
            },
            "agent_results": {},
            "available_data": {},
            "confidence_assessment": {},
        }

        # Collect results from each executed agent
        for agent_role in state["agent_execution_order"]:
            agent_key = agent_role.value
            agent_result = None

            if agent_role == AgentRole.GUARD:
                agent_result = state.get("guard_validation")
            elif agent_role == AgentRole.EMBEDDING:
                agent_result = state.get("embeddings")
            elif agent_role == AgentRole.RETRIEVER:
                agent_result = state.get("retrieval_results")
            elif agent_role == AgentRole.SEARCH:
                agent_result = state.get("search_results")
            elif agent_role == AgentRole.ANALYZE:
                agent_result = state.get("analysis_results")
            elif agent_role == AgentRole.PREDICT:
                agent_result = state.get("prediction_results")

            if agent_result:
                organized["agent_results"][agent_key] = agent_result

        # Calculate overall confidence assessment
        organized["confidence_assessment"] = (
            self._calculate_overall_confidence(organized["agent_results"])
        )

        return organized

    def _calculate_overall_confidence(
        self, agent_results: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calculate overall confidence assessment from agent results.

        Args:
            agent_results: Results from all agents

        Returns:
            Confidence assessment
        """
        confidence_scores = []

        # Extract confidence scores from different agent types
        if "guard" in agent_results and agent_results["guard"]:
            confidence_scores.append(agent_results["guard"].confidence_score)

        if "analysis" in agent_results and agent_results["analysis"]:
            for analysis in agent_results["analysis"]:
                confidence_scores.append(analysis.confidence_score)

        if "prediction" in agent_results and agent_results["prediction"]:
            for prediction in agent_results["prediction"]:
                confidence_scores.append(prediction.confidence_score)

        # Calculate weighted average
        if confidence_scores:
            # More recent results (higher index) get slightly higher weight
            weights = [i + 1 for i in range(len(confidence_scores))]
            weighted_sum = sum(
                score * weight
                for score, weight in zip(confidence_scores, weights)
            )
            total_weight = sum(weights)
            overall_confidence = weighted_sum / total_weight
        else:
            overall_confidence = 0.5

        return {
            "overall_confidence": overall_confidence,
            "agent_count": len(confidence_scores),
            "confidence_range": (
                min(confidence_scores) if confidence_scores else 0.0,
                max(confidence_scores) if confidence_scores else 0.0,
            ),
        }

    async def _synthesize_response(
        self,
        query: str,
        organized_results: Dict[str, Any],
        strategy: AggregationStrategy,
    ) -> str:
        """Synthesize the comprehensive response.

        Args:
            query: Original query
            organized_results: Organized agent results
            strategy: Aggregation strategy

        Returns:
            Synthesized response
        """
        # Prepare synthesis context
        synthesis_context = self._prepare_synthesis_context(organized_results)

        synthesis_prompt = f"""
        Synthesize a comprehensive financial analysis response based on the following information:

        Original Query: "{query}"
        Query Type: {organized_results['query_context']['query_type'].value}
        Overall Confidence: {organized_results['confidence_assessment']['overall_confidence']:.1%}

        Agent Results:
        {json.dumps(synthesis_context, indent=2, default=str)}

        Aggregation Strategy:
        - Method: {strategy.synthesis_method}
        - Include Sources: {strategy.include_sources}
        - Include Confidence: {strategy.include_confidence}
        - Include Risks: {strategy.include_risks}

        Generate a structured response that:
        1. Directly addresses the user's query
        2. Synthesizes insights from all available agent results
        3. Provides clear sourcing and attribution
        4. Includes confidence assessments and limitations
        5. Offers actionable recommendations where appropriate

        Response should be comprehensive yet accessible, with clear section headings and logical flow.
        """

        response = await self.invoke_llm(
            [
                SystemMessage(
                    content="You are an expert financial response synthesizer."
                ),
                HumanMessage(content=synthesis_prompt),
            ]
        )

        return response.content

    def _prepare_synthesis_context(
        self, organized_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Prepare synthesis context from organized results.

        Args:
            organized_results: Organized agent results

        Returns:
            Synthesis context
        """
        context = {}

        # Include key insights from each agent
        for agent_name, result in organized_results["agent_results"].items():
            if agent_name == "analysis" and isinstance(result, list):
                # Extract insights from analysis results
                insights = []
                for analysis in result:
                    if hasattr(analysis, "insights"):
                        insights.extend(analysis.insights)
                if insights:
                    context[f"{agent_name}_insights"] = insights[
                        :5
                    ]  # Top 5 insights

            elif agent_name == "prediction" and isinstance(result, list):
                # Extract key predictions
                predictions = []
                for pred in result:
                    if hasattr(pred, "predicted_value") and hasattr(
                        pred, "prediction_type"
                    ):
                        predictions.append(
                            {
                                "type": pred.prediction_type,
                                "value": pred.predicted_value,
                                "confidence": pred.confidence_score,
                                "model": pred.model_used,
                            }
                        )
                if predictions:
                    context[f"{agent_name}_forecasts"] = predictions

            elif agent_name in ["retrieval", "search"] and hasattr(
                result, "results"
            ):
                # Extract key findings from search results
                key_findings = [
                    r.content[:200] + "..." for r in result.results[:3]
                ]
                if key_findings:
                    context[f"{agent_name}_findings"] = key_findings

        # Add overall context
        context["overall_confidence"] = organized_results[
            "confidence_assessment"
        ]

        return context

    async def _generate_recommendations(
        self,
        query: str,
        organized_results: Dict[str, Any],
        synthesized_response: str,
    ) -> List[str]:
        """Generate follow-up recommendations.

        Args:
            query: Original query
            organized_results: Organized agent results
            synthesized_response: Synthesized response

        Returns:
            List of recommendations
        """
        recommendation_prompt = f"""
        Based on this financial analysis, generate actionable follow-up recommendations:

        Original Query: "{query}"
        Synthesized Response (first 500 chars): "{synthesized_response[:500]}..."
        Overall Confidence: {organized_results['confidence_assessment']['overall_confidence']:.1%}

        Provide 3-5 specific, actionable recommendations for:
        1. Next steps for deeper analysis
        2. Additional data sources to consider
        3. Risk management strategies
        4. Monitoring and follow-up actions

        Recommendations should be practical and directly related to the analysis provided.
        """

        try:
            response = await self.invoke_llm(
                [
                    SystemMessage(
                        content="You are a financial recommendations expert."
                    ),
                    HumanMessage(content=recommendation_prompt),
                ]
            )

            # Parse recommendations from response
            recommendations_text = response.content
            recommendations = [
                rec.strip()
                for rec in recommendations_text.split("\n")
                if rec.strip() and not rec.strip().startswith("#")
            ]

            return recommendations[:5]  # Limit to 5 recommendations

        except Exception as e:
            self.logger.warning(
                "Recommendation generation failed", error=str(e)
            )
            return [
                "Consider consulting with a financial advisor for personalized advice",
                "Monitor market conditions regularly for updates",
                "Review additional sources for comprehensive analysis",
            ]

    async def _create_final_response(
        self,
        synthesized_response: str,
        recommendations: List[str],
        strategy: AggregationStrategy,
    ) -> str:
        """Create the final structured response.

        Args:
            synthesized_response: Core synthesized response
            recommendations: Follow-up recommendations
            strategy: Aggregation strategy

        Returns:
            Final structured response
        """
        # Structure the final response
        final_parts = []

        # Add synthesized response
        final_parts.append(synthesized_response)

        # Add recommendations if they exist
        if recommendations:
            final_parts.append("\n\n## Recommendations\n\n")
            for i, rec in enumerate(recommendations, 1):
                final_parts.append(f"{i}. {rec}\n")

        # Add confidence disclosure
        if strategy.include_confidence:
            confidence_note = (
                "\n\n## Confidence & Limitations\n\n"
                "This analysis is based on available data and AI-generated insights. "
                "While we strive for accuracy, financial predictions involve inherent uncertainties. "
                "Always verify critical information and consider multiple sources before making decisions."
            )
            final_parts.append(confidence_note)

        # Combine all parts
        final_response = "".join(final_parts)

        # Ensure response length limits
        if (
            len(final_response)
            > self.aggregation_config["max_response_length"]
        ):
            # Truncate intelligently
            final_response = final_response[
                : self.aggregation_config["max_response_length"] - 200
            ]
            final_response += (
                "\n\n[Response truncated due to length constraints]"
            )

        return final_response

    async def _create_fallback_response(
        self, query: str, error_message: str
    ) -> str:
        """Create a fallback response when processing fails.

        Args:
            query: Original query
            error_message: Error that occurred

        Returns:
            Fallback response
        """
        return f"""
I apologize, but I encountered an issue while processing your financial analysis request for "{query}".

**Error Details:** {error_message}

**What happened:** Our multi-agent analysis system experienced a technical difficulty.

**Recommendations:**
1. Please try rephrasing your question
2. Consider breaking down complex queries into simpler components
3. Contact support if the issue persists

**Alternative approach:** You may want to consult directly with financial professionals or use traditional financial analysis tools for this specific query.

We appreciate your patience and are continuously working to improve our system.
        """

    def _extract_all_sources(
        self, organized_results: Dict[str, Any]
    ) -> List[str]:
        """Extract all unique sources from agent results.

        Args:
            organized_results: Organized agent results

        Returns:
            List of unique sources
        """
        sources = set()

        for agent_name, result in organized_results["agent_results"].items():
            if hasattr(result, "data_sources"):
                sources.update(result.data_sources)
            elif hasattr(result, "sources_used"):
                sources.update(result.sources_used)
            elif hasattr(result, "results") and hasattr(result, "results"):
                for r in result.results:
                    if hasattr(r, "metadata") and hasattr(
                        r.metadata, "source"
                    ):
                        sources.add(r.metadata.source)

        return sorted(list(sources))

    async def explain_aggregation_methodology(
        self, query: str, query_type: QueryType
    ) -> str:
        """Explain the aggregation methodology for a given query.

        Args:
            query: User query
            query_type: Type of query

        Returns:
            Explanation of aggregation methodology
        """
        methodology_prompt = f"""
        Explain how our multi-agent system would synthesize responses for this query:

        Query: "{query}"
        Query Type: {query_type.value}

        Provide a detailed explanation of:
        1. How results from different agents would be combined
        2. What prioritization strategy would be used
        3. How conflicting information would be resolved
        4. How confidence levels would be calculated
        5. What the final response structure would look like
        """

        response = await self.invoke_llm(
            [
                SystemMessage(
                    content="You are a multi-agent system methodology expert."
                ),
                HumanMessage(content=methodology_prompt),
            ]
        )

        return response.content

    def get_aggregation_statistics(self) -> Dict[str, Any]:
        """Get statistics about aggregation operations.

        Returns:
            Dictionary with aggregation statistics
        """
        return {
            "agent_name": self.name,
            "aggregation_config": self.aggregation_config,
            "supported_synthesis_methods": [
                "comprehensive",
                "concise",
                "detailed",
            ],
            "response_capabilities": [
                "structured_output",
                "confidence_assessment",
                "source_attribution",
                "recommendation_generation",
            ],
            "metrics": self.get_metrics_summary(),
        }
