import pytest
import pandas as pd
from datetime import date, datetime
from sqlmodel import Session, select

from app.models.stock import StockTicker, StockPrice
from app.services.stock_data import fetch_stock_prices, upsert_stock_prices, ingest_all_active_tickers
from app.core.exceptions import CrawlerException

@pytest.fixture
def mock_vnstock(monkeypatch):
    class MockQuote:
        def history(self, *args, **kwargs):
            return pd.DataFrame([
                {"time": "2026-06-05", "open": 100.0, "high": 105.0, "low": 98.0, "close": 102.0, "volume": 1500000},
                {"time": "2026-06-06", "open": 102.0, "high": 107.0, "low": 101.0, "close": 106.0, "volume": 1800000}
            ])
            
    class MockStock:
        quote = MockQuote()
        
    class MockVnstock:
        def stock(self, symbol, source):
            return MockStock()
            
    monkeypatch.setattr("vnstock.Vnstock", MockVnstock)


def test_fetch_stock_prices(mock_vnstock):
    prices = fetch_stock_prices("VNM", "2026-06-05", "2026-06-06")
    assert len(prices) == 2
    assert prices[0]["date"] == date(2026, 6, 5)
    assert prices[0]["open"] == 100.0
    assert prices[0]["close"] == 102.0
    assert prices[0]["volume"] == 1500000
    
    assert prices[1]["date"] == date(2026, 6, 6)
    assert prices[1]["close"] == 106.0


def test_upsert_stock_prices(session: Session):
    # Setup: Create a ticker first
    ticker = StockTicker(ticker="FPT", name="Công ty Cổ phần FPT", market="HOSE", is_active=True)
    session.add(ticker)
    session.commit()
    session.refresh(ticker)
    
    # Ingest some prices
    prices_data = [
        {
            "ticker_id": ticker.id,
            "date": date(2026, 6, 5),
            "open": 100.0,
            "high": 105.0,
            "low": 98.0,
            "close": 102.0,
            "volume": 1500000
        }
    ]
    
    upsert_stock_prices(session, prices_data)
    
    # Verify insert
    prices = session.exec(select(StockPrice).where(StockPrice.ticker_id == ticker.id)).all()
    assert len(prices) == 1
    assert prices[0].close == 102.0
    
    # Try to upsert the same row with different values (simulate ON CONFLICT)
    updated_prices_data = [
        {
            "ticker_id": ticker.id,
            "date": date(2026, 6, 5),
            "open": 100.0,
            "high": 108.0, # Updated
            "low": 98.0,
            "close": 105.0, # Updated
            "volume": 1600000 # Updated
        }
    ]
    
    upsert_stock_prices(session, updated_prices_data)
    
    # Verify update occurred, no duplicate record
    session.expire_all()
    prices = session.exec(select(StockPrice).where(StockPrice.ticker_id == ticker.id)).all()
    assert len(prices) == 1
    assert prices[0].close == 105.0
    assert prices[0].high == 108.0
    assert prices[0].volume == 1600000


def test_ingest_all_active_tickers(session: Session, mock_vnstock, monkeypatch):
    # Setup: Create tickers (one active, one inactive)
    active_ticker = StockTicker(ticker="VIC", name="Tập đoàn Vingroup", market="HOSE", is_active=True)
    inactive_ticker = StockTicker(ticker="VNM", name="Vinamilk", market="HOSE", is_active=False)
    session.add(active_ticker)
    session.add(inactive_ticker)
    session.commit()
    session.refresh(active_ticker)
    session.refresh(inactive_ticker)
    
    # Mock time.sleep to run tests instantly
    monkeypatch.setattr("time.sleep", lambda x: None)
    
    # Run ingestion
    results = ingest_all_active_tickers(session, "2026-06-05", "2026-06-06")
    
    # Verify results
    assert results["success_count"] == 1
    assert "VIC" in results["details"]
    assert "VNM" not in results["details"] # Inactive ticker should be skipped
    
    # Check that price records exist in db for VIC
    prices = session.exec(select(StockPrice).where(StockPrice.ticker_id == active_ticker.id)).all()
    assert len(prices) == 2
