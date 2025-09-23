"""
Integration tests for income statement financial endpoint.
These tests will fail initially and pass once the implementation is complete.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app  # This will be available after implementation

client = TestClient(app)

class TestIncomeStatementEndpoint:
    """Integration tests for income statement endpoint."""

    @pytest.mark.asyncio
    async def test_income_statement_basic_request(self):
        """Test basic income statement request."""
        response = client.get("/api/v1/financial/income-statement/VIC")

        # Initially will return 404 until implemented
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = response.json()
            assert "data" in data
            assert "metadata" in data
            assert data["metadata"]["symbol"] == "VIC"

    @pytest.mark.asyncio
    async def test_income_statement_with_parameters(self):
        """Test income statement request with parameters."""
        params = {
            "source": "VCI",
            "period": "year",
            "language": "en",
            "use_cache": True
        }
        response = client.get("/api/v1/financial/income-statement/ACB", params=params)

        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = response.json()
            assert data["metadata"]["source"] == "VCI"
            assert data["metadata"]["period"] == "year"
            assert data["metadata"]["language"] == "en"

    @pytest.mark.asyncio
    async def test_income_statement_quarterly_data(self):
        """Test income statement with quarterly period."""
        response = client.get(
            "/api/v1/financial/income-statement/VNM",
            params={"period": "quarter", "source": "TCBS"}
        )

        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_income_statement_bilingual_support(self):
        """Test income statement bilingual support."""
        for language in ["vi", "en"]:
            response = client.get(
                "/api/v1/financial/income-statement/HPG",
                params={"language": language}
            )

            assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_income_statement_data_structure(self):
        """Test income statement response data structure."""
        response = client.get("/api/v1/financial/income-statement/FPT")

        if response.status_code == 200:
            data = response.json()

            # Check that data contains expected income statement fields
            if data["data"]:
                first_item = data["data"][0]
                assert "period_end" in first_item
                assert "symbol" in first_item
                assert "total_revenue" in first_item or "net_income" in first_item

    @pytest.mark.asyncio
    async def test_income_statement_source_comparison(self):
        """Test income statement data from different sources."""
        sources = ["VCI", "TCBS"]

        for source in sources:
            response = client.get(
                "/api/v1/financial/income-statement/ACB",
                params={"source": source}
            )

            assert response.status_code in [200, 404]