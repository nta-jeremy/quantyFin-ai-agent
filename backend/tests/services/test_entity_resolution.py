import pytest
from datetime import datetime
from sqlmodel import Session, select

from app.models.entity import CanonicalEntity, EntitySynonym
from app.models.news import NewsArticle
from app.models.stock import StockTicker
from app.services.entity_resolution import (
    resolve_entity,
    resolve_article_entities_and_relationships,
    process_resolved_entities_batch,
    normalize_text,
)


@pytest.fixture
def seed_tickers(session: Session):
    """Seed test stock tickers."""
    tickers = [
        StockTicker(ticker="VIC", name="Tập đoàn Vingroup - CTCP", market="HOSE", is_active=True),
        StockTicker(ticker="VNM", name="Công ty Cổ phần Sữa Việt Nam", market="HOSE", is_active=True),
        StockTicker(ticker="FPT", name="Công ty Cổ phần FPT", market="HOSE", is_active=True),
    ]
    for t in tickers:
        session.add(t)
    session.commit()
    return tickers


@pytest.fixture
def seed_canonical(session: Session, seed_tickers):
    """Seed canonical entities and synonyms."""
    canonicals = [
        CanonicalEntity(id="VIC", name="Tập đoàn Vingroup - CTCP", type="COMPANY"),
        CanonicalEntity(id="VNM", name="Công ty Cổ phần Sữa Việt Nam", type="COMPANY"),
    ]
    for c in canonicals:
        session.add(c)
    session.commit()
    
    synonyms = [
        EntitySynonym(synonym="vic", canonical_id="VIC"),
        EntitySynonym(synonym="vingroup", canonical_id="VIC"),
        EntitySynonym(synonym="tập đoàn vingroup", canonical_id="VIC"),
        EntitySynonym(synonym="vnm", canonical_id="VNM"),
        EntitySynonym(synonym="vinamilk", canonical_id="VNM"),
    ]
    for s in synonyms:
        session.add(s)
    session.commit()
    return canonicals


class TestNormalizeText:
    def test_normalize_basic(self):
        assert normalize_text("  Hello World  ") == "hello world"
    
    def test_normalize_empty(self):
        assert normalize_text("") == ""
    
    def test_normalize_already_normalized(self):
        assert normalize_text("test") == "test"


class TestResolveEntity:
    def test_resolve_existing_synonym(self, session: Session, seed_canonical):
        """Test resolving an existing synonym returns correct canonical ID."""
        result = resolve_entity(session, "Vingroup", "COMPANY")
        assert result == "VIC"
    
    def test_resolve_case_insensitive(self, session: Session, seed_canonical):
        """Test resolving is case insensitive."""
        result = resolve_entity(session, "vingroup", "COMPANY")
        assert result == "VIC"
    
    def test_resolve_exact_ticker_match(self, session: Session, seed_tickers):
        """Test resolving by exact ticker match."""
        result = resolve_entity(session, "FPT", "COMPANY")
        assert result == "FPT"
    
    def test_resolve_creates_new_entity(self, session: Session, seed_canonical):
        """Test resolving unknown entity creates new canonical entity."""
        result = resolve_entity(session, "Unknown Company", "COMPANY", "A test company")
        
        assert result is not None
        canonical = session.exec(select(CanonicalEntity).where(CanonicalEntity.id == result)).first()
        assert canonical is not None
        assert canonical.name == "Unknown Company"
        assert canonical.type == "COMPANY"
    
    def test_resolve_substring_match(self, session: Session, seed_canonical):
        """Test resolving by substring matching."""
        result = resolve_entity(session, "Công ty Cổ phần Vingroup", "COMPANY")
        assert result == "VIC"
    
    def test_resolve_adds_synonym(self, session: Session, seed_canonical):
        """Test that resolving adds a new synonym."""
        resolve_entity(session, "New Alias for VIC", "COMPANY")
        
        syn = session.exec(
            select(EntitySynonym).where(EntitySynonym.synonym == "new alias for vic")
        ).first()
        assert syn is not None


class TestResolveArticleEntitiesAndRelationships:
    def test_resolve_article_entities(self, session: Session, seed_canonical):
        """Test resolving entities in an article."""
        article = NewsArticle(
            title="Test Article",
            content="Vingroup vừa công bố dự án mới.",
            published_at=datetime(2026, 1, 1, 0, 0, 0),
            url="http://test.com/1",
            source="TestSource",
            status="extraction_completed",
            raw_entities=[
                {"name": "Vingroup", "type": "COMPANY"},
                {"name": "Vinamilk", "type": "COMPANY"},
            ],
            raw_relationships=[
                {"source": "Vingroup", "target": "Vinamilk", "type": "PARTNER_OF"}
            ]
        )
        session.add(article)
        session.commit()
        
        resolve_article_entities_and_relationships(session, article)
        session.commit()
        
        assert article.resolved_entities is not None
        assert len(article.resolved_entities) == 2
        
        canonical_ids = [e["canonical_id"] for e in article.resolved_entities]
        assert "VIC" in canonical_ids
        assert "VNM" in canonical_ids
        
        assert article.resolved_relationships is not None
        assert len(article.resolved_relationships) == 1
        assert article.resolved_relationships[0]["source"] == "VIC"
        assert article.resolved_relationships[0]["target"] == "VNM"
        
        assert article.status == "entities_resolved"
    
    def test_resolve_article_no_entities(self, session: Session, seed_canonical):
        """Test article with no raw_entities."""
        article = NewsArticle(
            title="Test Article",
            content="No entities here.",
            published_at=datetime(2026, 1, 1, 0, 0, 0),
            url="http://test.com/2",
            source="TestSource",
            status="extraction_completed",
            raw_entities=None
        )
        session.add(article)
        session.commit()
        
        resolve_article_entities_and_relationships(session, article)
        
        assert article.resolved_entities is None


class TestProcessResolvedEntitiesBatch:
    def test_batch_processing(self, session: Session, seed_canonical):
        """Test batch processing of multiple articles."""
        for i in range(3):
            article = NewsArticle(
                title=f"Test Article {i}",
                content=f"Article {i} about Vingroup.",
                published_at=datetime(2026, 1, 1, 0, 0, 0),
                url=f"http://test.com/batch/{i}",
                source="TestSource",
                status="extraction_completed",
                raw_entities=[{"name": "Vingroup", "type": "COMPANY"}],
                raw_relationships=[]
            )
            session.add(article)
        session.commit()
        
        stats = process_resolved_entities_batch(session)
        
        assert stats["total"] == 3
        assert stats["processed"] == 3
        assert stats["failed"] == 0
    
    def test_batch_handles_errors(self, session: Session, seed_canonical, monkeypatch):
        """Test batch processing handles errors gracefully."""
        article = NewsArticle(
            title="Error Article",
            content="This will fail.",
            published_at=datetime(2026, 1, 1, 0, 0, 0),
            url="http://test.com/error",
            source="TestSource",
            status="extraction_completed",
            raw_entities=[{"name": "Test", "type": "COMPANY"}],
            raw_relationships=[]
        )
        session.add(article)
        session.commit()
        
        def mock_resolve(*args, **kwargs):
            raise Exception("Simulated error")
        
        monkeypatch.setattr(
            "app.services.entity_resolution.resolve_article_entities_and_relationships",
            mock_resolve
        )
        
        stats = process_resolved_entities_batch(session)
        
        assert stats["failed"] == 1
        assert len(stats["errors"]) == 1
        
        updated_article = session.exec(
            select(NewsArticle).where(NewsArticle.url == "http://test.com/error")
        ).first()
        assert updated_article.status == "resolution_failed"


class TestCanonicalEntityCreation:
    def test_new_entity_has_synonym(self, session: Session, seed_canonical):
        """Test that new canonical entity has itself as synonym."""
        result = resolve_entity(session, "Brand New Company", "COMPANY")
        
        syn = session.exec(
            select(EntitySynonym).where(EntitySynonym.synonym == "brand new company")
        ).first()
        assert syn is not None
        assert syn.canonical_id == result
