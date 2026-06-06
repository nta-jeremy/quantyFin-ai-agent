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
    from app.services.scrapers import CafeFScraper, VnEconomyScraper
    
    scraped_sources = []
    
    def mock_scrape_cafef(self, client):
        scraped_sources.append(self.source_name)
        return []

    def mock_scrape_vneconomy(self, client):
        scraped_sources.append(self.source_name)
        return []
        
    monkeypatch.setattr(CafeFScraper, "scrape", mock_scrape_cafef)
    monkeypatch.setattr(VnEconomyScraper, "scrape", mock_scrape_vneconomy)
    
    # Run ingestion with only cafef active
    results = ingest_news_articles(session, active_sources="cafef")
    
    # Assert CafeF was scraped, but VnEconomy (and others) were not
    assert "CafeF" in scraped_sources
    assert "VnEconomy" not in scraped_sources
    assert len(scraped_sources) == 1
