import pytest
import datetime as dt
from sqlmodel import Session, select
from app.models.news import NewsArticle
from app.services.ai_pipeline import process_pending_news_articles
from app.agents.tasks import ExtractionResult, ExtractedEntity, ExtractedRelationship

def test_process_pending_news_articles_success(session: Session, monkeypatch):
    # Chuẩn bị bài báo mẫu ở trạng thái pending_entity_extraction trong database
    article = NewsArticle(
        title="FPT ký hợp đồng với VIC",
        content="Nguyễn Văn A ký kết biên bản hợp tác kinh doanh.",
        published_at=dt.datetime.now(),
        url="https://example.com/news1",
        source="CafeF",
        status="pending_entity_extraction"
    )
    session.add(article)
    session.commit()
    session.refresh(article)
    
    # Giả lập run_extraction của CrewAI
    def mock_run_extraction(title, content):
        return ExtractionResult(
            sentiment_score=0.9,
            entities=[
                ExtractedEntity(name="FPT", type="TICKER", description="Tập đoàn FPT"),
                ExtractedEntity(name="Nguyễn Văn A", type="PERSON", description="Lãnh đạo")
            ],
            relationships=[
                ExtractedRelationship(source="Nguyễn Văn A", target="FPT", relation_type="LEADER_OF", description="Đại diện")
            ]
        )
        
    import app.services.ai_pipeline
    monkeypatch.setattr(app.services.ai_pipeline, "run_extraction", mock_run_extraction)
    
    # Gọi hàm xử lý
    summary = process_pending_news_articles(session)
    
    # Xác minh số lượng xử lý thành công
    assert summary["processed"] == 1
    assert summary["success"] == 1
    assert summary["failed"] == 0
    
    # Tải lại bài báo từ DB và kiểm tra các thông tin lưu trữ
    refreshed_article = session.exec(select(NewsArticle).where(NewsArticle.id == article.id)).one()
    assert refreshed_article.status == "extraction_completed"
    assert refreshed_article.sentiment_score == 0.9
    assert len(refreshed_article.raw_entities) == 2
    assert refreshed_article.raw_entities[0]["name"] == "FPT"
    assert refreshed_article.raw_entities[0]["type"] == "TICKER"
    assert len(refreshed_article.raw_relationships) == 1
    assert refreshed_article.raw_relationships[0]["relation_type"] == "LEADER_OF"

def test_process_pending_news_articles_failure(session: Session, monkeypatch):
    # Chuẩn bị bài báo mẫu thứ hai
    article = NewsArticle(
        title="Bài báo gây lỗi LLM",
        content="Nội dung gây lỗi kết nối API.",
        published_at=dt.datetime.now(),
        url="https://example.com/news2",
        source="CafeF",
        status="pending_entity_extraction"
    )
    session.add(article)
    session.commit()
    session.refresh(article)
    
    # Giả lập run_extraction ném ngoại lệ
    def mock_run_extraction(title, content):
        raise Exception("API Rate limit / Timeout")
        
    import app.services.ai_pipeline
    monkeypatch.setattr(app.services.ai_pipeline, "run_extraction", mock_run_extraction)
    
    # Gọi hàm xử lý
    summary = process_pending_news_articles(session)
    
    # Xác minh tiến trình không sập và bài báo được đánh dấu lỗi
    assert summary["processed"] == 1
    assert summary["success"] == 0
    assert summary["failed"] == 1
    
    # Kiểm tra trạng thái bài báo đổi thành extraction_failed
    session.rollback()
    refreshed_article = session.exec(select(NewsArticle).where(NewsArticle.id == article.id)).one()
    assert refreshed_article.status == "extraction_failed"
