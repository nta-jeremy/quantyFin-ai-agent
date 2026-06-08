import pytest
import pandas as pd
from fastapi.testclient import TestClient
from app.models.stock import StockTicker, StockPrice

from sqlmodel import Session

@pytest.fixture(autouse=True)
def seed_test_db(session: Session):
    initial_tickers = [
        {"ticker": "VNINDEX", "name": "Chỉ số VN-Index", "market": "HOSE"},
        {"ticker": "VIC", "name": "Tập đoàn Vingroup - CTCP", "market": "HOSE"},
        {"ticker": "VNM", "name": "Công ty Cổ phần Sữa Việt Nam", "market": "HOSE"},
        {"ticker": "FPT", "name": "Công ty Cổ phần FPT", "market": "HOSE"},
    ]
    for ticker_data in initial_tickers:
        new_ticker = StockTicker(
            ticker=ticker_data["ticker"],
            name=ticker_data["name"],
            market=ticker_data["market"],
            is_active=True
        )
        session.add(new_ticker)
    session.commit()

@pytest.fixture
def mock_vnstock_api(monkeypatch):
    class MockQuote:
        def history(self, *args, **kwargs):
            return pd.DataFrame([
                {"time": "2026-06-05", "open": 100.0, "high": 105.0, "low": 98.0, "close": 102.0, "volume": 1500000}
            ])
            
    class MockStock:
        quote = MockQuote()
        
    class MockVnstock:
        def stock(self, symbol, source):
            return MockStock()
            
    monkeypatch.setattr("vnstock.Vnstock", MockVnstock)
    monkeypatch.setattr("time.sleep", lambda x: None)


def test_get_tickers(client: TestClient):
    """
    Test retrieving active tickers.
    """
    response = client.get("/api/v1/stocks/tickers")
    assert response.status_code == 200
    json_data = response.json()
    
    assert "data" in json_data
    assert json_data["error"] is None
    assert "meta" in json_data
    assert "trace_id" in json_data["meta"]
    
    tickers = json_data["data"]
    # Seed data on startup includes 4 tickers (VNINDEX, VIC, VNM, FPT)
    assert len(tickers) == 4
    ticker_symbols = [t["ticker"] for t in tickers]
    assert "VNINDEX" in ticker_symbols
    assert "VIC" in ticker_symbols
    assert "VNM" in ticker_symbols
    assert "FPT" in ticker_symbols
    
    for t in tickers:
        assert "id" in t
        assert "ticker" in t
        assert "name" in t
        assert "market" in t
        assert "isActive" in t


def test_post_ingest_and_get_prices(client: TestClient, mock_vnstock_api):
    """
    Test triggering ingestion and then retrieving the ingested prices.
    """
    response = client.post("/api/v1/stocks/ingest?start_date=2026-06-05&end_date=2026-06-05")
    assert response.status_code == 200
    json_data = response.json()
    
    assert "data" in json_data
    assert json_data["error"] is None
    assert json_data["data"]["successCount"] == 4
    assert len(json_data["data"]["failedTickers"]) == 0
    
    # Retrieve FPT prices
    response_prices = client.get("/api/v1/stocks/prices?ticker=FPT&start_date=2026-06-05&end_date=2026-06-05")
    assert response_prices.status_code == 200
    prices_data = response_prices.json()
    
    assert "data" in prices_data
    assert prices_data["error"] is None
    assert len(prices_data["data"]) == 1
    
    price_rec = prices_data["data"][0]
    assert price_rec["tickerId"] is not None
    assert price_rec["date"] == "2026-06-05"
    assert price_rec["open"] == 100.0
    assert price_rec["high"] == 105.0
    assert price_rec["low"] == 98.0
    assert price_rec["close"] == 102.0
    assert price_rec["volume"] == 1500000


def test_get_prices_not_found(client: TestClient):
    """
    Test retrieving price data for a ticker that does not exist.
    """
    response = client.get("/api/v1/stocks/prices?ticker=NONEXISTENT")
    assert response.status_code == 400
    json_data = response.json()
    assert json_data["data"] is None
    assert json_data["error"]["code"] == "BAD_REQUEST"
    assert "NONEXISTENT" in json_data["error"]["message"]


def test_get_prices_invalid_date(client: TestClient):
    """
    Test retrieving price data with an invalid date format.
    """
    response = client.get("/api/v1/stocks/prices?ticker=FPT&start_date=invalid")
    assert response.status_code == 400
    json_data = response.json()
    assert json_data["data"] is None
    assert json_data["error"]["code"] == "BAD_REQUEST"
