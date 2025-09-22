"""
Rate limiting and retry logic service implementation.

This module provides the application layer implementation for rate limiting
and retry mechanisms following hexagonal architecture principles.
"""

import asyncio
import logging
import random
import time
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from app.core.domain.data_source_models import DataSource, DataSourceConfig
from app.core.domain.historical_models import (
    DataSourceUnavailableError,
    HistoricalDataError,
    NetworkError,
    RateLimitExceededError,
    TimeoutError,
)
from app.infrastructure.cache.cache_adapter import CacheAdapter

logger = logging.getLogger(__name__)


class RateLimitStrategy(Enum):
    """Rate limiting strategies."""

    TOKEN_BUCKET = "token_bucket"  # Token bucket algorithm
    SLIDING_WINDOW = "sliding_window"  # Sliding window counter
    FIXED_WINDOW = "fixed_window"  # Fixed window counter
    LEAKY_BUCKET = "leaky_bucket"  # Leaky bucket algorithm


class RetryStrategy(Enum):
    """Retry strategies."""

    EXPONENTIAL_BACKOFF = (
        "exponential_backoff"  # Exponential backoff with jitter
    )
    LINEAR_BACKOFF = "linear_backoff"  # Linear backoff
    FIXED_DELAY = "fixed_delay"  # Fixed delay between retries
    FIBONACCI_BACKOFF = "fibonacci_backoff"  # Fibonacci sequence backoff


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Circuit is open, fast fail
    HALF_OPEN = "half_open"  # Testing if service is restored


class RateLimitRule:
    """Rate limiting rule configuration."""

    def __init__(
        self,
        key: str,
        max_requests: int,
        time_window_seconds: int,
        strategy: RateLimitStrategy = RateLimitStrategy.TOKEN_BUCKET,
        burst_limit: Optional[int] = None,
    ):
        self.key = key
        self.max_requests = max_requests
        self.time_window_seconds = time_window_seconds
        self.strategy = strategy
        self.burst_limit = burst_limit or max_requests


class RetryPolicy:
    """Retry policy configuration."""

    def __init__(
        self,
        max_retries: int,
        strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF,
        base_delay_ms: int = 100,
        max_delay_ms: int = 30000,
        jitter_ms: int = 100,
        retryable_exceptions: Tuple[Exception, ...] = (
            NetworkError,
            TimeoutError,
            RateLimitExceededError,
        ),
    ):
        self.max_retries = max_retries
        self.strategy = strategy
        self.base_delay_ms = base_delay_ms
        self.max_delay_ms = max_delay_ms
        self.jitter_ms = jitter_ms
        self.retryable_exceptions = retryable_exceptions


class CircuitBreakerConfig:
    """Circuit breaker configuration."""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout_seconds: int = 60,
        expected_exception_types: Tuple[Exception, ...] = (
            NetworkError,
            TimeoutError,
            DataSourceUnavailableError,
        ),
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout_seconds = recovery_timeout_seconds
        self.expected_exception_types = expected_exception_types


class RateLimitService:
    """Service for rate limiting and retry logic."""

    def __init__(
        self,
        cache_adapter: CacheAdapter,
        default_rate_limit: RateLimitRule,
        default_retry_policy: RetryPolicy,
        circuit_breaker_config: CircuitBreakerConfig,
    ):
        """Initialize rate limit service."""
        self.cache_adapter = cache_adapter
        self.default_rate_limit = default_rate_limit
        self.default_retry_policy = default_retry_policy
        self.circuit_breaker_config = circuit_breaker_config

        # Rate limit rules by key
        self.rate_limit_rules: Dict[str, RateLimitRule] = {
            "default": default_rate_limit
        }

        # Circuit breaker state per service/data source
        self.circuit_states: Dict[str, Dict[str, Any]] = {}

        # Metrics
        self.metrics = {
            "total_requests": 0,
            "allowed_requests": 0,
            "blocked_requests": 0,
            "retry_attempts": 0,
            "successful_retries": 0,
            "circuit_trips": 0,
            "circuit_resets": 0,
        }

    async def initialize(self) -> None:
        """Initialize rate limit service."""
        await self.cache_adapter.initialize()
        logger.info("Rate limit service initialized")

    async def close(self) -> None:
        """Close rate limit service."""
        await self.cache_adapter.close()
        logger.info("Rate limit service closed")

    def add_rate_limit_rule(self, rule: RateLimitRule) -> None:
        """Add a rate limiting rule."""
        self.rate_limit_rules[rule.key] = rule
        logger.info(f"Added rate limit rule: {rule.key}")

    def get_rate_limit_rule(self, key: str) -> RateLimitRule:
        """Get rate limit rule for key."""
        return self.rate_limit_rules.get(key, self.default_rate_limit)

    async def check_rate_limit(
        self, key: str, rule_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """Check if request is allowed under rate limit."""
        rule = self.get_rate_limit_rule(rule_key or "default")
        cache_key = f"rate_limit:{rule.key}:{key}"

        self.metrics["total_requests"] += 1

        try:
            if rule.strategy == RateLimitStrategy.TOKEN_BUCKET:
                result = await self._token_bucket_check(cache_key, rule)
            elif rule.strategy == RateLimitStrategy.SLIDING_WINDOW:
                result = await self._sliding_window_check(cache_key, rule)
            elif rule.strategy == RateLimitStrategy.FIXED_WINDOW:
                result = await self._fixed_window_check(cache_key, rule)
            elif rule.strategy == RateLimitStrategy.LEAKY_BUCKET:
                result = await self._leaky_bucket_check(cache_key, rule)
            else:
                raise ValueError(
                    f"Unknown rate limit strategy: {rule.strategy}"
                )

            if result["allowed"]:
                self.metrics["allowed_requests"] += 1
            else:
                self.metrics["blocked_requests"] += 1

            return result

        except Exception as e:
            logger.error(f"Rate limit check error: {e}")
            # Allow request on error to prevent service disruption
            self.metrics["allowed_requests"] += 1
            return {
                "allowed": True,
                "remaining": rule.max_requests,
                "reset_time": 0,
            }

    async def _token_bucket_check(
        self, cache_key: str, rule: RateLimitRule
    ) -> Dict[str, Any]:
        """Token bucket rate limiting algorithm."""
        current_time = time.time()

        # Get current bucket state
        bucket_data = await self.cache_adapter.get(cache_key)
        if not bucket_data:
            bucket_data = {
                "tokens": rule.max_requests,
                "last_refill": current_time,
                "burst_tokens": rule.burst_limit,
            }
        else:
            # Ensure bucket_data is a dictionary
            if isinstance(bucket_data, dict):
                pass  # Already a dict
            else:
                # Convert to expected format if it's not
                bucket_data = {
                    "tokens": rule.max_requests,
                    "last_refill": current_time,
                    "burst_tokens": rule.burst_limit,
                }

        # Refill tokens based on time passed
        time_passed = current_time - bucket_data["last_refill"]
        tokens_to_add = time_passed * (
            rule.max_requests / rule.time_window_seconds
        )

        bucket_data["tokens"] = min(
            rule.max_requests, bucket_data["tokens"] + tokens_to_add
        )
        bucket_data["last_refill"] = current_time

        # Check if we can allow this request
        if bucket_data["tokens"] >= 1:
            bucket_data["tokens"] -= 1
            await self.cache_adapter.set(
                cache_key, bucket_data, rule.time_window_seconds
            )

            return {
                "allowed": True,
                "remaining": int(bucket_data["tokens"]),
                "reset_time": int(
                    current_time
                    + (1 - bucket_data["tokens"])
                    * (rule.time_window_seconds / rule.max_requests)
                ),
            }
        else:
            # Use burst tokens if available
            if bucket_data["burst_tokens"] > 0:
                bucket_data["burst_tokens"] -= 1
                await self.cache_adapter.set(
                    cache_key, bucket_data, rule.time_window_seconds
                )

                return {
                    "allowed": True,
                    "remaining": 0,
                    "burst_remaining": int(bucket_data["burst_tokens"]),
                    "reset_time": int(
                        current_time
                        + (rule.time_window_seconds / rule.max_requests)
                    ),
                }

        return {
            "allowed": False,
            "remaining": 0,
            "reset_time": int(
                current_time + (rule.time_window_seconds / rule.max_requests)
            ),
        }

    async def _sliding_window_check(
        self, cache_key: str, rule: RateLimitRule
    ) -> Dict[str, Any]:
        """Sliding window rate limiting algorithm."""
        current_time = time.time()
        window_start = current_time - rule.time_window_seconds

        # Get request timestamps
        request_timestamps = await self.cache_adapter.get(cache_key)
        if not request_timestamps:
            request_timestamps = []

        # Remove old timestamps
        recent_requests = [
            ts for ts in request_timestamps if ts > window_start
        ]

        if len(recent_requests) < rule.max_requests:
            # Allow request
            recent_requests.append(current_time)
            await self.cache_adapter.set(
                cache_key, recent_requests, rule.time_window_seconds
            )

            return {
                "allowed": True,
                "remaining": rule.max_requests - len(recent_requests),
                "reset_time": int(current_time + rule.time_window_seconds),
            }
        else:
            # Block request
            oldest_request = min(recent_requests)
            return {
                "allowed": False,
                "remaining": 0,
                "reset_time": int(oldest_request + rule.time_window_seconds),
            }

    async def _fixed_window_check(
        self, cache_key: str, rule: RateLimitRule
    ) -> Dict[str, Any]:
        """Fixed window rate limiting algorithm."""
        current_time = time.time()
        window_start = (
            int(current_time / rule.time_window_seconds)
            * rule.time_window_seconds
        )
        window_key = f"{cache_key}:{window_start}"

        # Get request count for current window
        request_count = await self.cache_adapter.get(window_key)
        if request_count is None:
            request_count = 0

        if request_count < rule.max_requests:
            # Allow request
            await self.cache_adapter.set(
                window_key, request_count + 1, rule.time_window_seconds
            )

            return {
                "allowed": True,
                "remaining": rule.max_requests - (request_count + 1),
                "reset_time": int(window_start + rule.time_window_seconds),
            }
        else:
            # Block request
            return {
                "allowed": False,
                "remaining": 0,
                "reset_time": int(window_start + rule.time_window_seconds),
            }

    async def _leaky_bucket_check(
        self, cache_key: str, rule: RateLimitRule
    ) -> Dict[str, Any]:
        """Leaky bucket rate limiting algorithm."""
        current_time = time.time()

        # Get bucket state
        bucket_data = await self.cache_adapter.get(cache_key)
        if not bucket_data:
            bucket_data = {"bucket_level": 0.0, "last_leak": current_time}

        # Leak based on time passed
        time_passed = current_time - bucket_data["last_leak"]
        leak_rate = rule.max_requests / rule.time_window_seconds
        bucket_data["bucket_level"] = max(
            0, bucket_data["bucket_level"] - (time_passed * leak_rate)
        )
        bucket_data["last_leak"] = current_time

        if bucket_data["bucket_level"] < rule.max_requests:
            # Allow request
            bucket_data["bucket_level"] += 1
            await self.cache_adapter.set(
                cache_key, bucket_data, rule.time_window_seconds
            )

            return {
                "allowed": True,
                "remaining": int(
                    rule.max_requests - bucket_data["bucket_level"]
                ),
                "reset_time": int(
                    current_time + (bucket_data["bucket_level"] / leak_rate)
                ),
            }
        else:
            # Block request
            return {
                "allowed": False,
                "remaining": 0,
                "reset_time": int(
                    current_time + (bucket_data["bucket_level"] / leak_rate)
                ),
            }

    async def execute_with_retry(
        self,
        func: Callable,
        *args,
        retry_policy: Optional[RetryPolicy] = None,
        circuit_key: Optional[str] = None,
        **kwargs,
    ) -> Any:
        """Execute function with retry logic and circuit breaker."""
        policy = retry_policy or self.default_retry_policy

        for attempt in range(policy.max_retries + 1):
            try:
                # Check circuit breaker if enabled
                if circuit_key:
                    await self._check_circuit_breaker(circuit_key)

                # Execute the function
                result = await func(*args, **kwargs)

                # Record successful retry
                if attempt > 0:
                    self.metrics["successful_retries"] += 1

                return result

            except policy.retryable_exceptions as e:
                self.metrics["retry_attempts"] += 1

                if attempt == policy.max_retries:
                    # Max retries reached
                    if circuit_key:
                        await self._record_circuit_failure(circuit_key)
                    raise e

                # Calculate delay based on retry strategy
                delay_ms = self._calculate_retry_delay(policy, attempt)

                logger.warning(
                    f"Retry attempt {attempt + 1}/{policy.max_retries} after {delay_ms}ms delay. Error: {e}"
                )

                # Wait before retry
                await asyncio.sleep(delay_ms / 1000)

            except Exception as e:
                # Non-retryable exception
                if circuit_key:
                    await self._record_circuit_failure(circuit_key)
                raise e

    def _calculate_retry_delay(self, policy: RetryPolicy, attempt: int) -> int:
        """Calculate retry delay based on strategy."""
        base_delay = policy.base_delay_ms

        if policy.strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            delay = base_delay * (2**attempt)
        elif policy.strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = base_delay * (attempt + 1)
        elif policy.strategy == RetryStrategy.FIXED_DELAY:
            delay = base_delay
        elif policy.strategy == RetryStrategy.FIBONACCI_BACKOFF:
            fib_sequence = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55]
            fib_index = min(attempt, len(fib_sequence) - 1)
            delay = base_delay * fib_sequence[fib_index]
        else:
            delay = base_delay

        # Add jitter
        jitter = random.randint(0, policy.jitter_ms)
        delay += jitter

        # Cap at maximum delay
        return min(delay, policy.max_delay_ms)

    async def _check_circuit_breaker(self, circuit_key: str) -> None:
        """Check circuit breaker state."""
        if circuit_key not in self.circuit_states:
            self.circuit_states[circuit_key] = {
                "state": CircuitState.CLOSED,
                "failure_count": 0,
                "last_failure_time": 0,
                "last_attempt_time": 0,
            }

        state = self.circuit_states[circuit_key]

        if state["state"] == CircuitState.OPEN:
            # Check if recovery timeout has passed
            current_time = time.time()
            if (
                current_time - state["last_failure_time"]
                > self.circuit_breaker_config.recovery_timeout_seconds
            ):
                # Move to half-open state
                state["state"] = CircuitState.HALF_OPEN
                state["last_attempt_time"] = current_time
                logger.info(
                    f"Circuit breaker for {circuit_key} moved to HALF_OPEN"
                )
            else:
                # Circuit is still open
                raise DataSourceUnavailableError(
                    f"Circuit breaker is OPEN for {circuit_key}",
                    circuit_key,
                    None,
                )

    async def _record_circuit_failure(self, circuit_key: str) -> None:
        """Record failure for circuit breaker."""
        if circuit_key not in self.circuit_states:
            self.circuit_states[circuit_key] = {
                "state": CircuitState.CLOSED,
                "failure_count": 0,
                "last_failure_time": 0,
                "last_attempt_time": 0,
            }

        state = self.circuit_states[circuit_key]
        current_time = time.time()

        state["failure_count"] += 1
        state["last_failure_time"] = current_time

        # Check if we should trip the circuit
        if (
            state["state"] == CircuitState.CLOSED
            and state["failure_count"]
            >= self.circuit_breaker_config.failure_threshold
        ):
            state["state"] = CircuitState.OPEN
            self.metrics["circuit_trips"] += 1
            logger.warning(
                f"Circuit breaker for {circuit_key} tripped to OPEN"
            )
        elif state["state"] == CircuitState.HALF_OPEN:
            # Failed in half-open state, return to open
            state["state"] = CircuitState.OPEN
            logger.warning(
                f"Circuit breaker for {circuit_key} returned to OPEN from HALF_OPEN"
            )

    async def record_circuit_success(self, circuit_key: str) -> None:
        """Record success for circuit breaker."""
        if circuit_key in self.circuit_states:
            state = self.circuit_states[circuit_key]

            if state["state"] == CircuitState.HALF_OPEN:
                # Success in half-open, reset to closed
                state["state"] = CircuitState.CLOSED
                state["failure_count"] = 0
                self.metrics["circuit_resets"] += 1
                logger.info(
                    f"Circuit breaker for {circuit_key} reset to CLOSED"
                )

    async def get_circuit_state(self, circuit_key: str) -> Dict[str, Any]:
        """Get current circuit breaker state."""
        if circuit_key not in self.circuit_states:
            return {"state": CircuitState.CLOSED.value, "failure_count": 0}

        state = self.circuit_states[circuit_key].copy()
        state["state"] = state["state"].value
        return state

    async def get_metrics(self) -> Dict[str, Any]:
        """Get rate limiting and retry metrics."""
        circuit_metrics = {}
        for key, state in self.circuit_states.items():
            circuit_metrics[key] = {
                "state": state["state"].value,
                "failure_count": state["failure_count"],
                "last_failure_time": state["last_failure_time"],
            }

        return {
            "rate_limit_metrics": self.metrics.copy(),
            "circuit_breakers": circuit_metrics,
            "total_rules": len(self.rate_limit_rules),
            "timestamp": datetime.now(timezone.utc),
        }

    async def reset_metrics(self) -> None:
        """Reset all metrics."""
        self.metrics = {
            "total_requests": 0,
            "allowed_requests": 0,
            "blocked_requests": 0,
            "retry_attempts": 0,
            "successful_retries": 0,
            "circuit_trips": 0,
            "circuit_resets": 0,
        }
        logger.info("Rate limit metrics reset")

    async def reset_circuit_breaker(self, circuit_key: str) -> None:
        """Reset circuit breaker for specific key."""
        if circuit_key in self.circuit_states:
            self.circuit_states[circuit_key] = {
                "state": CircuitState.CLOSED,
                "failure_count": 0,
                "last_failure_time": 0,
                "last_attempt_time": 0,
            }
            logger.info(f"Circuit breaker reset for {circuit_key}")
