import asyncio
import pytest
from sqlmodel import Session
from app.models.crawler_config import CrawlerConfig
from app.main import scheduled_crawler_task
from app.services.crawler import ingest_news_articles

@pytest.mark.asyncio
async def test_scheduler_dynamic_reload(session: Session):
    # 1. Insert initial config in database
    config = CrawlerConfig(id=1, schedule_time="22:00", active_sources="cafef,vietstock")
    session.add(config)
    session.commit()

    # 2. Create the update event
    event = asyncio.Event()

    # 3. Start scheduler task in background
    task = asyncio.create_task(scheduled_crawler_task(event))

    # Let the scheduler run and query DB
    await asyncio.sleep(0.1)

    # Update config in database
    config.schedule_time = "12:00"
    config.active_sources = "vneconomy"
    session.add(config)
    session.commit()

    # Trigger the event
    event.set()
    assert event.is_set() is True

    # Let the scheduler process the event
    await asyncio.sleep(0.2)

    # The event should be cleared by the scheduler after reloading
    assert event.is_set() is False

    # Cancel the scheduler task
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

def test_ingest_news_articles_with_active_sources(session: Session, monkeypatch):
    import app.services.crawler as crawler_mod

    discovered_sources = []

    def mock_discover_rss(source, client):
        discovered_sources.append(source.name)
        return [], "empty"

    monkeypatch.setattr(crawler_mod, "discover_rss", mock_discover_rss)

    # Run ingestion with only cafef active (R13.1: chỉ thu thập nguồn cấu hình).
    results = ingest_news_articles(session, active_sources="cafef")

    # Chỉ nguồn CafeF được discovery; các nguồn khác trong registry bị bỏ qua.
    assert "CafeF" in discovered_sources
    assert "TuoiTre" not in discovered_sources
    assert len(discovered_sources) == 1
    assert [h["source"] for h in results["source_health"]] == ["CafeF"]
