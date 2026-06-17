import pytest
from datetime import datetime, date
from sqlmodel import Session, select
from unittest.mock import MagicMock, call

from app.models.news import NewsArticle
from app.models.stock import StockTicker, StockPrice
from app.models.entity import CanonicalEntity

# These imports will fail because the module doesn't exist yet, starting the RED phase
from app.services.neo4j_sync import (
    init_neo4j_constraints,
    sync_all_stocks_to_neo4j,
    sync_article_to_graph,
    process_graph_sync_batch,
)


@pytest.fixture
def mock_neo4j_session():
    session = MagicMock()
    # Mock return value for run() to return a result mock
    mock_result = MagicMock()
    mock_result.data.return_value = [{"result": 1}]
    session.run.return_value = mock_result
    return session


def test_init_neo4j_constraints(mock_neo4j_session):
    init_neo4j_constraints(mock_neo4j_session)
    assert mock_neo4j_session.run.call_count >= 5
    
    # Verify some expected queries
    calls = [c[0][0] for c in mock_neo4j_session.run.call_args_list]
    assert any("Article" in q and "UNIQUE" in q for q in calls)
    assert any("Stock" in q and "UNIQUE" in q for q in calls)


def test_sync_all_stocks_to_neo4j(session: Session, mock_neo4j_session):
    # Seed a StockTicker and a StockPrice
    ticker = StockTicker(ticker="VIC", name="Vingroup", market="HOSE", is_active=True)
    session.add(ticker)
    session.commit()
    
    price = StockPrice(
        ticker_id=ticker.id,
        date=date(2026, 6, 9),
        open=100.0,
        high=105.0,
        low=99.0,
        close=102.0,
        volume=100000
    )
    session.add(price)
    session.commit()
    
    sync_all_stocks_to_neo4j(session, mock_neo4j_session)
    
    # Check that session.run was called to MERGE Stock
    assert mock_neo4j_session.run.call_count >= 1
    calls = mock_neo4j_session.run.call_args_list
    merge_stock_call = [c for c in calls if "MERGE (s:Stock" in c[0][0]]
    assert len(merge_stock_call) > 0
    # merge_stock_call[0] is a call object: call(query, params)
    args, kwargs = merge_stock_call[0]
    params = args[1]
    assert params["ticker"] == "VIC"
    assert params["close"] == 102.0


def test_sync_article_to_graph(session: Session, mock_neo4j_session):
    # Seed StockTicker "VIC" to test stock linkage logic
    ticker = StockTicker(ticker="VIC", name="Vingroup", market="HOSE", is_active=True)
    session.add(ticker)
    session.commit()
    
    # Seed an article with resolved entities and relationships
    article = NewsArticle(
        title="VIC reports record earnings",
        content="Vingroup VIC reports growth.",
        published_at=datetime(2026, 6, 9, 10, 0, 0),
        url="https://news.example/vic-earnings",
        source="Example",
        sentiment_score=0.8,
        status="entities_resolved",
        resolved_entities=[
            {
                "canonical_id": "VIC",
                "name": "Tập đoàn Vingroup",
                "type": "COMPANY",
                "description": "Vingroup group"
            },
            {
                "canonical_id": "MR_VUONG",
                "name": "Phạm Nhật Vượng",
                "type": "PERSON",
                "description": "Chairman"
            }
        ],
        resolved_relationships=[
            {
                "source": "MR_VUONG",
                "target": "VIC",
                "type": "CHAIRMAN_OF"
            }
        ]
    )
    session.add(article)
    session.commit()
    
    active_tickers = {t.ticker: t for t in session.exec(select(StockTicker).where(StockTicker.is_active == True)).all()}
    sync_article_to_graph(session, mock_neo4j_session, article, active_tickers)
    
    calls = [c[0][0] for c in mock_neo4j_session.run.call_args_list]
    # Check Article merged
    assert any("MERGE (a:Article" in q for q in calls)
    # Check Company merged
    assert any("MERGE (e:Company" in q for q in calls)
    # Check Person merged
    assert any("MERGE (e:Person" in q for q in calls)
    # Check mentions relation merged
    assert any("MERGE (a)-[r:MENTIONS]->(e)" in q or "MERGE (a)-[r:MENTIONS]->(s)" in q for q in calls)
    # Check custom relationship merged
    assert any("MERGE (src)-[r:CHAIRMAN_OF]->(tgt)" in q for q in calls)


def test_process_graph_sync_batch(session: Session, monkeypatch):
    # Mock Neo4j Driver and session inside process_graph_sync_batch
    mock_driver = MagicMock()
    mock_neo4j_session = MagicMock()
    mock_driver.session.return_value.__enter__.return_value = mock_neo4j_session
    
    mock_result = MagicMock()
    mock_result.data.return_value = [{"result": 1}]
    mock_neo4j_session.run.return_value = mock_result
    
    from app.core.neo4j import neo4j_manager
    monkeypatch.setattr(neo4j_manager, "get_driver", lambda: mock_driver)

    # Seed an article
    article = NewsArticle(
        title="VIC reports record earnings",
        content="Vingroup VIC reports growth.",
        published_at=datetime(2026, 6, 9, 10, 0, 0),
        url="https://news.example/vic-earnings-batch",
        source="Example",
        sentiment_score=0.8,
        status="entities_resolved",
        resolved_entities=[
            {"canonical_id": "VIC", "name": "Vingroup", "type": "COMPANY"}
        ],
        resolved_relationships=[]
    )
    session.add(article)
    session.commit()
    
    # Mock the sync_article_to_graph to verify it's called
    sync_mock = MagicMock()
    monkeypatch.setattr("app.services.neo4j_sync.sync_article_to_graph", sync_mock)
    
    stats = process_graph_sync_batch(session)
    
    assert stats["total"] == 1
    assert stats["processed"] == 1
    assert stats["failed"] == 0
    
    # Check that article status updated in database
    session.refresh(article)
    assert article.status == "synced_to_graph"
    
    # Verify sync_mock was called
    assert sync_mock.call_count == 1
