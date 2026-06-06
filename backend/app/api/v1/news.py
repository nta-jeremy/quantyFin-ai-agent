from fastapi import APIRouter, Depends, Query, Request, BackgroundTasks, status
from sqlmodel import Session, select
from sqlalchemy import func
from typing import Optional

from app.core.db import get_session
from app.core.logging import trace_id_var, logger
from app.models.news import NewsArticle
from app.services.crawler import ingest_news_articles
from app.core.limiter import limiter

router = APIRouter()

@router.post("/process-ai", status_code=202)
@limiter.limit("5/minute")
def process_news_ai(
    request: Request,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session)
):
    """
    Kích hoạt tiến trình AI bóc tách thực thể và phân tích cảm xúc bất đồng bộ.
    """
    try:
        from app.services.ai_pipeline import process_pending_news_articles
        trace_id = trace_id_var.get()
        
        def run_in_background():
            token = trace_id_var.set(trace_id)
            try:
                from app.core.db import engine
                with Session(engine) as bg_session:
                    process_pending_news_articles(bg_session)
            except Exception as bg_err:
                logger.error(f"Lỗi khi chạy AI pipeline ngầm: {str(bg_err)}")
            finally:
                trace_id_var.reset(token)

        background_tasks.add_task(run_in_background)
        
        return {
            "data": {
                "message": "AI pipeline triggered successfully"
            },
            "error": None,
            "meta": {
                "trace_id": trace_id
            }
        }
    except Exception as e:
        logger.error(f"Lỗi khi kích hoạt AI pipeline: {str(e)}")
        raise e

@router.post("/ingest")
@limiter.limit("5/minute")
def trigger_news_ingestion(request: Request, session: Session = Depends(get_session)):
    """
    Trigger crawling and filtering news articles manually from RSS sources.
    """
    try:
        logger.info("Manual news ingestion triggered via API.")
        stats = ingest_news_articles(session)
        return {
            "data": {
                "totalScraped": stats["total_scraped"],
                "totalFiltered": stats["total_filtered"],
                "totalSaved": stats["total_saved"],
                "errors": stats["errors"]
            },
            "error": None,
            "meta": {
                "trace_id": trace_id_var.get()
            }
        }
    except Exception as e:
        logger.error(f"Error during manual news ingestion: {str(e)}")
        raise e


@router.get("/articles")
def get_articles(
    page: int = Query(1, ge=1, description="Trang số"),
    limit: int = Query(20, ge=1, le=100, description="Số tin trên mỗi trang"),
    source: Optional[str] = Query(None, description="Lọc theo nguồn tin (ví dụ: CafeF, TuoiTre)"),
    status: Optional[str] = Query(None, description="Lọc theo trạng thái (ví dụ: pending_entity_extraction)"),
    session: Session = Depends(get_session)
):
    """
    Lấy danh sách tin tức đã cào và lưu trữ, hỗ trợ phân trang và bộ lọc.
    """
    try:
        offset = (page - 1) * limit

        # Base query and count query
        stmt = select(NewsArticle)
        count_stmt = select(func.count()).select_from(NewsArticle)

        if source:
            stmt = stmt.where(NewsArticle.source == source)
            count_stmt = count_stmt.where(NewsArticle.source == source)

        if status:
            stmt = stmt.where(NewsArticle.status == status)
            count_stmt = count_stmt.where(NewsArticle.status == status)

        # Sort by publication date descending (newest first)
        stmt = stmt.order_by(NewsArticle.published_at.desc()).offset(offset).limit(limit)

        articles = session.exec(stmt).all()
        total = session.exec(count_stmt).one()

        return {
            "data": {
                "items": [
                    {
                        "id": art.id,
                        "title": art.title,
                        "content": art.content,
                        "publishedAt": art.published_at.isoformat(),
                        "url": art.url,
                        "source": art.source,
                        "status": art.status,
                        "createdAt": art.created_at.isoformat(),
                        "updatedAt": art.updated_at.isoformat()
                    }
                    for art in articles
                ],
                "total": total,
                "page": page,
                "limit": limit
            },
            "error": None,
            "meta": {
                "trace_id": trace_id_var.get()
            }
        }
    except Exception as e:
        logger.error(f"Error retrieving news articles: {str(e)}")
        raise e
