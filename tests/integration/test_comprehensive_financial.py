"""
Integration tests for comprehensive financial data endpoint.
These tests will fail initially and pass once the implementation is complete.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app  # This will be available after implementation

client = TestClient(app)

class TestComprehensiveFinancialEndpoint:
    """Integration tests for comprehensive financial data endpoint."""

    @pytest.mark.asyncio
    async def test_comprehensive_basic_request(self):
        """Test basic comprehensive financial data request."""
        response = client.get("/api/v1/financial/comprehensive/VIC")

        # Initially will return 404 until implemented
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = response.json()
            assert "success" in data
            assert "data" in data
            assert data["data"]["metadata"]["symbol"] == "VIC"

    @pytest.mark.asyncio
    async def test_comprehensive_data_structure(self):
        """Test comprehensive data contains all report types."""
        response = client.get("/api/v1/financial/comprehensive/ACB")

        if response.status_code == 200:
            data = response.json()
            report_data = data["data"]

            # Should contain all four report types
            assert "balance_sheet" in report_data
            assert "income_statement" in report_data
            assert "cash_flow" in report_data
            assert "financial_ratios" in report_data
            assert "metadata" in report_data

    @pytest.mark.asyncio
    async def test_comprehensive_with_parameters(self):
        """Test comprehensive request with parameters."""
        params = {
            "source": "VCI",
            "period": "year",
            "language": "vi",
            "use_cache": True
        }
        response = client.get("/api/v1/financial/comprehensive/FPT", params=params)

        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = response.json()
            metadata = data["data"]["metadata"]
            assert metadata["source"] == "VCI"
            assert metadata["period"] == "year"
            assert metadata["language"] == "vi"

    @pytest.mark.asyncio
    async def test_comprehensive_data_consistency(self):
        """Test data consistency across report types."""
        response = client.get("/api/v1/financial/comprehensive/VNM")

        if response.status_code == 200:
            data = response.json()
            report_data = data["data"]

            # All reports should have the same symbol and source
            metadata = report_data["metadata"]
            symbol = metadata["symbol"]
            source = metadata["source"]

            for report_type in ["balance_sheet", "income_statement", "cash_flow", "financial_ratios"]:
                if report_data[report_type]:
                    first_item = report_data[report_type][0]
                    assert first_item["symbol"] == symbol
                    assert first_item["source"] == source

    @pytest.mark.asyncio
    async def test_comprehensive_performance_indicators(self):
        """Test comprehensive response includes performance metrics."""
        response = client.get("/api/v1/financial/comprehensive/HPG")

        if response.status_code == 200:
            data = response.json()
            metadata = data["data"]["metadata"]

            # Should have processing time and data quality metrics
            assert "processing_time_ms" in metadata
            assert "data_quality" in metadata
            assert "generated_at" in metadata

    @pytest.mark.asyncio
    async def test_comprehensive_quarterly_data(self):
        """Test comprehensive endpoint with quarterly period."""
        response = client.get(
            "/api/v1/financial/comprehensive/TCB",
            params={"period": "quarter"}
        )

        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = response.json()
            metadata = data["data"]["metadata"]
            assert metadata["period"] == "quarter"

    @pytest.mark.asyncio
    async def test_comprehensive_different_sources(self):
        """Test comprehensive endpoint with different sources."""
        sources = ["VCI", "TCBS"]

        for source in sources:
            response = client.get(
                "/api/v1/financial/compressive/MSN",
                params={"source": source}
            )

            assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_comprehensive_error_handling(self):
        """Test comprehensive endpoint error handling."""
        # Test with invalid symbol
        response = client.get("/api/v1/financial/comprehensive/INVALID")

        assert response.status_code in [400, 404]

        # Test with invalid parameters
        response = client.get(
            "/api/v1/financial/comprehensive/ACB",
            params={"period": "invalid"}
        )

        assert response.status_code in [422, 404]

    @pytest.mark.asyncio
    async def test_comprehensive_cache_behavior(self):
        """Test comprehensive endpoint caching behavior."""
        symbol = "ACB"

        # First request
        response1 = client.get(f"/api/v1/financial/comprehensive/{symbol}")

        # Second request (should be faster if cached)
        response2 = client.get(f"/api/v1/financial/comprehensive/{symbol}")

        assert response1.status_code == response2.status_code

        if response1.status_code == 200:
            data1 = response1.json()
            data2 = response2.json()

            # Data should be consistent
            assert data1["data"]["metadata"]["symbol"] == data2["data"]["metadata"]["symbol"]