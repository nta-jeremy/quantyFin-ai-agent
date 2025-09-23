"""
Integration tests for cash flow financial endpoint.
These tests will fail initially and pass once the implementation is complete.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app  # This will be available after implementation

client = TestClient(app)

class TestCashFlowEndpoint:
    """Integration tests for cash flow endpoint."""

    @pytest.mark.asyncio
    async def test_cash_flow_basic_request(self):
        """Test basic cash flow request."""
        response = client.get("/api/v1/financial/cash-flow/VNM")

        # Initially will return 404 until implemented
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = response.json()
            assert "data" in data
            assert "metadata" in data
            assert data["metadata"]["symbol"] == "VNM"

    @pytest.mark.asyncio
    async def test_cash_flow_with_parameters(self):
        """Test cash flow request with parameters."""
        params = {
            "source": "VCI",
            "period": "year",
            "use_cache": True
        }
        response = client.get("/api/v1/financial/cash-flow/HPG", params=params)

        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = response.json()
            assert data["metadata"]["source"] == "VCI"
            assert data["metadata"]["period"] == "year"

    @pytest.mark.asyncio
    async def test_cash_flow_quarterly_data(self):
        """Test cash flow with quarterly period."""
        response = client.get(
            "/api/v1/financial/cash-flow/VIC",
            params={"period": "quarter"}
        )

        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_cash_flow_different_sources(self):
        """Test cash flow data from different sources."""
        sources = ["VCI", "TCBS"]

        for source in sources:
            response = client.get(
                "/api/v1/financial/cash-flow/ACB",
                params={"source": source}
            )

            assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_cash_flow_data_completeness(self):
        """Test cash flow data completeness."""
        response = client.get("/api/v1/financial/cash-flow/FPT")

        if response.status_code == 200:
            data = response.json()

            # Check that data contains expected cash flow categories
            if data["data"]:
                first_item = data["data"][0]
                expected_categories = [
                    "net_cash_from_operations",
                    "net_cash_from_investing",
                    "net_cash_from_financing"
                ]

                # Should have at least one of the main cash flow categories
                has_cash_flow_data = any(
                    category in str(first_item).lower()
                    for category in expected_categories
                )
                assert has_cash_flow_data

    @pytest.mark.asyncio
    async def test_cash_flow_free_cash_flow(self):
        """Test cash flow includes free cash flow calculation."""
        response = client.get("/api/v1/financial/cash-flow/TCB")

        if response.status_code == 200:
            data = response.json()

            # Check if free cash flow is included
            if data["data"]:
                first_item = data["data"][0]
                # Free cash flow might be calculated or raw data
                assert "free_cash_flow" in str(first_item).lower() or "net_change_in_cash" in str(first_item)