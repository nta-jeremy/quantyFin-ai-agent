"""
Load tests for the Vnstock Historical Data API.

This module tests system performance under high load conditions,
simulating 1000 concurrent users to ensure the API meets performance requirements.
"""

import asyncio
import statistics
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

import aiohttp
import httpx
import pytest

from app.core.domain.historical_models import AssetType, TimeInterval


class LoadTestConfig:
    """Configuration for load testing."""

    BASE_URL = "http://localhost:8000/api/v1"
    AUTH_HEADERS = {"Authorization": "Bearer test-token"}

    # Load test scenarios
    SCENARIOS = {
        "historical_data": {
            "url": "/historical/data?symbol=VNM&start_date=2024-01-01&end_date=2024-01-31",
            "method": "GET",
            "weight": 0.4,  # 40% of requests
        },
        "real_time": {
            "url": "/historical/data/real-time?symbol=VNM",
            "method": "GET",
            "weight": 0.3,  # 30% of requests
        },
        "international_forex": {
            "url": "/international/forex/pairs",
            "method": "GET",
            "weight": 0.15,  # 15% of requests
        },
        "international_indices": {
            "url": "/international/indices",
            "method": "GET",
            "weight": 0.15,  # 15% of requests
        },
    }

    # Performance thresholds
    THRESHOLDS = {
        "avg_response_time": 500,  # ms
        "max_response_time": 2000,  # ms
        "error_rate": 0.01,  # 1%
        "throughput": 1000,  # requests per second
        "success_rate": 0.99,  # 99%
    }


class LoadTestResults:
    """Container for load test results."""

    def __init__(self):
        self.response_times: List[float] = []
        self.error_count: int = 0
        self.success_count: int = 0
        self.status_codes: Dict[int, int] = {}
        self.start_time: float = 0
        self.end_time: float = 0

    def add_result(self, response_time: float, status_code: int):
        """Add a single request result."""
        self.response_times.append(response_time)
        self.status_codes[status_code] = (
            self.status_codes.get(status_code, 0) + 1
        )

        if 200 <= status_code < 300:
            self.success_count += 1
        else:
            self.error_count += 1

    def get_statistics(self) -> Dict[str, Any]:
        """Calculate performance statistics."""
        if not self.response_times:
            return {}

        total_time = self.end_time - self.start_time
        total_requests = len(self.response_times)

        return {
            "total_requests": total_requests,
            "success_count": self.success_count,
            "error_count": self.error_count,
            "success_rate": (
                self.success_count / total_requests
                if total_requests > 0
                else 0
            ),
            "error_rate": (
                self.error_count / total_requests if total_requests > 0 else 0
            ),
            "avg_response_time": statistics.mean(self.response_times),
            "median_response_time": statistics.median(self.response_times),
            "min_response_time": min(self.response_times),
            "max_response_time": max(self.response_times),
            "p95_response_time": statistics.quantiles(
                self.response_times, n=20
            )[
                18
            ],  # 95th percentile
            "p99_response_time": statistics.quantiles(
                self.response_times, n=100
            )[
                98
            ],  # 99th percentile
            "throughput": total_requests / total_time if total_time > 0 else 0,
            "duration_seconds": total_time,
            "status_codes": self.status_codes,
        }


class LoadTester:
    """Load testing engine for the Vnstock Historical Data API."""

    def __init__(self, config: LoadTestConfig):
        self.config = config
        self.results = LoadTestResults()

    async def make_request(
        self, session: aiohttp.ClientSession, scenario: Dict[str, Any]
    ) -> float:
        """Make a single HTTP request and return response time."""
        url = self.config.BASE_URL + scenario["url"]
        method = scenario["method"]
        headers = self.config.AUTH_HEADERS

        start_time = time.time()

        try:
            if method.upper() == "GET":
                async with session.get(url, headers=headers) as response:
                    response_time = (time.time() - start_time) * 1000
                    return response_time, response.status
            else:
                response_time = (time.time() - start_time) * 1000
                return response_time, 500
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return response_time, 500

    async def run_user_session(
        self, session: aiohttp.ClientSession, num_requests: int
    ) -> List[Dict[str, Any]]:
        """Simulate a user session with multiple requests."""
        results = []

        for _ in range(num_requests):
            # Select scenario based on weights
            scenarios = list(self.config.SCENARIOS.items())
            weights = [scenario["weight"] for _, scenario in scenarios]

            # Simple weighted selection
            import random

            selected = random.choices(scenarios, weights=weights)[0]
            scenario_name, scenario_config = selected

            response_time, status_code = await self.make_request(
                session, scenario_config
            )

            results.append(
                {
                    "scenario": scenario_name,
                    "response_time": response_time,
                    "status_code": status_code,
                }
            )

            # Small delay between requests to simulate user behavior
            await asyncio.sleep(0.01)

        return results

    async def run_load_test(
        self, concurrent_users: int, requests_per_user: int
    ) -> LoadTestResults:
        """Run the main load test."""
        print(
            f"Starting load test: {concurrent_users} concurrent users, {requests_per_user} requests each"
        )

        self.results = LoadTestResults()
        self.results.start_time = time.time()

        # Create aiohttp session with connection pooling
        connector = aiohttp.TCPConnector(
            limit=concurrent_users,
            limit_per_host=concurrent_users,
            ttl_dns_cache=300,
            use_dns_cache=True,
        )

        timeout = aiohttp.ClientTimeout(total=30)

        async with aiohttp.ClientSession(
            connector=connector, timeout=timeout
        ) as session:
            # Create user tasks
            user_tasks = []
            for _ in range(concurrent_users):
                task = self.run_user_session(session, requests_per_user)
                user_tasks.append(task)

            # Run all user sessions concurrently
            user_results = await asyncio.gather(
                *user_tasks, return_exceptions=True
            )

            # Process results
            for user_result in user_results:
                if isinstance(user_result, Exception):
                    self.results.error_count += 1
                    self.results.status_codes[500] = (
                        self.results.status_codes.get(500, 0) + 1
                    )
                else:
                    for result in user_result:
                        self.results.add_result(
                            result["response_time"], result["status_code"]
                        )

        self.results.end_time = time.time()

        return self.results

    def print_results(self, results: LoadTestResults):
        """Print detailed load test results."""
        stats = results.get_statistics()

        print("\n" + "=" * 60)
        print("LOAD TEST RESULTS")
        print("=" * 60)
        print(f"Total Requests: {stats['total_requests']}")
        print(f"Duration: {stats['duration_seconds']:.2f} seconds")
        print(f"Throughput: {stats['throughput']:.2f} requests/second")
        print()
        print("Response Times:")
        print(f"  Average: {stats['avg_response_time']:.2f}ms")
        print(f"  Median: {stats['median_response_time']:.2f}ms")
        print(f"  Min: {stats['min_response_time']:.2f}ms")
        print(f"  Max: {stats['max_response_time']:.2f}ms")
        print(f"  95th percentile: {stats['p95_response_time']:.2f}ms")
        print(f"  99th percentile: {stats['p99_response_time']:.2f}ms")
        print()
        print("Success/Error Rates:")
        print(
            f"  Success: {stats['success_count']} ({stats['success_rate']*100:.1f}%)"
        )
        print(
            f"  Errors: {stats['error_count']} ({stats['error_rate']*100:.1f}%)"
        )
        print()
        print("Status Codes:")
        for code, count in stats["status_codes"].items():
            print(f"  {code}: {count}")
        print("=" * 60)

    def validate_results(self, results: LoadTestResults) -> bool:
        """Validate results against performance thresholds."""
        stats = results.get_statistics()
        thresholds = self.config.THRESHOLDS

        passed = True
        print("\nVALIDATION RESULTS:")

        # Check average response time
        if stats["avg_response_time"] <= thresholds["avg_response_time"]:
            print(
                f"✅ Average response time: {stats['avg_response_time']:.2f}ms <= {thresholds['avg_response_time']}ms"
            )
        else:
            print(
                f"❌ Average response time: {stats['avg_response_time']:.2f}ms > {thresholds['avg_response_time']}ms"
            )
            passed = False

        # Check max response time
        if stats["max_response_time"] <= thresholds["max_response_time"]:
            print(
                f"✅ Max response time: {stats['max_response_time']:.2f}ms <= {thresholds['max_response_time']}ms"
            )
        else:
            print(
                f"❌ Max response time: {stats['max_response_time']:.2f}ms > {thresholds['max_response_time']}ms"
            )
            passed = False

        # Check error rate
        if stats["error_rate"] <= thresholds["error_rate"]:
            print(
                f"✅ Error rate: {stats['error_rate']*100:.2f}% <= {thresholds['error_rate']*100}%"
            )
        else:
            print(
                f"❌ Error rate: {stats['error_rate']*100:.2f}% > {thresholds['error_rate']*100}%"
            )
            passed = False

        # Check throughput
        if stats["throughput"] >= thresholds["throughput"]:
            print(
                f"✅ Throughput: {stats['throughput']:.2f} req/s >= {thresholds['throughput']} req/s"
            )
        else:
            print(
                f"❌ Throughput: {stats['throughput']:.2f} req/s < {thresholds['throughput']} req/s"
            )
            passed = False

        # Check success rate
        if stats["success_rate"] >= thresholds["success_rate"]:
            print(
                f"✅ Success rate: {stats['success_rate']*100:.2f}% >= {thresholds['success_rate']*100}%"
            )
        else:
            print(
                f"❌ Success rate: {stats['success_rate']*100:.2f}% < {thresholds['success_rate']*100}%"
            )
            passed = False

        return passed


@pytest.mark.load
@pytest.mark.asyncio
async def test_1000_concurrent_users():
    """Main load test: 1000 concurrent users."""
    config = LoadTestConfig()
    tester = LoadTester(config)

    # Test configuration
    concurrent_users = 1000
    requests_per_user = 1  # Each user makes 1 request

    # Run the load test
    results = await tester.run_load_test(concurrent_users, requests_per_user)

    # Print results
    tester.print_results(results)

    # Validate results
    passed = tester.validate_results(results)

    # Assert that the test passes all thresholds
    assert passed, "Load test failed to meet performance thresholds"


@pytest.mark.load
@pytest.mark.asyncio
async def test_sustained_load():
    """Test sustained load over time."""
    config = LoadTestConfig()
    tester = LoadTester(config)

    # Test with sustained load
    concurrent_users = 100
    requests_per_user = 10  # Each user makes 10 requests

    # Run the load test
    results = await tester.run_load_test(concurrent_users, requests_per_user)

    # Print results
    print(
        f"\nSUSTAINED LOAD TEST ({concurrent_users} users, {requests_per_user} requests each):"
    )
    tester.print_results(results)

    # Validate with slightly relaxed thresholds for sustained load
    stats = results.get_statistics()
    assert (
        stats["avg_response_time"] < 750
    ), f"Sustained load average response time too high: {stats['avg_response_time']:.2f}ms"
    assert (
        stats["success_rate"] > 0.95
    ), f"Sustained load success rate too low: {stats['success_rate']*100:.1f}%"


@pytest.mark.load
@pytest.mark.asyncio
async def test_burst_load():
    """Test handling of burst traffic."""
    config = LoadTestConfig()
    tester = LoadTester(config)

    # Test with burst of traffic
    concurrent_users = 500
    requests_per_user = 1

    # Run the load test
    results = await tester.run_load_test(concurrent_users, requests_per_user)

    # Print results
    print(f"\nBURST LOAD TEST ({concurrent_users} users):")
    tester.print_results(results)

    # Validate burst handling
    stats = results.get_statistics()
    assert (
        stats["max_response_time"] < 3000
    ), f"Burst load max response time too high: {stats['max_response_time']:.2f}ms"
    assert (
        stats["success_rate"] > 0.98
    ), f"Burst load success rate too low: {stats['success_rate']*100:.1f}%"


@pytest.mark.load
@pytest.mark.asyncio
async def test_scalability():
    """Test system scalability with increasing load."""
    config = LoadTestConfig()
    tester = LoadTester(config)

    user_counts = [100, 250, 500, 1000]
    scalability_results = []

    for user_count in user_counts:
        print(f"\nTesting with {user_count} concurrent users...")

        results = await tester.run_load_test(user_count, 1)
        stats = results.get_statistics()

        scalability_results.append(
            {
                "users": user_count,
                "avg_response_time": stats["avg_response_time"],
                "throughput": stats["throughput"],
                "success_rate": stats["success_rate"],
            }
        )

    # Print scalability results
    print(f"\nSCALABILITY RESULTS:")
    print(
        f"{'Users':<8} {'Avg Response (ms)':<20} {'Throughput (req/s)':<20} {'Success Rate (%)':<15}"
    )
    print("-" * 65)

    for result in scalability_results:
        print(
            f"{result['users']:<8} {result['avg_response_time']:<20.2f} {result['throughput']:<20.2f} {result['success_rate']*100:<15.1f}"
        )

    # Validate scalability
    # Response time should not increase linearly with user count
    last_response_time = scalability_results[0]["avg_response_time"]
    for i, result in enumerate(scalability_results[1:], 1):
        response_time_increase = (
            result["avg_response_time"] / last_response_time
        )
        user_increase = result["users"] / scalability_results[i - 1]["users"]

        # Response time should not increase proportionally to user count
        if response_time_increase > user_increase * 1.5:  # Allow 50% overhead
            print(
                f"⚠️  Scalability concern at {result['users']} users: response time increased {response_time_increase:.2f}x, users increased {user_increase:.2f}x"
            )

        last_response_time = result["avg_response_time"]

    # Final validation
    final_result = scalability_results[-1]
    assert (
        final_result["avg_response_time"] < 1000
    ), f"Scalability test failed: response time too high at {final_result['users']} users"
    assert (
        final_result["success_rate"] > 0.95
    ), f"Scalability test failed: success rate too low at {final_result['users']} users"


if __name__ == "__main__":
    # Run load tests directly
    asyncio.run(test_1000_concurrent_users())
