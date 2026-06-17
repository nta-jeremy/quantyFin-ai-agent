import datetime as dt
from typing import Tuple, List, Dict, Any, Optional
from sqlmodel import Session, select
from sqlalchemy import desc
from sqlalchemy.orm import selectinload
from app.core.logging import logger
from app.core.neo4j import neo4j_manager
from app.models.stock import StockTicker, StockPrice
from app.models.alert import AlertRule, TriggeredAlert

def format_price(val: Optional[float]) -> str:
    if val is None:
        return "N/A"
    return f"{val:,.2f}" if val < 100 else f"{val:,.0f}"

def evaluate_price_risk(session: Session, ticker_id: int, threshold: float) -> Tuple[bool, float, str]:
    """
    Kiểm tra biến động giá close-to-close của ticker.
    So sánh ngày gần nhất với ngày giao dịch trước đó.
    Trả về: (is_triggered, change_pct, description)
    """
    # Lấy 2 phiên giao dịch gần nhất
    statement = (
        select(StockPrice)
        .where(StockPrice.ticker_id == ticker_id)
        .order_by(desc(StockPrice.date))
        .limit(2)
    )
    prices = session.exec(statement).all()
    
    if len(prices) < 2:
        return False, 0.0, "Không đủ dữ liệu giá (yêu cầu ít nhất 2 phiên giao dịch) để đánh giá."

    latest = prices[0]
    prev = prices[1]
    
    if latest.close is None or prev.close is None:
        return False, 0.0, "Dữ liệu giá đóng cửa bị rỗng (None), không thể đánh giá."
        
    if prev.close <= 0:
        return False, 0.0, f"Giá đóng cửa của phiên trước không hợp lệ ({prev.close}), không thể tính toán."
        
    change_pct = (latest.close - prev.close) / prev.close
    
    # price_threshold phải là số âm để kích hoạt cho đà giảm giá.
    # Nếu người dùng nhập nhầm số dương (ví dụ 0.03), chúng ta tự động đổi dấu thành -0.03.
    effective_threshold = -abs(threshold)
    is_triggered = change_pct <= effective_threshold
    
    desc_str = (
        f"Giá đóng cửa ngày {latest.date.strftime('%Y-%m-%d')} là {format_price(latest.close)} "
        f"thay đổi {change_pct * 100:+.2f}% so với ngày {prev.date.strftime('%Y-%m-%d')} ({format_price(prev.close)})."
    )
    
    return is_triggered, change_pct, desc_str


def evaluate_sentiment_risk(ticker: str, threshold: float) -> Tuple[bool, Optional[float], List[Dict[str, Any]]]:
    """
    Truy vấn Neo4j lấy các bài báo trực tiếp liên quan đến Stock node
    có sentimentScore nhỏ hơn hoặc bằng ngưỡng threshold.
    Trả về: (is_triggered, min_sentiment, list_of_articles)
    """
    driver = neo4j_manager.get_driver()
    articles = []
    
    query = """
    MATCH (s:Stock {ticker: $ticker})<-[:MENTIONS]-(a:Article)
    WHERE a.sentimentScore <= $threshold
    RETURN a.title AS title, a.sentimentScore AS sentimentScore, a.url AS url
    """
    
    try:
        with driver.session() as session:
            result = session.run(query, {"ticker": ticker, "threshold": threshold})
            for record in result:
                articles.append({
                    "title": record["title"],
                    "sentimentScore": record["sentimentScore"],
                    "url": record["url"]
                })
    except Exception as e:
        logger.error(f"Lỗi hệ thống khi truy vấn sentiment từ Neo4j cho {ticker}: {str(e)}")
        return False, None, []

    if not articles:
        return False, None, []
        
    valid_scores = [a["sentimentScore"] for a in articles if a["sentimentScore"] is not None]
    if not valid_scores:
        return False, None, []
        
    min_sentiment = min(valid_scores)
    return True, min_sentiment, articles


def has_negative_news(ticker: str, threshold: float = -0.1) -> Tuple[bool, List[Dict[str, Any]]]:
    """
    Kiểm tra xem có tin tức tiêu cực nào liên quan trực tiếp đến Stock trong Neo4j hay không.
    Trả về: (has_negative_news, list_of_articles)
    """
    driver = neo4j_manager.get_driver()
    articles = []
    
    query = """
    MATCH (s:Stock {ticker: $ticker})<-[:MENTIONS]-(a:Article)
    WHERE a.sentimentScore <= $threshold
    RETURN a.title AS title, a.sentimentScore AS sentimentScore, a.url AS url
    LIMIT 3
    """
    
    try:
        with driver.session() as session:
            result = session.run(query, {"ticker": ticker, "threshold": threshold})
            for record in result:
                articles.append({
                    "title": record["title"],
                    "sentimentScore": record["sentimentScore"],
                    "url": record["url"]
                })
    except Exception as e:
        logger.error(f"Lỗi hệ thống khi kiểm tra tin tức tiêu cực cho {ticker}: {str(e)}")
        return False, []
        
    return len(articles) > 0, articles


def evaluate_indirect_sentiment_risk(ticker: str, threshold: float = -0.3) -> List[Dict[str, Any]]:
    """
    Truy vấn Neo4j để tìm các liên kết gián tiếp (2-hop) từ Stock node đến các bài báo tiêu cực.
    Được sử dụng cho cảnh báo cấp độ Info.
    """
    driver = neo4j_manager.get_driver()
    articles = []
    
    # Tìm Article đề cập đến một Entity/Company (không lọc nhãn Entity cứng), và thực thể đó liên kết với Stock.
    # Loại trừ các bài viết đề cập trực tiếp đến Stock.
    # Định hướng quan hệ rõ ràng để tránh bùng nổ đường đi
    query = """
    MATCH (s:Stock {ticker: $ticker})
    MATCH (s)<-[:HAS_STOCK|RELATED_TO|MENTIONS*1..2]-(e)
    MATCH (e)<-[:MENTIONS]-(a:Article)
    WHERE a.sentimentScore <= $threshold
      AND NOT (s)<-[:MENTIONS]-(a)
    RETURN DISTINCT a.title AS title, a.sentimentScore AS sentimentScore, a.url AS url, e.name AS relatedEntity
    LIMIT 5
    """
    
    try:
        with driver.session() as session:
            result = session.run(query, {"ticker": ticker, "threshold": threshold})
            for record in result:
                articles.append({
                    "title": record["title"],
                    "sentimentScore": record["sentimentScore"],
                    "url": record["url"],
                    "relatedEntity": record["relatedEntity"] or "Thực thể liên quan"
                })
    except Exception as e:
        logger.error(f"Lỗi hệ thống khi truy vấn indirect sentiment từ Neo4j cho {ticker}: {str(e)}")
        
    return articles


def check_and_trigger_alerts(session: Session) -> List[TriggeredAlert]:
    """
    Quét qua toàn bộ cấu hình AlertRule đang hoạt động để đánh giá rủi ro và tạo cảnh báo.
    """
    logger.info("Bắt đầu quét và phân tích rủi ro hệ thống...")
    
    # Eagerly load ticker relation to resolve N+1 Query
    statement = select(AlertRule).where(AlertRule.is_active == True).options(selectinload(AlertRule.ticker))
    rules = session.exec(statement).all()
    
    triggered_alerts = []
    now_utc = dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)
    
    for rule in rules:
        # Sử dụng Postgres Savepoint (begin_nested) cho từng rule để cô lập lỗi
        try:
            with session.begin_nested():
                ticker = rule.ticker
                if not ticker or not ticker.is_active:
                    continue
                
                ticker_symbol = ticker.ticker
                
                # 1. Đánh giá rủi ro giá
                price_triggered, price_change, price_desc = evaluate_price_risk(
                    session, rule.ticker_id, rule.price_threshold
                )
                
                # AC 2: Kết hợp biến động giá > 3% với việc xuất hiện thực thể tiêu cực trong đồ thị tri thức
                price_has_neg_news = False
                price_neg_articles = []
                if price_triggered:
                    price_has_neg_news, price_neg_articles = has_negative_news(ticker_symbol, -0.1)
                    if not price_has_neg_news:
                        # Hủy kích hoạt rủi ro giá vì không đi kèm thực thể/tin tức tiêu cực nào trong đồ thị
                        price_triggered = False
                
                # 2. Đánh giá rủi ro sentiment trực tiếp
                sentiment_triggered, min_sentiment, direct_articles = evaluate_sentiment_risk(
                    ticker_symbol, rule.sentiment_threshold
                )
                
                # 3. Phân loại mức độ cảnh báo (critical, warning, info)
                level = None
                title = ""
                message_parts = []
                
                if price_triggered and sentiment_triggered:
                    level = "critical"
                    min_sent_val = min_sentiment if min_sentiment is not None else rule.sentiment_threshold
                    title = f"🔴 CẢNH BÁO NGUY CẤP: Phát hiện rủi ro kép đối với mã {ticker_symbol}"
                    message_parts.append("Hệ thống phát hiện biến động tiêu cực đồng thời từ cả giá và tin tức:")
                    message_parts.append(f"- Biến động giá: {price_desc}")
                    message_parts.append(f"- Tin tức tiêu cực trực tiếp (Sentiment thấp nhất: {min_sent_val:.2f}):")
                    for art in direct_articles[:3]:
                        score = art.get('sentimentScore')
                        score_str = f"{score:.2f}" if score is not None else "N/A"
                        message_parts.append(f"  * {art['title']} (Sentiment: {score_str}) - {art['url']}")
                        
                elif price_triggered or sentiment_triggered:
                    level = "warning"
                    title = f"🟡 CẢNH BÁO: Phát hiện rủi ro đối với mã {ticker_symbol}"
                    if price_triggered:
                        message_parts.append(f"- Biến động giá vượt ngưỡng: {price_desc}")
                        if price_neg_articles:
                            message_parts.append("- Thực thể/tin tức tiêu cực kết hợp ghi nhận trên đồ thị:")
                            for art in price_neg_articles[:3]:
                                score = art.get('sentimentScore')
                                score_str = f"{score:.2f}" if score is not None else "N/A"
                                message_parts.append(f"  * {art['title']} (Sentiment: {score_str}) - {art['url']}")
                    if sentiment_triggered:
                        min_sent_val = min_sentiment if min_sentiment is not None else rule.sentiment_threshold
                        message_parts.append(f"- Tin tức tiêu cực trực tiếp vượt ngưỡng (Sentiment thấp nhất: {min_sent_val:.2f}):")
                        for art in direct_articles[:3]:
                            score = art.get('sentimentScore')
                            score_str = f"{score:.2f}" if score is not None else "N/A"
                            message_parts.append(f"  * {art['title']} (Sentiment: {score_str}) - {art['url']}")
                
                else:
                    # 4. Kiểm tra Info level: sentiment tiêu cực nhẹ [-0.5, -0.3] hoặc liên kết gián tiếp
                    # Check direct mild sentiment
                    info_threshold = max(-0.3, rule.sentiment_threshold)
                    mild_sentiment_triggered, mild_min_sentiment, mild_articles = evaluate_sentiment_risk(
                        ticker_symbol, info_threshold
                    )
                    if mild_articles:
                        # Filter out those <= sentiment_threshold (already checked in sentiment_triggered)
                        mild_articles = [a for a in mild_articles if a["sentimentScore"] is not None and a["sentimentScore"] > rule.sentiment_threshold]
                    
                    # Check indirect sentiment
                    indirect_articles = evaluate_indirect_sentiment_risk(ticker_symbol, -0.3)
                    
                    if mild_articles or indirect_articles:
                        level = "info"
                        title = f"🔵 THÔNG TIN: Ghi nhận tín hiệu rủi ro nhẹ đối với mã {ticker_symbol}"
                        if mild_articles:
                            mild_sent_val = mild_min_sentiment if mild_min_sentiment is not None else -0.3
                            message_parts.append(f"- Tin tức tiêu cực nhẹ trực tiếp (Sentiment: {mild_sent_val:.2f}):")
                            for art in mild_articles[:3]:
                                score = art.get('sentimentScore')
                                score_str = f"{score:.2f}" if score is not None else "N/A"
                                message_parts.append(f"  * {art['title']} (Sentiment: {score_str}) - {art['url']}")
                        if indirect_articles:
                            message_parts.append("- Phát hiện mối liên kết gián tiếp đến thực thể rủi ro trong đồ thị:")
                            for art in indirect_articles[:3]:
                                score = art.get('sentimentScore')
                                score_str = f"{score:.2f}" if score is not None else "N/A"
                                message_parts.append(f"  * Đề cập [{art['relatedEntity']}]: {art['title']} (Sentiment: {score_str}) - {art['url']}")
                
                # Nếu có cảnh báo được kích hoạt
                if level:
                    # Kiểm tra trùng lặp trong vòng 24 giờ qua (anti-spam thông minh)
                    time_limit = now_utc - dt.timedelta(hours=24)
                    dup_stmt = (
                        select(TriggeredAlert)
                        .where(TriggeredAlert.ticker == ticker_symbol)
                        .where(TriggeredAlert.level == level)
                        .where(TriggeredAlert.triggered_at >= time_limit)
                    )
                    duplicates = session.exec(dup_stmt).all()
                    
                    is_duplicate = False
                    for dup in duplicates:
                        if level == "critical":
                            is_duplicate = True
                            break
                        elif level == "warning":
                            # Chỉ chặn trùng nếu cùng nguyên nhân kích hoạt
                            if price_triggered and "- Biến động giá" in dup.message:
                                is_duplicate = True
                                break
                            if sentiment_triggered and "- Tin tức tiêu cực trực tiếp" in dup.message:
                                is_duplicate = True
                                break
                        elif level == "info":
                            if mild_articles and "- Tin tức tiêu cực nhẹ trực tiếp" in dup.message:
                                is_duplicate = True
                                break
                            if indirect_articles and "- Phát hiện mối liên kết gián tiếp" in dup.message:
                                is_duplicate = True
                                break
                    
                    if not is_duplicate:
                        new_alert = TriggeredAlert(
                            rule_id=rule.id,
                            ticker=ticker_symbol,
                            level=level,
                            title=title,
                            message="\n".join(message_parts),
                            is_dismissed=False,
                            triggered_at=now_utc
                        )
                        session.add(new_alert)
                        session.flush()  # flush to populate ID inside savepoint
                        triggered_alerts.append(new_alert)
                        logger.info(f"Đã kích hoạt cảnh báo {level} cho {ticker_symbol}")
                    else:
                        logger.info(f"Bỏ qua cảnh báo {level} trùng lặp cho {ticker_symbol} (đã kích hoạt trong 24 giờ qua)")
        
        except Exception as rule_err:
            logger.error(f"Lỗi khi đánh giá rủi ro cho AlertRule ID {rule.id}: {str(rule_err)}")
            # nested transaction (savepoint) will auto rollback on exiting 'with session.begin_nested()'
            
    try:
        session.commit()
    except Exception as commit_err:
        logger.error(f"Lỗi khi commit các cảnh báo mới kích hoạt: {str(commit_err)}")
        session.rollback()
        return []
        
    # Gửi cảnh báo qua Telegram chạy ngầm để tránh chặn tiến trình chính
    import threading
    from app.services.telegram import send_triggered_alert_to_telegram, HAS_HTTPX
    from app.core.logging import trace_id_var

    # Lấy trace_id hiện tại từ thread chính để đồng bộ log
    current_trace_id = trace_id_var.get()

    def send_alerts_bg(alerts_list: List[dict], trace_id: str):
        # Thiết lập trace_id cho thread chạy ngầm
        token = trace_id_var.set(trace_id)
        try:
            if HAS_HTTPX:
                import httpx
                # Tái sử dụng HTTP connection pool để tránh rò rỉ kết nối
                with httpx.Client(timeout=10.0) as client:
                    for alert in alerts_list:
                        try:
                            send_triggered_alert_to_telegram(alert, client)
                        except Exception as e:
                            logger.error(f"Lỗi không mong muốn khi gửi Telegram trong thread ngầm: {str(e)}")
            else:
                for alert in alerts_list:
                    try:
                        send_triggered_alert_to_telegram(alert)
                    except Exception as e:
                        logger.error(f"Lỗi không mong muốn khi gửi Telegram trong thread ngầm: {str(e)}")
        finally:
            trace_id_var.reset(token)

    if triggered_alerts:
        # Chuyển đổi sang dict thô (DTO) để tránh lỗi DetachedInstanceError khi session bị đóng
        alerts_data = [{"title": a.title, "message": a.message} for a in triggered_alerts]
        thread = threading.Thread(target=send_alerts_bg, args=(alerts_data, current_trace_id))
        thread.daemon = True
        thread.start()
        
    return triggered_alerts
