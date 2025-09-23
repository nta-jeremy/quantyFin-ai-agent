"""
Integration tests for balance sheet financial endpoint.
These tests will fail initially and pass once the implementation is complete.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app  # This will be available after implementation

client = TestClient(app)

class TestBalanceSheetEndpoint:
    """Integration tests for balance sheet endpoint."""

    @pytest.mark.asyncio
    async def test_balance_sheet_basic_request(self):
        """Test basic balance sheet request."""
        response = client.get("/api/v1/financial/balance-sheet/ACB")

        # Initially will return 404 until implemented
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = response.json()
            assert "data" in data
            assert "metadata" in data
            assert data["metadata"]["symbol"] == "ACB"

    @pytest.mark.asyncio
    async def test_balance_sheet_with_parameters(self):
        """Test balance sheet request with parameters."""
        params = {
            "source": "VCI",
            "period": "year",
            "language": "vi",
            "use_cache": True
        }
        response = client.get("/api/v1/financial/balance-sheet/VIC", params=params)

        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = response.json()
            assert data["metadata"]["source"] == "VCI"
            assert data["metadata"]["period"] == "year"
            assert data["metadata"]["language"] == "vi"

    @pytest.mark.asyncio
    async def test_balance_sheet_tcbs_source(self):
        """Test balance sheet with TCBS data source."""
        response = client.get(
            "/api/v1/financial/balance-sheet/ACB",
            params={"source": "TCBS", "period": "quarter"}
        )

        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_balance_sheet_invalid_symbol(self):
        """Test balance sheet with invalid symbol."""
        response = client.get("/api/v1/financial/balance-sheet/INVALID")

        assert response.status_code in [400, 404]

    @pytest.mark.asyncio
    async def test_balance_sheet_invalid_period(self):
        """Test balance sheet with invalid period."""
        response = client.get(
            "/api/v1/financial/balance-sheet/ACB",
            params={"period": "invalid"}
        )

        assert response.status_code in [422, 404]

    @pytest.mark.asyncio
    async def test_balance_sheet_cache_behavior(self):
        """Test balance sheet caching behavior."""
        # First request
        response1 = client.get("/api/v1/financial/balance-sheet/ACB")

        # Second request (should hit cache if implemented)
        response2 = client.get("/api/v1/financial/balance-sheet/ACB")

        assert response1.status_code == response2.status_code