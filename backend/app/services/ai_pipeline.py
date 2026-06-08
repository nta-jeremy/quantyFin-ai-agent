from sqlmodel import Session, select
from app.models.news import NewsArticle
from app.agents.crew import run_extraction
from app.core.logging import logger, trace_id_var
import uuid

def process_pending_news_articles(session: Session) -> dict:
    # Lấy trace_id hiện tại từ context var hoặc tạo mới nếu chạy ngầm hoàn toàn
    trace_id = trace_id_var.get() or f"pipeline-{uuid.uuid4()}"
    logger.info(f"[{trace_id}] Bắt đầu tiến trình AI bóc tách thực thể và phân tích cảm xúc.")
    
    # 1. Lấy danh sách các bài báo có trạng thái 'pending_entity_extraction'
    statement = select(NewsArticle).where(NewsArticle.status == "pending_entity_extraction")
    try:
        bind = session.get_bind()
        if bind.dialect.name != "sqlite":
            statement = statement.with_for_update(skip_locked=True)
    except Exception:
        pass
    statement = statement.limit(100)
    articles = session.exec(statement).all()
    
    processed_count = 0
    success_count = 0
    failed_count = 0
    
    logger.info(f"[{trace_id}] Tìm thấy {len(articles)} bài báo đang chờ xử lý.")
    
    for article in articles:
        processed_count += 1
        logger.info(f"[{trace_id}] Đang xử lý bài báo id={article.id}, tiêu đề='{article.title}'")
        try:
            # 2. Gọi run_extraction của CrewAI
            result = run_extraction(title=article.title, content=article.content)
            
            # 3. Thành công: cập nhật trạng thái và lưu kết quả vào DB
            article.status = "extraction_completed"
            article.sentiment_score = result.sentiment_score
            
            # Chuyển đổi list Pydantic model sang dict để lưu vào cột JSON
            article.raw_entities = [entity.model_dump() for entity in result.entities]
            article.raw_relationships = [relationship.model_dump() for relationship in result.relationships]
            
            session.add(article)
            session.commit()
            success_count += 1
            logger.info(f"[{trace_id}] Đã trích xuất thành công thực thể & cảm xúc cho bài báo id={article.id}")
            
        except Exception as e:
            # Rollback transaction bị lỗi hiện tại
            session.rollback()
            failed_count += 1
            logger.error(f"[{trace_id}] Lỗi khi xử lý bài báo id={article.id}: {str(e)}", exc_info=True)
            
            # 4. Thất bại: Cập nhật trạng thái bài báo thành 'extraction_failed' (dùng session riêng để cô lập lỗi)
            try:
                with Session(session.get_bind()) as err_session:
                    db_article = err_session.get(NewsArticle, article.id)
                    if db_article:
                        db_article.status = "extraction_failed"
                        err_session.add(db_article)
                        err_session.commit()
                logger.info(f"[{trace_id}] Đã đánh dấu bài báo id={article.id} là 'extraction_failed'")
            except Exception as update_err:
                logger.critical(f"[{trace_id}] Không thể cập nhật trạng thái lỗi cho bài báo id={article.id}: {str(update_err)}")
                
    summary = {
        "processed": processed_count,
        "success": success_count,
        "failed": failed_count,
        "trace_id": trace_id
    }
    logger.info(f"[{trace_id}] Tiến trình AI Ingestion hoàn tất. Tóm tắt: {summary}")
    return summary
