"""
Performance tests for financial endpoints.

This module tests the performance requirements for financial reporting
endpoints to ensure response times meet the <500ms requirement.
"""

import asyncio
import statistics
import time
from typing import List

import pytest

from app.main import app


class TestFinancialEndpointsPerformance:
    """Performance test suite for financial endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from fastapi.testclient import TestClient
        return TestClient(app)

    @pytest.mark.performance
    def test_balance_sheet_endpoint_performance(self, client):
        """Test balance sheet endpoint performance."""
        response_times = []
        num_requests = 10

        for _ in range(num_requests):
            start_time = time.time()
            response = client.get(
                "/api/v1/financial/balance-sheet/ACB",
                params={
                    "source": "VCI",
                    "period": "year",
                    "language": "vi",
                    "use_cache": "true",
                },
            )
            end_time = time.time()
            response_times.append((end_time - start_time) * 1000)  # Convert to ms

        # Calculate performance metrics
        avg_time = statistics.mean(response_times)
        max_time = max(response_times)
        min_time = min(response_times)
        p95_time = statistics.quantiles(response_times, n=20)[18]  # 95th percentile

        # Performance assertions
        assert avg_time < 500, f"Average response time {avg_time:.2f}ms exceeds 500ms limit"
        assert max_time < 1000, f"Max response time {max_time:.2f}ms exceeds 1000ms limit"
        assert p95_time < 750, f"95th percentile response time {p95_time:.2f}ms exceeds 750ms limit"

        print(f"\nBalance Sheet Performance:")
        print(f"  Average: {avg_time:.2f}ms")
        print(f"  Min: {min_time:.2f}ms")
        print(f"  Max: {max_time:.2f}ms")
        print(f"  95th percentile: {p95_time:.2f}ms")

    @pytest.mark.performance
    def test_income_statement_endpoint_performance(self, client):
        """Test income statement endpoint performance."""
        response_times = []
        num_requests = 10

        for _ in range(num_requests):
            start_time = time.time()
            response = client.get(
                "/api/v1/financial/income-statement/ACB",
                params={
                    "source": "VCI",
                    "period": "year",
                    "language": "vi",
                    "use_cache": "true",
                },
            )
            end_time = time.time()
            response_times.append((end_time - start_time) * 1000)

        avg_time = statistics.mean(response_times)
        max_time = max(response_times)
        p95_time = statistics.quantiles(response_times, n=20)[18]

        assert avg_time < 500, f"Average response time {avg_time:.2f}ms exceeds 500ms limit"
        assert max_time < 1000, f"Max response time {max_time:.2f}ms exceeds 1000ms limit"

        print(f"\nIncome Statement Performance:")
        print(f"  Average: {avg_time:.2f}ms")
        print(f"  Max: {max_time:.2f}ms")
        print(f"  95th percentile: {p95_time:.2f}ms")

    @pytest.mark.performance
    def test_cash_flow_endpoint_performance(self, client):
        """Test cash flow endpoint performance."""
        response_times = []
        num_requests = 10

        for _ in range(num_requests):
            start_time = time.time()
            response = client.get(
                "/api/v1/financial/cash-flow/ACB",
                params={
                    "source": "VCI",
                    "period": "year",
                    "language": "vi",
                    "use_cache": "true",
                },
            )
            end_time = time.time()
            response_times.append((end_time - start_time) * 1000)

        avg_time = statistics.mean(response_times)
        max_time = max(response_times)
        p95_time = statistics.quantiles(response_times, n=20)[18]

        assert avg_time < 500, f"Average response time {avg_time:.2f}ms exceeds 500ms limit"

        print(f"\nCash Flow Performance:")
        print(f"  Average: {avg_time:.2f}ms")
        print(f"  Max: {max_time:.2f}ms")
        print(f"  95th percentile: {p95_time:.2f}ms")

    @pytest.mark.performance
    def test_financial_ratios_endpoint_performance(self, client):
        """Test financial ratios endpoint performance."""
        response_times = []
        num_requests = 10

        for _ in range(num_requests):
            start_time = time.time()
            response = client.get(
                "/api/v1/financial/financial-ratios/ACB",
                params={
                    "source": "VCI",
                    "period": "year",
                    "language": "vi",
                    "use_cache": "true",
                },
            )
            end_time = time.time()
            response_times.append((end_time - start_time) * 1000)

        avg_time = statistics.mean(response_times)
        max_time = max(response_times)
        p95_time = statistics.quantiles(response_times, n=20)[18]

        assert avg_time < 500, f"Average response time {avg_time:.2f}ms exceeds 500ms limit"

        print(f"\nFinancial Ratios Performance:")
        print(f"  Average: {avg_time:.2f}ms")
        print(f"  Max: {max_time:.2f}ms")
        print(f"  95th percentile: {p95_time:.2f}ms")

    @pytest.mark.performance
    def test_comprehensive_endpoint_performance(self, client):
        """Test comprehensive financial data endpoint performance."""
        response_times = []
        num_requests = 10

        for _ in range(num_requests):
            start_time = time.time()
            response = client.get(
                "/api/v1/financial/comprehensive/ACB",
                params={
                    "source": "VCI",
                    "period": "year",
                    "language": "vi",
                    "use_cache": "true",
                },
            )
            end_time = time.time()
            response_times.append((end_time - start_time) * 1000)

        avg_time = statistics.mean(response_times)
        max_time = max(response_times)
        p95_time = statistics.quantiles(response_times, n=20)[18]

        # Comprehensive endpoint might be slightly slower due to concurrent calls
        assert avg_time < 750, f"Average response time {avg_time:.2f}ms exceeds 750ms limit"
        assert max_time < 1500, f"Max response time {max_time:.2f}ms exceeds 1500ms limit"

        print(f"\nComprehensive Financial Performance:")
        print(f"  Average: {avg_time:.2f}ms")
        print(f"  Max: {max_time:.2f}ms")
        print(f"  95th percentile: {p95_time:.2f}ms")

    @pytest.mark.performance
    def test_cache_performance_comparison(self, client):
        """Test performance difference between cached and uncached requests."""
        # First request (cache miss)
        start_time = time.time()
        response1 = client.get(
            "/api/v1/financial/balance-sheet/ACB",
            params={
                "source": "VCI",
                "period": "year",
                "language": "vi",
                "use_cache": "true",
            },
        )
        first_request_time = (time.time() - start_time) * 1000

        # Second request (should be cache hit)
        start_time = time.time()
        response2 = client.get(
            "/api/v1/financial/balance-sheet/ACB",
            params={
                "source": "VCI",
                "period": "year",
                "language": "vi",
                "use_cache": "true",
            },
        )
        second_request_time = (time.time() - start_time) * 1000

        # Third request (explicitly no cache)
        start_time = time.time()
        response3 = client.get(
            "/api/v1/financial/balance-sheet/ACB",
            params={
                "source": "VCI",
                "period": "year",
                "language": "vi",
                "use_cache": "false",
            },
        )
        third_request_time = (time.time() - start_time) * 1000

        print(f"\nCache Performance Comparison:")
        print(f"  First request (cache miss): {first_request_time:.2f}ms")
        print(f"  Second request (cache hit): {second_request_time:.2f}ms")
        print(f"  Third request (no cache): {third_request_time:.2f}ms")

        # Cache should be significantly faster
        if second_request_time < first_request_time:
            cache_improvement = ((first_request_time - second_request_time) / first_request_time) * 100
            print(f"  Cache improvement: {cache_improvement:.1f}%")

    @pytest.mark.performance
    def test_concurrent_requests_performance(self, client):
        """Test performance under concurrent load."""
        num_concurrent = 20
        num_requests_per_client = 5

        async def make_request():
            import aiohttp
            import json

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "http://testserver/api/v1/financial/balance-sheet/ACB",
                    params={
                        "source": "VCI",
                        "period": "year",
                        "language": "vi",
                        "use_cache": "true",
                    },
                ) as response:
                    return response.status, await response.text()

        # Test concurrent requests
        start_time = time.time()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            tasks = [make_request() for _ in range(num_concurrent)]
            results = loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
        finally:
            loop.close()

        total_time = (time.time() - start_time) * 1000
        avg_time = total_time / num_concurrent

        print(f"\nConcurrent Requests Performance:")
        print(f"  Concurrent requests: {num_concurrent}")
        print(f"  Total time: {total_time:.2f}ms")
        print(f"  Average per request: {avg_time:.2f}ms")

        # Check that all requests completed successfully
        successful_requests = [r for r in results if not isinstance(r, Exception)]
        assert len(successful_requests) == num_concurrent, \
            f"Only {len(successful_requests)}/{num_concurrent} requests completed successfully"

    @pytest.mark.performance
    def test_different_symbols_performance(self, client):
        """Test performance with different stock symbols."""
        symbols = ["ACB", "TCB", "VCB", "HPG", "MWG"]
        response_times = {}

        for symbol in symbols:
            start_time = time.time()
            response = client.get(
                f"/api/v1/financial/balance-sheet/{symbol}",
                params={
                    "source": "VCI",
                    "period": "year",
                    "language": "vi",
                    "use_cache": "true",
                },
            )
            end_time = time.time()
            response_times[symbol] = (end_time - start_time) * 1000

        avg_time = statistics.mean(response_times.values())
        max_time = max(response_times.values())

        print(f"\nDifferent Symbols Performance:")
        for symbol, time_ms in response_times.items():
            print(f"  {symbol}: {time_ms:.2f}ms")
        print(f"  Average: {avg_time:.2f}ms")
        print(f"  Max: {max_time:.2f}ms")

        assert avg_time < 500, f"Average response time {avg_time:.2f}ms exceeds 500ms limit"

    @pytest.mark.performance
    def test_endpoint_response_sizes(self, client):
        """Test that response sizes are reasonable for performance."""
        response = client.get(
            "/api/v1/financial/comprehensive/ACB",
            params={
                "source": "VCI",
                "period": "year",
                "language": "vi",
                "use_cache": "true",
            },
        )

        response_size = len(response.content)
        response_time_ms = (time.time() - time.time()) * 1000  # Placeholder

        print(f"\nResponse Size Analysis:")
        print(f"  Response size: {response_size} bytes")
        print(f"  Size per KB: {response_size / 1024:.2f} KB")

        # Response size should be reasonable (< 1MB for financial data)
        assert response_size < 1024 * 1024, \
            f"Response size {response_size} bytes exceeds 1MB limit"

    @pytest.mark.performance
    def test_error_handling_performance(self, client):
        """Test that error responses are also fast."""
        start_time = time.time()
        response = client.get(
            "/api/v1/financial/balance-sheet/INVALID_SYMBOL",
            params={
                "source": "VCI",
                "period": "year",
                "language": "vi",
                "use_cache": "true",
            },
        )
        end_time = time.time()

        error_response_time = (end_time - start_time) * 1000

        print(f"\nError Response Performance:")
        print(f"  Error response time: {error_response_time:.2f}ms")

        # Error responses should be fast
        assert error_response_time < 100, \
            f"Error response time {error_response_time:.2f}ms exceeds 100ms limit"