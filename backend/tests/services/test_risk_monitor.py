import pytest
import datetime as dt
from sqlmodel import Session, select
from unittest.mock import MagicMock

from app.models.stock import StockTicker, StockPrice
from app.models.alert import AlertRule, TriggeredAlert
from app.services.risk_monitor import (
    evaluate_price_risk,
    evaluate_sentiment_risk,
    evaluate_indirect_sentiment_risk,
    check_and_trigger_alerts
)

@pytest.fixture
def mock_neo4j(monkeypatch):
    mock_driver = MagicMock()
    mock_session = MagicMock()
    mock_driver.session.return_value.__enter__.return_value = mock_session
    
    from app.core.neo4j import neo4j_manager
    monkeypatch.setattr(neo4j_manager, "get_driver", lambda: mock_driver)
    
    return mock_session


def test_evaluate_price_risk_insufficient_data(session: Session):
    # Seed a StockTicker but no prices
    ticker = StockTicker(ticker="VIC", name="Vingroup", market="HOSE")
    session.add(ticker)
    session.commit()
    
    is_trig, val, msg = evaluate_price_risk(session, ticker.id, -0.03)
    assert not is_trig
    assert "Không đủ dữ liệu giá" in msg


def test_evaluate_price_risk_triggered(session: Session):
    ticker = StockTicker(ticker="VIC", name="Vingroup", market="HOSE")
    session.add(ticker)
    session.commit()
    
    # Phiên trước: 100, Phiên mới: 96 (giảm 4%)
    p1 = StockPrice(ticker_id=ticker.id, date=dt.date(2026, 6, 8), open=100, high=100, low=100, close=100, volume=1000)
    p2 = StockPrice(ticker_id=ticker.id, date=dt.date(2026, 6, 9), open=100, high=100, low=96, close=96, volume=1000)
    session.add_all([p1, p2])
    session.commit()
    
    is_trig, val, msg = evaluate_price_risk(session, ticker.id, -0.03)
    assert is_trig
    assert val == -0.04
    assert "-4.00%" in msg


def test_evaluate_price_risk_not_triggered(session: Session):
    ticker = StockTicker(ticker="VIC", name="Vingroup", market="HOSE")
    session.add(ticker)
    session.commit()
    
    # Phiên trước: 100, Phiên mới: 99 (giảm 1% - chưa vượt ngưỡng -3%)
    p1 = StockPrice(ticker_id=ticker.id, date=dt.date(2026, 6, 8), open=100, high=100, low=100, close=100, volume=1000)
    p2 = StockPrice(ticker_id=ticker.id, date=dt.date(2026, 6, 9), open=100, high=100, low=99, close=99, volume=1000)
    session.add_all([p1, p2])
    session.commit()
    
    is_trig, val, msg = evaluate_price_risk(session, ticker.id, -0.03)
    assert not is_trig
    assert val == -0.01


def test_evaluate_sentiment_risk(mock_neo4j):
    # Mock Neo4j session.run return value
    mock_record1 = {"title": "VIC scandal", "sentimentScore": -0.7, "url": "https://url1"}
    mock_record2 = {"title": "VIC bad sales", "sentimentScore": -0.6, "url": "https://url2"}
    mock_neo4j.run.return_value = [mock_record1, mock_record2]
    
    is_trig, min_s, articles = evaluate_sentiment_risk("VIC", -0.5)
    assert is_trig
    assert min_s == -0.7
    assert len(articles) == 2
    assert articles[0]["title"] == "VIC scandal"


def test_check_and_trigger_alerts_critical(session: Session, mock_neo4j):
    # Seed StockTicker
    ticker = StockTicker(ticker="VIC", name="Vingroup", market="HOSE")
    session.add(ticker)
    session.commit()
    
    # Price drop 4%
    p1 = StockPrice(ticker_id=ticker.id, date=dt.date(2026, 6, 8), open=100, high=100, low=100, close=100, volume=1000)
    p2 = StockPrice(ticker_id=ticker.id, date=dt.date(2026, 6, 9), open=100, high=100, low=96, close=96, volume=1000)
    session.add_all([p1, p2])
    
    # Active AlertRule
    rule = AlertRule(ticker_id=ticker.id, price_threshold=-0.03, sentiment_threshold=-0.5, is_active=True)
    session.add(rule)
    session.commit()
    
    # Mock Neo4j direct negative article
    mock_record = {"title": "VIC negative news", "sentimentScore": -0.8, "url": "https://news"}
    mock_neo4j.run.return_value = [mock_record]
    
    alerts = check_and_trigger_alerts(session)
    assert len(alerts) == 1
    alert = alerts[0]
    assert alert.level == "critical"
    assert alert.ticker == "VIC"
    assert "nguy cấp" in alert.title.lower()
    
    # Verify saved in DB
    saved_alert = session.get(TriggeredAlert, alert.id)
    assert saved_alert is not None
    assert not saved_alert.is_dismissed


def test_check_and_trigger_alerts_warning(session: Session, mock_neo4j):
    ticker = StockTicker(ticker="VIC", name="Vingroup", market="HOSE")
    session.add(ticker)
    session.commit()
    
    # Price unchanged (no price drop)
    p1 = StockPrice(ticker_id=ticker.id, date=dt.date(2026, 6, 8), open=100, high=100, low=100, close=100, volume=1000)
    p2 = StockPrice(ticker_id=ticker.id, date=dt.date(2026, 6, 9), open=100, high=100, low=100, close=100, volume=1000)
    session.add_all([p1, p2])
    
    rule = AlertRule(ticker_id=ticker.id, price_threshold=-0.03, sentiment_threshold=-0.5, is_active=True)
    session.add(rule)
    session.commit()
    
    # Mock Neo4j negative article (sentiment triggered, but price not triggered -> Warning)
    mock_record = {"title": "VIC negative news", "sentimentScore": -0.8, "url": "https://news"}
    mock_neo4j.run.return_value = [mock_record]
    
    alerts = check_and_trigger_alerts(session)
    assert len(alerts) == 1
    assert alerts[0].level == "warning"


def test_check_and_trigger_alerts_warning_price_only(session: Session, mock_neo4j):
    ticker = StockTicker(ticker="VIC", name="Vingroup", market="HOSE")
    session.add(ticker)
    session.commit()
    
    # Price drop 4%
    p1 = StockPrice(ticker_id=ticker.id, date=dt.date(2026, 6, 8), open=100, high=100, low=100, close=100, volume=1000)
    p2 = StockPrice(ticker_id=ticker.id, date=dt.date(2026, 6, 9), open=100, high=100, low=96, close=96, volume=1000)
    session.add_all([p1, p2])
    
    rule = AlertRule(ticker_id=ticker.id, price_threshold=-0.03, sentiment_threshold=-0.5, is_active=True)
    session.add(rule)
    session.commit()
    
    # Mock Neo4j mild negative news (sentiment = -0.2, which is <= -0.1 to combine with price, but not <= -0.5 for direct sentiment)
    mock_record = {"title": "VIC mild news", "sentimentScore": -0.2, "url": "https://news"}
    
    def mock_run(query, params):
        threshold = params.get("threshold", 0.0)
        if threshold <= -0.5:
            return []
        return [mock_record]
        
    mock_neo4j.run.side_effect = mock_run
    
    alerts = check_and_trigger_alerts(session)
    assert len(alerts) == 1
    assert alerts[0].level == "warning"
    assert "Biến động giá vượt ngưỡng" in alerts[0].message
    assert "VIC mild news" in alerts[0].message


def test_check_and_trigger_alerts_anti_spam(session: Session, mock_neo4j):
    ticker = StockTicker(ticker="VIC", name="Vingroup", market="HOSE")
    session.add(ticker)
    session.commit()
    
    p1 = StockPrice(ticker_id=ticker.id, date=dt.date(2026, 6, 8), open=100, high=100, low=100, close=100, volume=1000)
    p2 = StockPrice(ticker_id=ticker.id, date=dt.date(2026, 6, 9), open=100, high=100, low=96, close=96, volume=1000)
    session.add_all([p1, p2])
    
    rule = AlertRule(ticker_id=ticker.id, price_threshold=-0.03, sentiment_threshold=-0.5, is_active=True)
    session.add(rule)
    session.flush()
    
    # Seed an alert already triggered in the last 2 hours (less than 24 hours)
    existing_alert = TriggeredAlert(
        rule_id=rule.id,
        ticker="VIC",
        level="critical",
        title="Spam test",
        message="Already triggered",
        triggered_at=dt.datetime.now(dt.timezone.utc).replace(tzinfo=None) - dt.timedelta(hours=2)
    )
    session.add(existing_alert)
    session.commit()
    
    # Mock Neo4j direct negative article (would trigger Critical again)
    mock_record = {"title": "VIC negative news", "sentimentScore": -0.8, "url": "https://news"}
    mock_neo4j.run.return_value = [mock_record]
    
    alerts = check_and_trigger_alerts(session)
    # Anti-spam should skip triggering because Critical is suppressed anyway
    assert len(alerts) == 0


def test_check_and_trigger_alerts_warning_anti_spam_selective(session: Session, mock_neo4j):
    ticker = StockTicker(ticker="VIC", name="Vingroup", market="HOSE")
    session.add(ticker)
    session.commit()
    
    # Price drop 4%
    p1 = StockPrice(ticker_id=ticker.id, date=dt.date(2026, 6, 8), open=100, high=100, low=100, close=100, volume=1000)
    p2 = StockPrice(ticker_id=ticker.id, date=dt.date(2026, 6, 9), open=100, high=100, low=96, close=96, volume=1000)
    session.add_all([p1, p2])
    
    rule = AlertRule(ticker_id=ticker.id, price_threshold=-0.03, sentiment_threshold=-0.5, is_active=True)
    session.add(rule)
    session.flush()
    
    # Seed warning alert due to price drop
    existing_alert = TriggeredAlert(
        rule_id=rule.id,
        ticker="VIC",
        level="warning",
        title="Price Warning",
        message="- Biến động giá vượt ngưỡng: Giá đóng cửa giảm 4%",
        triggered_at=dt.datetime.now(dt.timezone.utc).replace(tzinfo=None) - dt.timedelta(hours=2)
    )
    session.add(existing_alert)
    session.commit()
    
    # Price is now unchanged (no price drop), but sentiment is triggered (sentiment <= -0.5)
    # This should trigger Warning due to sentiment, and NOT be suppressed by the existing price warning!
    p3 = StockPrice(ticker_id=ticker.id, date=dt.date(2026, 6, 10), open=96, high=96, low=96, close=96, volume=1000)
    session.add(p3)
    session.commit()
    
    mock_record = {"title": "VIC severe news", "sentimentScore": -0.8, "url": "https://news"}
    mock_neo4j.run.return_value = [mock_record]
    
    alerts = check_and_trigger_alerts(session)
    # Selective anti-spam should allow sentiment warning to trigger
    assert len(alerts) == 1
    assert alerts[0].level == "warning"
    assert "Tin tức tiêu cực trực tiếp" in alerts[0].message
