"""
Performance tests for API response times.

This module tests that all API endpoints respond within 500ms,
ensuring the Vnstock Historical Data API meets performance requirements.
"""

import asyncio
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

import pytest
from fastapi.testclient import TestClient

from app.core.domain.historical_models import (
    AssetType,
    HistoricalDataRequest,
    HistoricalDataResponse,
    OHLCVTData,
    TimeInterval,
)
from app.main import app


class TestAPIResponseTimes:
    """Performance tests for API response times."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def auth_headers(self):
        """Create authentication headers."""
        return {
            "Authorization": "Bearer test-token",
            "X-API-Key": "test-api-key",
        }

    def measure_response_time(
        self,
        client,
        method: str,
        url: str,
        headers: Dict[str, str] = None,
        json_data: Dict[str, Any] = None,
    ) -> float:
        """
        Measure response time for an API call.

        Args:
            client: TestClient instance
            method: HTTP method (GET, POST, etc.)
            url: API endpoint URL
            headers: Optional headers
            json_data: Optional JSON data for POST requests

        Returns:
            Response time in milliseconds
        """
        start_time = time.time()

        if method.upper() == "GET":
            response = client.get(url, headers=headers)
        elif method.upper() == "POST":
            response = client.post(url, headers=headers, json=json_data)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

        end_time = time.time()
        response_time_ms = (end_time - start_time) * 1000

        # Log response time and status
        print(
            f"{method} {url}: {response_time_ms:.2f}ms (Status: {response.status_code})"
        )

        return response_time_ms

    def test_historical_data_response_time(self, client, auth_headers):
        """Test historical data endpoint response time under 500ms."""
        start_date = (
            datetime.now(timezone.utc) - timedelta(days=30)
        ).strftime("%Y-%m-%d")
        end_date = (datetime.now(timezone.utc) - timedelta(days=1)).strftime(
            "%Y-%m-%d"
        )

        url = f"/api/v1/historical/data?symbol=VNM&start_date={start_date}&end_date={end_date}"

        response_time = self.measure_response_time(
            client, "GET", url, headers=auth_headers
        )

        # Assert response time is under 500ms
        assert (
            response_time < 500
        ), f"Historical data endpoint took {response_time:.2f}ms, expected < 500ms"

    def test_historical_data_bulk_response_time(self, client, auth_headers):
        """Test bulk historical data endpoint response time under 500ms."""
        start_date = (datetime.now(timezone.utc) - timedelta(days=7)).strftime(
            "%Y-%m-%d"
        )
        end_date = (datetime.now(timezone.utc) - timedelta(days=1)).strftime(
            "%Y-%m-%d"
        )

        url = f"/api/v1/historical/data/bulk?symbols=VNM,AAPL&start_date={start_date}&end_date={end_date}"

        response_time = self.measure_response_time(
            client, "GET", url, headers=auth_headers
        )

        # Assert response time is under 500ms
        assert (
            response_time < 500
        ), f"Bulk historical data endpoint took {response_time:.2f}ms, expected < 500ms"

    def test_intraday_data_response_time(self, client, auth_headers):
        """Test intraday data endpoint response time under 500ms."""
        url = "/api/v1/historical/data/intraday?symbol=VNM&interval=5m"

        response_time = self.measure_response_time(
            client, "GET", url, headers=auth_headers
        )

        # Assert response time is under 500ms
        assert (
            response_time < 500
        ), f"Intraday data endpoint took {response_time:.2f}ms, expected < 500ms"

    def test_real_time_quote_response_time(self, client, auth_headers):
        """Test real-time quote endpoint response time under 500ms."""
        url = "/api/v1/historical/data/real-time?symbol=VNM"

        response_time = self.measure_response_time(
            client, "GET", url, headers=auth_headers
        )

        # Assert response time is under 500ms
        assert (
            response_time < 500
        ), f"Real-time quote endpoint took {response_time:.2f}ms, expected < 500ms"

    def test_forex_pairs_response_time(self, client, auth_headers):
        """Test forex pairs endpoint response time under 500ms."""
        url = "/api/v1/international/forex/pairs"

        response_time = self.measure_response_time(
            client, "GET", url, headers=auth_headers
        )

        # Assert response time is under 500ms
        assert (
            response_time < 500
        ), f"Forex pairs endpoint took {response_time:.2f}ms, expected < 500ms"

    def test_indices_response_time(self, client, auth_headers):
        """Test world indices endpoint response time under 500ms."""
        url = "/api/v1/international/indices"

        response_time = self.measure_response_time(
            client, "GET", url, headers=auth_headers
        )

        # Assert response time is under 500ms
        assert (
            response_time < 500
        ), f"World indices endpoint took {response_time:.2f}ms, expected < 500ms"

    def test_crypto_response_time(self, client, auth_headers):
        """Test crypto endpoint response time under 500ms."""
        url = "/api/v1/international/crypto"

        response_time = self.measure_response_time(
            client, "GET", url, headers=auth_headers
        )

        # Assert response time is under 500ms
        assert (
            response_time < 500
        ), f"Crypto endpoint took {response_time:.2f}ms, expected < 500ms"

    def test_data_source_health_response_time(self, client, auth_headers):
        """Test data source health endpoint response time under 500ms."""
        url = "/api/v1/historical/data/sources/health"

        response_time = self.measure_response_time(
            client, "GET", url, headers=auth_headers
        )

        # Assert response time is under 500ms
        assert (
            response_time < 500
        ), f"Data source health endpoint took {response_time:.2f}ms, expected < 500ms"

    def test_data_source_metrics_response_time(self, client, auth_headers):
        """Test data source metrics endpoint response time under 500ms."""
        url = "/api/v1/historical/data/sources/metrics"

        response_time = self.measure_response_time(
            client, "GET", url, headers=auth_headers
        )

        # Assert response time is under 500ms
        assert (
            response_time < 500
        ), f"Data source metrics endpoint took {response_time:.2f}ms, expected < 500ms"

    @pytest.mark.performance
    def test_multiple_requests_performance(self, client, auth_headers):
        """Test performance of multiple consecutive requests."""
        start_date = (datetime.now(timezone.utc) - timedelta(days=7)).strftime(
            "%Y-%m-%d"
        )
        end_date = (datetime.now(timezone.utc) - timedelta(days=1)).strftime(
            "%Y-%m-%d"
        )

        url = f"/api/v1/historical/data?symbol=VNM&start_date={start_date}&end_date={end_date}"

        response_times = []

        # Make 10 consecutive requests
        for i in range(10):
            response_time = self.measure_response_time(
                client, "GET", url, headers=auth_headers
            )
            response_times.append(response_time)

            # Small delay between requests
            time.sleep(0.1)

        # Calculate statistics
        avg_response_time = sum(response_times) / len(response_times)
        max_response_time = max(response_times)
        min_response_time = min(response_times)

        print(
            f"Response times - Avg: {avg_response_time:.2f}ms, Max: {max_response_time:.2f}ms, Min: {min_response_time:.2f}ms"
        )

        # Assert average response time is under 500ms
        assert (
            avg_response_time < 500
        ), f"Average response time {avg_response_time:.2f}ms exceeds 500ms limit"

        # Assert no single request takes more than 1000ms (generous limit for individual requests)
        assert (
            max_response_time < 1000
        ), f"Maximum response time {max_response_time:.2f}ms exceeds 1000ms limit"

    @pytest.mark.performance
    def test_different_symbols_performance(self, client, auth_headers):
        """Test performance with different symbols."""
        start_date = (datetime.now(timezone.utc) - timedelta(days=5)).strftime(
            "%Y-%m-%d"
        )
        end_date = (datetime.now(timezone.utc) - timedelta(days=1)).strftime(
            "%Y-%m-%d"
        )

        symbols = ["VNM", "AAPL", "GOOGL", "MSFT", "TSLA"]
        response_times = {}

        for symbol in symbols:
            url = f"/api/v1/historical/data?symbol={symbol}&start_date={start_date}&end_date={end_date}"
            response_time = self.measure_response_time(
                client, "GET", url, headers=auth_headers
            )
            response_times[symbol] = response_time

            # Small delay between requests
            time.sleep(0.1)

        # Print performance for each symbol
        for symbol, rt in response_times.items():
            print(f"{symbol}: {rt:.2f}ms")

        # Assert all symbols meet performance requirements
        for symbol, response_time in response_times.items():
            assert (
                response_time < 500
            ), f"Symbol {symbol} took {response_time:.2f}ms, expected < 500ms"

    @pytest.mark.performance
    def test_cache_performance(self, client, auth_headers):
        """Test cached response performance."""
        start_date = (datetime.now(timezone.utc) - timedelta(days=3)).strftime(
            "%Y-%m-%d"
        )
        end_date = (datetime.now(timezone.utc) - timedelta(days=1)).strftime(
            "%Y-%m-%d"
        )

        url = f"/api/v1/historical/data?symbol=VNM&start_date={start_date}&end_date={end_date}&use_cache=true"

        # First request (cache miss)
        first_response_time = self.measure_response_time(
            client, "GET", url, headers=auth_headers
        )
        print(f"First request (cache miss): {first_response_time:.2f}ms")

        # Second request (cache hit)
        second_response_time = self.measure_response_time(
            client, "GET", url, headers=auth_headers
        )
        print(f"Second request (cache hit): {second_response_time:.2f}ms")

        # Cache hit should be significantly faster
        assert (
            second_response_time < first_response_time
        ), "Cache hit should be faster than cache miss"

        # Both should meet performance requirements
        assert (
            first_response_time < 500
        ), f"Cache miss took {first_response_time:.2f}ms, expected < 500ms"
        assert (
            second_response_time < 200
        ), f"Cache hit took {second_response_time:.2f}ms, expected < 200ms"

    @pytest.mark.performance
    def test_error_handling_performance(self, client, auth_headers):
        """Test performance of error handling."""
        # Test with invalid symbol
        url = "/api/v1/historical/data?symbol=INVALID_SYMBOL"

        response_time = self.measure_response_time(
            client, "GET", url, headers=auth_headers
        )

        # Error responses should still be fast
        assert (
            response_time < 500
        ), f"Error response took {response_time:.2f}ms, expected < 500ms"

    @pytest.mark.performance
    def test_bulk_scaling_performance(self, client, auth_headers):
        """Test performance scaling with bulk request size."""
        start_date = (datetime.now(timezone.utc) - timedelta(days=7)).strftime(
            "%Y-%m-%d"
        )
        end_date = (datetime.now(timezone.utc) - timedelta(days=1)).strftime(
            "%Y-%m-%d"
        )

        # Test with different numbers of symbols
        symbol_counts = [1, 3, 5, 10]
        response_times = {}

        for count in symbol_counts:
            symbols = ["VNM", "AAPL", "GOOGL", "MSFT", "TSLA"][:count]
            symbols_str = ",".join(symbols)
            url = f"/api/v1/historical/data/bulk?symbols={symbols_str}&start_date={start_date}&end_date={end_date}"

            response_time = self.measure_response_time(
                client, "GET", url, headers=auth_headers
            )
            response_times[count] = response_time

            # Small delay between requests
            time.sleep(0.1)

        # Print scaling performance
        for count, rt in response_times.items():
            print(f"{count} symbols: {rt:.2f}ms")

        # Even 10 symbols should complete within reasonable time
        assert (
            response_times[10] < 2000
        ), f"10 symbols request took {response_times[10]:.2f}ms, expected < 2000ms"


class TestConcurrentPerformance:
    """Performance tests for concurrent requests."""

    @pytest.mark.asyncio
    async def test_concurrent_requests_performance(self):
        """Test performance under concurrent load."""
        import aiohttp

        # Test endpoint
        url = (
            "http://localhost:8000/api/v1/historical/data/real-time?symbol=VNM"
        )
        headers = {"Authorization": "Bearer test-token"}

        async def make_request():
            async with aiohttp.ClientSession() as session:
                start_time = time.time()
                try:
                    async with session.get(url, headers=headers) as response:
                        end_time = time.time()
                        response_time = (end_time - start_time) * 1000
                        return response_time
                except:
                    end_time = time.time()
                    return (end_time - start_time) * 1000

        # Make concurrent requests
        num_requests = 50
        tasks = [make_request() for _ in range(num_requests)]
        response_times = await asyncio.gather(*tasks)

        # Calculate statistics
        avg_response_time = sum(response_times) / len(response_times)
        max_response_time = max(response_times)
        min_response_time = min(response_times)

        print(f"Concurrent requests ({num_requests}):")
        print(f"  Avg: {avg_response_time:.2f}ms")
        print(f"  Max: {max_response_time:.2f}ms")
        print(f"  Min: {min_response_time:.2f}ms")

        # Concurrent requests should still perform well
        assert (
            avg_response_time < 1000
        ), f"Average concurrent response time {avg_response_time:.2f}ms exceeds 1000ms limit"
        assert (
            max_response_time < 3000
        ), f"Maximum concurrent response time {max_response_time:.2f}ms exceeds 3000ms limit"
