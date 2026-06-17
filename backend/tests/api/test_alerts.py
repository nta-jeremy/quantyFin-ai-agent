import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select
import datetime as dt

from app.models.stock import StockTicker
from app.models.alert import AlertRule, TriggeredAlert

def test_get_alerts_empty(client: TestClient):
    response = client.get("/api/v1/alerts")
    assert response.status_code == 200
    json_data = response.json()
    assert "data" in json_data
    assert len(json_data["data"]) == 0


def test_create_and_get_rules(client: TestClient, session: Session):
    # Seed stock ticker
    ticker = StockTicker(id=10, ticker="FPT", name="FPT Corp", market="HOSE")
    session.add(ticker)
    session.commit()

    # Create rule via API
    payload = {
        "tickerId": 10,
        "priceThreshold": -0.05,
        "sentimentThreshold": -0.4,
        "isActive": True
    }
    response = client.post("/api/v1/alerts/rules", json=payload)
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["data"]["tickerId"] == 10
    assert json_data["data"]["priceThreshold"] == -0.05
    assert json_data["data"]["sentimentThreshold"] == -0.4

    # Get rules via API
    get_resp = client.get("/api/v1/alerts/rules")
    assert get_resp.status_code == 200
    rules_data = get_resp.json()["data"]
    assert len(rules_data) == 1
    assert rules_data[0]["ticker"] == "FPT"
    assert rules_data[0]["tickerId"] == 10


def test_update_existing_rule(client: TestClient, session: Session):
    ticker = StockTicker(id=11, ticker="VNM", name="Vinamilk", market="HOSE")
    session.add(ticker)
    session.commit()

    # Create initial rule in DB
    rule = AlertRule(ticker_id=11, price_threshold=-0.03, sentiment_threshold=-0.5, is_active=True)
    session.add(rule)
    session.commit()

    # Update via API
    payload = {
        "tickerId": 11,
        "priceThreshold": -0.04,
        "sentimentThreshold": -0.6,
        "isActive": False
    }
    response = client.post("/api/v1/alerts/rules", json=payload)
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["data"]["priceThreshold"] == -0.04
    assert json_data["data"]["sentimentThreshold"] == -0.6
    assert not json_data["data"]["isActive"]


def test_dismiss_alert(client: TestClient, session: Session):
    # Seed triggered alert
    alert = TriggeredAlert(
        id=100,
        ticker="VIC",
        level="warning",
        title="VIC Alert",
        message="VIC price fell",
        is_dismissed=False,
        triggered_at=dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)
    )
    session.add(alert)
    session.commit()

    # Dismiss via API
    response = client.post("/api/v1/alerts/100/dismiss")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["data"]["isDismissed"] is True

    # Check database status
    session.refresh(alert)
    assert alert.is_dismissed is True


def test_dismiss_non_existent_alert(client: TestClient):
    response = client.post("/api/v1/alerts/9999/dismiss")
    assert response.status_code == 404


def test_trigger_process_monitor(client: TestClient, session: Session, monkeypatch):
    # Mock check_and_trigger_alerts
    mock_triggered = [
        TriggeredAlert(
            id=1,
            ticker="VIC",
            level="critical",
            title="VIC Critical Alert",
            message="VIC sentiment scan failed",
            is_dismissed=False,
            triggered_at=dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)
        )
    ]
    monkeypatch.setattr(
        "app.api.v1.alerts.check_and_trigger_alerts",
        lambda s: mock_triggered
    )

    response = client.post("/api/v1/alerts/process-monitor")
    assert response.status_code == 200
    json_data = response.json()
    assert "data" in json_data
    assert len(json_data["data"]) == 1
    assert json_data["data"][0]["ticker"] == "VIC"
    assert json_data["data"][0]["level"] == "critical"
