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


def test_skip_article_with_empty_content(session: Session, monkeypatch):
    # Bài có content rỗng → bỏ qua, không gọi run_extraction (R13.5)
    article = NewsArticle(
        title="Bài thiếu nội dung",
        content="",
        published_at=dt.datetime.now(),
        url="https://example.com/empty-content",
        source="CafeF",
        status="pending_entity_extraction"
    )
    session.add(article)
    session.commit()
    session.refresh(article)

    # run_extraction không được phép gọi cho bài thiếu content
    def fail_run_extraction(title, content):
        raise AssertionError("run_extraction không được gọi cho bài content rỗng/null")

    import app.services.ai_pipeline
    monkeypatch.setattr(app.services.ai_pipeline, "run_extraction", fail_run_extraction)

    summary = process_pending_news_articles(session)

    assert summary["processed"] == 1
    assert summary["skipped"] == 1
    assert summary["success"] == 0
    assert summary["failed"] == 0

    refreshed_article = session.exec(select(NewsArticle).where(NewsArticle.id == article.id)).one()
    assert refreshed_article.status == "extraction_skipped_no_content"


def test_full_body_article_runs_extraction(session: Session, monkeypatch):
    # Bài có full body → chạy run_extraction trên content (R13.4)
    full_body = "Toàn văn thân bài đầy đủ phục vụ phân tích AI." * 5
    article = NewsArticle(
        title="Bài có full body",
        content=full_body,
        published_at=dt.datetime.now(),
        url="https://example.com/full-body",
        source="CafeF",
        status="pending_entity_extraction"
    )
    session.add(article)
    session.commit()
    session.refresh(article)

    captured = {}

    def mock_run_extraction(title, content):
        captured["title"] = title
        captured["content"] = content
        return ExtractionResult(
            sentiment_score=0.5,
            entities=[ExtractedEntity(name="ACB", type="TICKER", description="Ngân hàng ACB")],
            relationships=[]
        )

    import app.services.ai_pipeline
    monkeypatch.setattr(app.services.ai_pipeline, "run_extraction", mock_run_extraction)

    summary = process_pending_news_articles(session)

    # run_extraction được gọi đúng với full body của bài
    assert captured["content"] == full_body
    assert captured["title"] == "Bài có full body"

    assert summary["processed"] == 1
    assert summary["success"] == 1
    assert summary["skipped"] == 0
    assert summary["failed"] == 0

    refreshed_article = session.exec(select(NewsArticle).where(NewsArticle.id == article.id)).one()
    assert refreshed_article.status == "extraction_completed"
    assert refreshed_article.sentiment_score == 0.5


def test_skip_empty_content_does_not_block_full_body(session: Session, monkeypatch):
    # Bài thiếu content bị bỏ qua nhưng không làm dừng xử lý bài còn lại (R13.5)
    empty_article = NewsArticle(
        title="Bài thiếu nội dung",
        content="",
        published_at=dt.datetime.now(),
        url="https://example.com/empty-1",
        source="CafeF",
        status="pending_entity_extraction"
    )
    full_article = NewsArticle(
        title="Bài có full body",
        content="Nội dung đầy đủ để phân tích thực thể và cảm xúc.",
        published_at=dt.datetime.now(),
        url="https://example.com/full-1",
        source="CafeF",
        status="pending_entity_extraction"
    )
    session.add(empty_article)
    session.add(full_article)
    session.commit()
    session.refresh(empty_article)
    session.refresh(full_article)

    def mock_run_extraction(title, content):
        return ExtractionResult(sentiment_score=0.1, entities=[], relationships=[])

    import app.services.ai_pipeline
    monkeypatch.setattr(app.services.ai_pipeline, "run_extraction", mock_run_extraction)

    summary = process_pending_news_articles(session)

    assert summary["processed"] == 2
    assert summary["skipped"] == 1
    assert summary["success"] == 1
    assert summary["failed"] == 0

    refreshed_empty = session.exec(select(NewsArticle).where(NewsArticle.id == empty_article.id)).one()
    refreshed_full = session.exec(select(NewsArticle).where(NewsArticle.id == full_article.id)).one()
    assert refreshed_empty.status == "extraction_skipped_no_content"
    assert refreshed_full.status == "extraction_completed"
