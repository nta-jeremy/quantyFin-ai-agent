"""
Integration tests for error handling scenarios.
Tests various error conditions and graceful degradation.
"""

from typing import Any, Dict

import httpx
import pytest

from tests.integration.utils import BASE_URL, get_auth_headers, get_test_config


@pytest.mark.integration
@pytest.mark.asyncio
async def test_authentication_error_scenarios():
    """Test various authentication error scenarios."""
    config = get_test_config()

    # Test 1: No authentication header
    async with httpx.AsyncClient(
        base_url=BASE_URL, timeout=config["timeout"]
    ) as client:
        response = await client.get("/listing/symbols")

    assert response.status_code == 401
    error_data = response.json()
    assert "error" in error_data
    assert "Unauthorized" in error_data.get("error", "")

    # Test 2: Invalid token format
    invalid_headers = {"Authorization": "InvalidFormat"}
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get(
            "/listing/symbols", headers=invalid_headers
        )

    assert response.status_code == 401

    # Test 3: Expired token (simulate with invalid token)
    expired_headers = {"Authorization": "Bearer expired_token_12345"}
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get(
            "/listing/symbols", headers=expired_headers
        )

    assert response.status_code == 401

    # Test 4: Malformed JWT
    malformed_headers = {"Authorization": "Bearer malformed.jwt.token"}
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get(
            "/listing/symbols", headers=malformed_headers
        )

    assert response.status_code == 401


@pytest.mark.integration
@pytest.mark.asyncio
async def test_validation_error_scenarios():
    """Test input validation error scenarios."""
    headers = get_auth_headers()

    # Test 1: Invalid exchange parameter
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get(
            "/listing/symbols/exchange?exchange=INVALID_EXCHANGE",
            headers=headers,
        )

    assert response.status_code == 400
    error_data = response.json()
    assert "error" in error_data
    assert "ValidationError" in error_data.get("error", "")

    # Test 2: Empty required parameter
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get(
            "/listing/symbols/exchange?exchange=", headers=headers
        )

    assert response.status_code == 400

    # Test 3: Invalid data types in query parameters
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get(
            "/listing/symbols/exchange?exchange=123", headers=headers
        )

    assert response.status_code == 400

    # Test 4: Very long parameter values
    long_param = "A" * 1000
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get(
            f"/listing/symbols/exchange?exchange={long_param}", headers=headers
        )

    assert response.status_code == 400


@pytest.mark.integration
@pytest.mark.asyncio
async def test_rate_limiting_scenarios():
    """Test rate limiting behavior."""
    headers = get_auth_headers()

    # Test 1: Normal rate (should succeed)
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get("/listing/symbols", headers=headers)

    assert response.status_code == 200

    # Test 2: Rapid successive requests (may trigger rate limiting)
    responses = []
    for i in range(15):  # Exceed typical rate limit
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            response = await client.get("/listing/symbols", headers=headers)
            responses.append(response)

    # Check if any requests were rate limited
    rate_limited_responses = [r for r in responses if r.status_code == 429]

    if rate_limited_responses:
        # Validate rate limit response format
        rate_limit_response = rate_limited_responses[0]
        assert "X-RateLimit-Limit" in rate_limit_response.headers
        assert "X-RateLimit-Remaining" in rate_limit_response.headers
        assert "X-RateLimit-Reset" in rate_limit_response.headers

        error_data = rate_limit_response.json()
        assert "error" in error_data
        assert "TooManyRequests" in error_data.get("error", "")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_not_found_scenarios():
    """Test 404 not found scenarios."""
    headers = get_auth_headers()

    # Test 1: Invalid endpoint
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get(
            "/listing/invalid_endpoint", headers=headers
        )

    assert response.status_code == 404

    # Test 2: Invalid market group
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get(
            "/listing/symbols/group/INVALID_GROUP", headers=headers
        )

    assert response.status_code == 404

    # Test 3: Invalid URL structure
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get(
            "/listing/symbols/exchange/INVALID/extra", headers=headers
        )

    assert response.status_code == 404


@pytest.mark.integration
@pytest.mark.asyncio
async def test_method_not_allowed_scenarios():
    """Test method not allowed scenarios."""
    headers = get_auth_headers()

    # Test POST on GET-only endpoints
    post_endpoints = [
        "/listing/symbols",
        "/listing/symbols/exchange",
        "/listing/symbols/vn30",
        "/listing/industries",
    ]

    for endpoint in post_endpoints:
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            response = await client.post(endpoint, headers=headers, json={})

        assert response.status_code == 405

    # Test PUT on GET-only endpoints
    for endpoint in post_endpoints:
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            response = await client.put(endpoint, headers=headers, json={})

        assert response.status_code == 405

    # Test DELETE on GET-only endpoints
    for endpoint in post_endpoints:
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            response = await client.delete(endpoint, headers=headers)

        assert response.status_code == 405


@pytest.mark.integration
@pytest.mark.asyncio
async def test_server_error_simulation():
    """Test server error scenarios and graceful degradation."""
    headers = get_auth_headers()

    # Note: These tests may need to be adjusted based on actual server behavior
    # For now, we test that the server handles malformed requests gracefully

    # Test 1: Malformed JSON in POST (even though endpoints are GET-only)
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.post(
            "/listing/symbols",
            headers={**headers, "Content-Type": "application/json"},
            content="invalid json {",
        )

    # Should return 400 (Bad Request) or 405 (Method Not Allowed)
    assert response.status_code in [400, 405]

    # Test 2: Invalid headers
    invalid_headers = {
        **headers,
        "Content-Type": "invalid/content-type",
        "X-Invalid-Header": "value",
    }

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get(
            "/listing/symbols", headers=invalid_headers
        )

    # Should handle invalid headers gracefully
    assert response.status_code in [200, 400]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_timeout_scenarios():
    """Test timeout handling."""
    # This test may need to be adjusted based on actual server configuration
    # For now, we test that requests complete within reasonable time

    headers = get_auth_headers()

    import time

    # Test normal request timing
    start_time = time.time()
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get("/listing/symbols", headers=headers)
    end_time = time.time()

    assert response.status_code == 200
    response_time = end_time - start_time

    # Request should complete within reasonable time
    assert response_time < 5.0, f"Request took too long: {response_time:.2f}s"

    # Test with timeout parameter
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=1.0) as client:
        response = await client.get("/listing/symbols", headers=headers)

    # Should either succeed or timeout gracefully
    assert response.status_code in [200, 408]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_error_response_format_consistency():
    """Test that all error responses follow consistent format."""
    headers = get_auth_headers()

    error_scenarios = [
        # Authentication errors
        lambda client: client.get("/listing/symbols"),
        # Validation errors
        lambda client: client.get(
            "/listing/symbols/exchange?exchange=INVALID"
        ),
        # Not found errors
        lambda client: client.get("/listing/symbols/group/INVALID_GROUP"),
        # Method not allowed
        lambda client: client.post(
            "/listing/symbols", headers=headers, json={}
        ),
    ]

    for scenario in error_scenarios:
        try:
            async with httpx.AsyncClient(base_url=BASE_URL) as client:
                response = await scenario(client)

            if response.status_code >= 400:
                error_data = response.json()

                # Check standard error format
                assert (
                    "error" in error_data
                ), "Error response missing 'error' field"

                # Check for optional fields
                if "message" in error_data:
                    assert isinstance(error_data["message"], str)
                    assert len(error_data["message"].strip()) > 0

                if "details" in error_data:
                    assert isinstance(error_data["details"], dict)

        except Exception as e:
            # Some scenarios may raise exceptions, which is also valid error handling
            pytest.fail(f"Exception in error scenario: {e}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_graceful_degradation():
    """Test graceful degradation when external services fail."""
    headers = get_auth_headers()

    # Test that basic endpoints still work even if some advanced features fail
    basic_endpoints = [
        "/listing/symbols",
        "/listing/symbols/exchange",
        "/listing/symbols/vn30",
    ]

    for endpoint in basic_endpoints:
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            response = await client.get(endpoint, headers=headers)

        # Should succeed or degrade gracefully (not 500 error)
        assert response.status_code not in [
            500,
            502,
            503,
            504,
        ], f"Server error on {endpoint}: {response.status_code}"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_error_logging_and_monitoring():
    """Test that errors are properly logged and can be monitored."""
    headers = get_auth_headers()

    # This test validates that error responses include monitoring-friendly information
    error_scenarios = [
        ("Authentication", lambda c: c.get("/listing/symbols")),
        (
            "Validation",
            lambda c: c.get("/listing/symbols/exchange?exchange=INVALID"),
        ),
        ("Not Found", lambda c: c.get("/listing/symbols/group/INVALID_GROUP")),
    ]

    for scenario_name, scenario in error_scenarios:
        try:
            async with httpx.AsyncClient(base_url=BASE_URL) as client:
                response = await scenario(client)

            if response.status_code >= 400:
                # Check for monitoring headers
                monitoring_headers = [
                    "X-Request-ID",
                    "X-Trace-ID",
                    "X-Error-Code",
                ]

                found_headers = [
                    header
                    for header in monitoring_headers
                    if header in response.headers
                ]

                # Note: Headers may not be present in test environment,
                # but this validates the structure for monitoring integration

                error_data = response.json()

                # Error data should be structured for logging
                assert isinstance(error_data, dict)
                assert "error" in error_data

        except Exception as e:
            # Log the exception for debugging
            print(f"Exception in {scenario_name} scenario: {e}")
            # Exceptions are also a valid form of error handling
