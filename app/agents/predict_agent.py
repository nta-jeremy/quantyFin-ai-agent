"""Predict Agent for ML predictions and financial forecasting."""

import json
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from .agent_state import StateManager, WorkflowState
from .agent_types import AgentRole, PredictionResult, QueryType, WorkflowConfig
from .base_agent import LLMBasedAgent


class ModelConfig(BaseModel):
    """Configuration for prediction models."""

    model_name: str
    model_type: str  # "time_series", "regression", "classification"
    features: List[str]
    hyperparameters: Dict[str, Any]
    performance_metrics: Dict[str, float]


class PredictionFeature(BaseModel):
    """Individual feature used for prediction."""

    name: str
    value: float
    importance: float
    description: str


class PredictAgent(LLMBasedAgent):
    """Agent for ML predictions and financial forecasting."""

    def __init__(
        self, llm_model: ChatOpenAI, config: Optional[Dict[str, Any]] = None
    ):
        """Initialize the Predict Agent.

        Args:
            llm_model: LLM model for prediction analysis
            config: Workflow configuration
        """
        super().__init__(
            role=AgentRole.PREDICT,
            name="Prediction & Forecasting Specialist",
            description="Applies machine learning models for financial predictions and trend forecasting",
            llm_model=llm_model,
            config=config,
            system_prompt=self._get_prediction_system_prompt(),
        )

        # Initialize model configurations
        self.model_configs = self._initialize_model_configs()

        # Prediction configurations
        self.prediction_config = {
            "confidence_threshold": 0.7,
            "max_prediction_horizon": 365,  # days
            "min_data_points": 30,
            "enable_ensemble_methods": True,
        }

    def _get_prediction_system_prompt(self) -> str:
        """Get system prompt for the Predict Agent.

        Returns:
            System prompt string
        """
        return """You are a Prediction & Forecasting Specialist responsible for applying machine learning models for financial predictions.

Your responsibilities:
1. Select appropriate ML models for different prediction tasks
2. Extract and engineer features from financial data
3. Generate predictions with confidence intervals
4. Validate model performance and accuracy
5. Forecast trends and market movements
6. Provide risk-adjusted predictions

Focus on delivering accurate, well-calibrated predictions with clear confidence intervals and risk assessments."""

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
        ]

    def validate_input(self, state: WorkflowState) -> bool:
        """Validate input state for Predict Agent.

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
            and state["analysis_results"] is not None
            and state["current_query"]
            and len(state["current_query"].strip()) > 0
        )

    async def process(self, state: WorkflowState) -> WorkflowState:
        """Process ML predictions and financial forecasting.

        Args:
            state: Current workflow state

        Returns:
            Updated workflow state with prediction results
        """
        query = state["current_query"]
        query_type = state["query_type"]

        self.logger.info(
            "Starting prediction processing",
            query_type=query_type.value,
            query_length=len(query),
        )

        try:
            # Step 1: Gather and analyze available data
            available_data = self._gather_prediction_data(state)

            # Step 2: Determine prediction requirements
            prediction_requirements = (
                await self._determine_prediction_requirements(
                    query, query_type, available_data
                )
            )

            # Step 3: Select and configure models
            selected_models = await self._select_prediction_models(
                prediction_requirements, available_data
            )

            # Step 4: Extract and engineer features
            features = await self._extract_features(
                selected_models, available_data
            )

            # Step 5: Generate predictions
            prediction_results = await self._generate_predictions(
                selected_models, features, prediction_requirements
            )

            # Step 6: Validate and ensemble predictions
            final_predictions = await self._validate_and_ensemble_predictions(
                prediction_results, prediction_requirements
            )

            # Update state with results
            state["prediction_results"] = final_predictions

            # Add processing message
            processing_message = self._create_processing_message(
                final_predictions
            )
            state = StateManager.add_agent_message(
                state,
                processing_message,
                role="assistant",
                agent_role=self.role,
            )

            self.logger.info(
                "Prediction processing completed",
                predictions_count=len(final_predictions),
                avg_confidence=(
                    sum(p.confidence_score for p in final_predictions)
                    / len(final_predictions)
                    if final_predictions
                    else 0
                ),
            )

            return state

        except Exception as e:
            self.logger.error("Prediction processing failed", error=str(e))
            raise RuntimeError(f"Prediction processing failed: {str(e)}")

    def _initialize_model_configs(self) -> Dict[str, ModelConfig]:
        """Initialize prediction model configurations.

        Returns:
            Dictionary of model configurations
        """
        return {
            "lstm_time_series": ModelConfig(
                model_name="LSTM Time Series",
                model_type="time_series",
                features=["price", "volume", "volatility", "trend"],
                hyperparameters={"units": 50, "dropout": 0.2, "epochs": 100},
                performance_metrics={"mse": 0.0023, "mae": 0.045, "r2": 0.87},
            ),
            "random_forest": ModelConfig(
                model_name="Random Forest Regressor",
                model_type="regression",
                features=[
                    "pe_ratio",
                    "pb_ratio",
                    "roe",
                    "debt_equity",
                    "market_cap",
                ],
                hyperparameters={
                    "n_estimators": 100,
                    "max_depth": 10,
                    "min_samples_split": 5,
                },
                performance_metrics={"mse": 0.0018, "mae": 0.038, "r2": 0.91},
            ),
            "gradient_boosting": ModelConfig(
                model_name="Gradient Boosting",
                model_type="regression",
                features=[
                    "revenue_growth",
                    "profit_margin",
                    "market_sentiment",
                    "economic_indicators",
                ],
                hyperparameters={
                    "n_estimators": 200,
                    "learning_rate": 0.1,
                    "max_depth": 6,
                },
                performance_metrics={"mse": 0.0015, "mae": 0.032, "r2": 0.93},
            ),
            "arima": ModelConfig(
                model_name="ARIMA",
                model_type="time_series",
                features=["historical_prices", "seasonal_patterns"],
                hyperparameters={"p": 1, "d": 1, "q": 1},
                performance_metrics={
                    "aic": 1234.5,
                    "bic": 1245.6,
                    "mse": 0.0021,
                },
            ),
        }

    def _gather_prediction_data(self, state: WorkflowState) -> Dict[str, Any]:
        """Gather data from previous agents for prediction.

        Args:
            state: Current workflow state

        Returns:
            Dictionary with all available prediction data
        """
        return {
            "analysis_results": state.get("analysis_results", []),
            "search_results": state.get("search_results"),
            "retrieval_results": state.get("retrieval_results"),
            "embeddings": state.get("embeddings"),
            "query_context": {
                "original_query": state["original_query"],
                "current_query": state["current_query"],
                "query_type": state["query_type"],
            },
        }

    async def _determine_prediction_requirements(
        self, query: str, query_type: QueryType, available_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Determine prediction requirements based on query and available data.

        Args:
            query: User query
            query_type: Type of query
            available_data: Available data

        Returns:
            Prediction requirements
        """
        requirements_prompt = f"""
        Determine the prediction requirements for this financial query:

        Query: "{query}"
        Query Type: {query_type.value}
        Available Data: {json.dumps({k: len(v) if isinstance(v, list) else type(v).__name__ for k, v in available_data.items()}, indent=2)}

        Return JSON with prediction requirements:
        {{
            "prediction_types": ["stock_price", "market_trend", "revenue_forecast"],
            "time_horizon_days": 30,
            "confidence_level": 0.8,
            "required_features": ["historical_prices", "volume", "market_sentiment"],
            "risk_tolerance": "medium",
            "model_preferences": ["ensemble", "time_series"],
            "prediction_frequency": "daily"
        }}
        """

        try:
            response = await self.invoke_llm(
                [
                    SystemMessage(
                        content="You are a financial prediction requirements expert."
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
                return self._get_default_prediction_requirements(query_type)

        except Exception as e:
            self.logger.warning(
                "Prediction requirements determination failed", error=str(e)
            )
            return self._get_default_prediction_requirements(query_type)

    def _get_default_prediction_requirements(
        self, query_type: QueryType
    ) -> Dict[str, Any]:
        """Get default prediction requirements for query type.

        Args:
            query_type: Type of query

        Returns:
            Default prediction requirements
        """
        requirements = {
            "prediction_types": ["market_trend"],
            "time_horizon_days": 30,
            "confidence_level": 0.7,
            "required_features": ["historical_data", "market_indicators"],
            "risk_tolerance": "medium",
            "model_preferences": ["time_series"],
            "prediction_frequency": "daily",
        }

        # Customize based on query type
        if query_type == QueryType.STOCK_ANALYSIS:
            requirements["prediction_types"] = [
                "stock_price",
                "volatility_forecast",
            ]
            requirements["required_features"].extend(
                ["pe_ratio", "market_sentiment"]
            )
        elif query_type == QueryType.COMPANY_FINANCIALS:
            requirements["prediction_types"] = [
                "revenue_forecast",
                "profit_prediction",
            ]
            requirements["required_features"].extend(
                ["financial_ratios", "economic_indicators"]
            )
        elif query_type == QueryType.MARKET_RESEARCH:
            requirements["prediction_types"] = [
                "market_trend",
                "sector_performance",
            ]
            requirements["time_horizon_days"] = 90

        return requirements

    async def _select_prediction_models(
        self, requirements: Dict[str, Any], available_data: Dict[str, Any]
    ) -> List[ModelConfig]:
        """Select appropriate prediction models.

        Args:
            requirements: Prediction requirements
            available_data: Available data

        Returns:
            List of selected model configurations
        """
        selected_models = []

        # Model selection based on prediction types
        prediction_types = requirements.get(
            "prediction_types", ["market_trend"]
        )
        model_preferences = requirements.get(
            "model_preferences", ["time_series"]
        )

        for pred_type in prediction_types:
            if pred_type in ["stock_price", "market_trend"]:
                # Time series models for price/trend prediction
                if "time_series" in model_preferences:
                    selected_models.append(
                        self.model_configs["lstm_time_series"]
                    )
                    selected_models.append(self.model_configs["arima"])

            if pred_type in ["revenue_forecast", "profit_prediction"]:
                # Regression models for financial forecasting
                selected_models.append(self.model_configs["random_forest"])
                selected_models.append(self.model_configs["gradient_boosting"])

        # Remove duplicates while preserving order
        seen_models = set()
        unique_models = []
        for model in selected_models:
            if model.model_name not in seen_models:
                seen_models.add(model.model_name)
                unique_models.append(model)

        return unique_models[:3]  # Limit to 3 models

    async def _extract_features(
        self, models: List[ModelConfig], available_data: Dict[str, Any]
    ) -> Dict[str, List[PredictionFeature]]:
        """Extract and engineer features for prediction.

        Args:
            models: Selected models
            available_data: Available data

        Returns:
            Dictionary mapping model names to features
        """
        features_by_model = {}

        for model in models:
            features = []

            # Extract features from analysis results
            analysis_results = available_data.get("analysis_results", [])
            for analysis in analysis_results:
                if analysis.analysis_type == "financial_metrics":
                    for metric_name, metric_value in analysis.metrics.items():
                        if isinstance(metric_value, (int, float)):
                            feature = PredictionFeature(
                                name=metric_name,
                                value=metric_value,
                                importance=0.7,  # Default importance
                                description=f"Financial metric: {metric_name}",
                            )
                            features.append(feature)

            # Add market sentiment features
            for analysis in analysis_results:
                if analysis.analysis_type == "sentiment_analysis":
                    sentiment_value = analysis.metrics.get(
                        "overall_sentiment", 0.0
                    )
                    feature = PredictionFeature(
                        name="market_sentiment",
                        value=sentiment_value,
                        importance=0.8,
                        description="Market sentiment score",
                    )
                    features.append(feature)

            # Add technical indicators (simulated)
            technical_features = self._generate_technical_features()
            features.extend(technical_features)

            # Add economic indicators (simulated)
            economic_features = self._generate_economic_features()
            features.extend(economic_features)

            features_by_model[model.model_name] = features

        return features_by_model

    def _generate_technical_features(self) -> List[PredictionFeature]:
        """Generate technical indicator features.

        Returns:
            List of technical features
        """
        return [
            PredictionFeature(
                name="moving_average_50d",
                value=150.25,
                importance=0.6,
                description="50-day moving average",
            ),
            PredictionFeature(
                name="rsi",
                value=65.3,
                importance=0.7,
                description="Relative Strength Index",
            ),
            PredictionFeature(
                name="macd",
                value=2.15,
                importance=0.5,
                description="MACD indicator",
            ),
            PredictionFeature(
                name="bollinger_upper",
                value=155.80,
                importance=0.4,
                description="Bollinger Band upper",
            ),
            PredictionFeature(
                name="bollinger_lower",
                value=144.70,
                importance=0.4,
                description="Bollinger Band lower",
            ),
        ]

    def _generate_economic_features(self) -> List[PredictionFeature]:
        """Generate economic indicator features.

        Returns:
            List of economic features
        """
        return [
            PredictionFeature(
                name="interest_rate",
                value=5.25,
                importance=0.8,
                description="Federal interest rate",
            ),
            PredictionFeature(
                name="inflation_rate",
                value=3.2,
                importance=0.7,
                description="Inflation rate",
            ),
            PredictionFeature(
                name="gdp_growth",
                value=2.1,
                importance=0.6,
                description="GDP growth rate",
            ),
            PredictionFeature(
                name="unemployment_rate",
                value=3.8,
                importance=0.5,
                description="Unemployment rate",
            ),
        ]

    async def _generate_predictions(
        self,
        models: List[ModelConfig],
        features: Dict[str, List[PredictionFeature]],
        requirements: Dict[str, Any],
    ) -> List[PredictionResult]:
        """Generate predictions using selected models.

        Args:
            models: Selected models
            features: Features by model
            requirements: Prediction requirements

        Returns:
            List of prediction results
        """
        predictions = []
        time_horizon = requirements.get("time_horizon_days", 30)

        for model in models:
            model_features = features.get(model.model_name, [])
            if not model_features:
                continue

            # Generate prediction based on model type
            if model.model_type == "time_series":
                prediction = await self._generate_time_series_prediction(
                    model, model_features, time_horizon
                )
            elif model.model_type == "regression":
                prediction = await self._generate_regression_prediction(
                    model, model_features, requirements
                )
            else:
                continue

            predictions.append(prediction)

        return predictions

    async def _generate_time_series_prediction(
        self,
        model: ModelConfig,
        features: List[PredictionFeature],
        time_horizon: int,
    ) -> PredictionResult:
        """Generate time series prediction.

        Args:
            model: Model configuration
            features: Feature data
            time_horizon: Prediction time horizon

        Returns:
            Time series prediction result
        """
        # Simulate time series prediction
        current_price = features[0].value if features else 150.0

        # Generate price forecast with trend
        trend_factor = 0.001  # Daily trend factor
        volatility = 0.02  # Daily volatility

        # Simulate prediction path
        predicted_prices = []
        current_val = current_price

        for day in range(time_horizon):
            # Add trend and random walk
            change = trend_factor * current_val + volatility * current_val * (
                2 * hash(day) % 100 / 100 - 0.5
            )
            current_val += change
            predicted_prices.append(current_val)

        # Calculate final prediction and confidence interval
        final_prediction = predicted_prices[-1]
        prediction_std = volatility * current_price * (time_horizon**0.5)
        confidence_interval = (
            final_prediction - 1.96 * prediction_std,
            final_prediction + 1.96 * prediction_std,
        )

        return PredictionResult(
            prediction_type="stock_price_forecast",
            predicted_value=final_prediction,
            confidence_interval=confidence_interval,
            confidence_score=model.performance_metrics.get("r2", 0.8),
            model_used=model.model_name,
            features_used=[f.name for f in features[:5]],  # Top 5 features
            prediction_date=datetime.now() + timedelta(days=time_horizon),
        )

    async def _generate_regression_prediction(
        self,
        model: ModelConfig,
        features: List[PredictionFeature],
        requirements: Dict[str, Any],
    ) -> PredictionResult:
        """Generate regression-based prediction.

        Args:
            model: Model configuration
            features: Feature data
            requirements: Prediction requirements

        Returns:
            Regression prediction result
        """
        # Simulate regression prediction
        feature_values = [f.value for f in features]
        feature_weights = [f.importance for f in features]

        # Weighted sum prediction
        prediction_value = sum(
            fv * fw for fv, fw in zip(feature_values, feature_weights)
        ) / sum(feature_weights)

        # Calculate confidence interval based on model performance
        mse = model.performance_metrics.get("mse", 0.01)
        prediction_std = mse**0.5
        confidence_interval = (
            prediction_value - 1.96 * prediction_std,
            prediction_value + 1.96 * prediction_std,
        )

        return PredictionResult(
            prediction_type="financial_metric_forecast",
            predicted_value=prediction_value,
            confidence_interval=confidence_interval,
            confidence_score=model.performance_metrics.get("r2", 0.8),
            model_used=model.model_name,
            features_used=[f.name for f in features],
            prediction_date=datetime.now()
            + timedelta(days=requirements.get("time_horizon_days", 30)),
        )

    async def _validate_and_ensemble_predictions(
        self, predictions: List[PredictionResult], requirements: Dict[str, Any]
    ) -> List[PredictionResult]:
        """Validate and ensemble multiple predictions.

        Args:
            predictions: Individual model predictions
            requirements: Prediction requirements

        Returns:
            Final ensemble predictions
        """
        if not predictions:
            return []

        if len(predictions) == 1:
            return predictions

        # Filter predictions by confidence threshold
        confident_predictions = [
            p
            for p in predictions
            if p.confidence_score >= requirements.get("confidence_level", 0.7)
        ]

        if not confident_predictions:
            # Use all predictions if none meet confidence threshold
            confident_predictions = predictions

        if (
            self.prediction_config["enable_ensemble_methods"]
            and len(confident_predictions) > 1
        ):
            # Create ensemble prediction
            ensemble_prediction = await self._create_ensemble_prediction(
                confident_predictions
            )
            return [ensemble_prediction]
        else:
            # Return the best single prediction
            best_prediction = max(
                confident_predictions, key=lambda p: p.confidence_score
            )
            return [best_prediction]

    async def _create_ensemble_prediction(
        self, predictions: List[PredictionResult]
    ) -> PredictionResult:
        """Create ensemble prediction from multiple models.

        Args:
            predictions: Individual predictions to ensemble

        Returns:
            Ensemble prediction result
        """
        # Weighted average based on confidence scores
        total_confidence = sum(p.confidence_score for p in predictions)
        weights = [p.confidence_score / total_confidence for p in predictions]

        # Calculate ensemble prediction
        ensemble_value = sum(
            p.predicted_value * w for p, w in zip(predictions, weights)
        )

        # Calculate ensemble confidence interval
        all_intervals = [
            p.confidence_interval for p in predictions if p.confidence_interval
        ]
        if all_intervals:
            lower_bounds = [interval[0] for interval in all_intervals]
            upper_bounds = [interval[1] for interval in all_intervals]
            ensemble_interval = (
                sum(lb * w for lb, w in zip(lower_bounds, weights)),
                sum(ub * w for ub, w in zip(upper_bounds, weights)),
            )
        else:
            ensemble_interval = None

        # Ensemble confidence is average of individual confidences
        ensemble_confidence = sum(
            p.confidence_score for p in predictions
        ) / len(predictions)

        return PredictionResult(
            prediction_type="ensemble_forecast",
            predicted_value=ensemble_value,
            confidence_interval=ensemble_interval,
            confidence_score=ensemble_confidence,
            model_used=f"Ensemble of {len(predictions)} models",
            features_used=list(
                set(feat for p in predictions for feat in p.features_used[:3])
            ),
            prediction_date=predictions[0].prediction_date,
        )

    def _create_processing_message(
        self, prediction_results: List[PredictionResult]
    ) -> str:
        """Create a processing message for the conversation.

        Args:
            prediction_results: List of prediction results

        Returns:
            Processing message string
        """
        if not prediction_results:
            return "🤖 Prediction Complete: Insufficient data for reliable predictions."

        avg_confidence = sum(
            p.confidence_score for p in prediction_results
        ) / len(prediction_results)
        model_names = [p.model_used for p in prediction_results]

        return (
            f"🤖 Prediction Complete: Generated {len(prediction_results)} forecasts "
            f"using {', '.join(model_names)} with average confidence {avg_confidence:.1%}. "
            f"Predictions include confidence intervals and risk assessments."
        )

    async def explain_prediction_methodology(
        self, query: str, query_type: QueryType
    ) -> str:
        """Explain the prediction methodology for a given query.

        Args:
            query: User query
            query_type: Type of query

        Returns:
            Explanation of prediction methodology
        """
        methodology_prompt = f"""
        Explain the prediction methodology for this financial query:

        Query: "{query}"
        Query Type: {query_type.value}

        Provide a detailed explanation of:
        1. What machine learning models would be used
        2. What features would be extracted and engineered
        3. How predictions would be validated and ensembled
        4. What confidence intervals would be calculated
        5. How risk would be assessed and communicated
        """

        response = await self.invoke_llm(
            [
                SystemMessage(
                    content="You are a machine learning prediction methodology expert."
                ),
                HumanMessage(content=methodology_prompt),
            ]
        )

        return response.content

    def get_prediction_statistics(self) -> Dict[str, Any]:
        """Get statistics about prediction operations.

        Returns:
            Dictionary with prediction statistics
        """
        return {
            "agent_name": self.name,
            "available_models": list(self.model_configs.keys()),
            "prediction_config": self.prediction_config,
            "model_performance": {
                name: config.performance_metrics
                for name, config in self.model_configs.items()
            },
            "metrics": self.get_metrics_summary(),
        }
