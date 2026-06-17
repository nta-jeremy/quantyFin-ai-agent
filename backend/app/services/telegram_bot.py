import asyncio
import html
import uuid
import re
from typing import Any, List, Dict, Optional
import httpx
import litellm
from app.core.config import settings
from app.core.logging import trace_id_var, logger
from app.core.neo4j import neo4j_manager
from app.services.telegram import send_telegram_message

async def send_telegram_message_async(message: str, chat_id: int, client: httpx.AsyncClient = None) -> bool:
    """
    Gửi tin nhắn Telegram bất đồng bộ qua việc gọi hàm dùng chung trong thread pool.
    """
    return await asyncio.to_thread(send_telegram_message, message, chat_id=str(chat_id))

def sanitize_telegram_html(text: str) -> str:
    """
    Lọc và chuyển đổi mã HTML để đảm bảo an toàn cho Telegram API.
    Chỉ giữ lại các thẻ được hỗ trợ và escape phần còn lại.
    """
    if not text:
        return ""
    # Chỉ cho phép: <b>, <i>, <code>, <pre>, <a href="..."> và thẻ đóng tương ứng
    allowed_tags_pattern = re.compile(
        r'(</?(?:b|i|code|pre)>|<a\s+href=["\']https?://[^"\']+["\']\s*>|</a>)',
        re.IGNORECASE
    )
    
    parts = allowed_tags_pattern.split(text)
    sanitized_parts = []
    for idx, part in enumerate(parts):
        if idx % 2 == 0:
            # Phần văn bản nằm ngoài thẻ, cần escape toàn bộ ký tự đặc biệt
            sanitized_parts.append(html.escape(part))
        else:
            # Phần thẻ HTML được cho phép, giữ nguyên cấu trúc
            sanitized_parts.append(part)
    return "".join(sanitized_parts)

async def translate_to_cypher(question: str) -> Optional[str]:
    """
    Dịch câu hỏi tiếng Việt tự nhiên sang câu lệnh Cypher dựa trên schema của dự án.
    """
    schema_context = (
        "Bạn là một chuyên gia cơ sở dữ liệu Neo4j. Nhiệm vụ của bạn là dịch câu hỏi tiếng Việt của người dùng "
        "thành câu truy vấn Neo4j Cypher duy nhất để lấy thông tin cần thiết.\n\n"
        "Schema cơ sở dữ liệu:\n"
        "- Stock: {ticker, name, market, open, high, low, close, volume, priceDate}\n"
        "- Article: {id, title, url, publishedAt, sentimentScore}\n"
        "- Company: {id, name, description}\n"
        "- Person: {id, name, description}\n"
        "- Event: {id, name, description}\n"
        "Mối quan hệ:\n"
        "- (a:Article)-[:MENTIONS {sentimentScore}]->(any_node)\n"
        "- (c:Company)-[:HAS_STOCK]->(s:Stock)\n"
        "- (e1)-[:RELATIONSHIP_TYPE]->(e2) (quan hệ tùy biến giữa các thực thể)\n\n"
        "Nguyên tắc:\n"
        "1. Trả về câu truy vấn Cypher duy nhất. Chỉ trả về code Cypher, KHÔNG giải thích, KHÔNG viết bất kỳ chữ nào ngoài câu truy vấn.\n"
        "2. Đảm bảo câu lệnh Cypher CHỈ ĐỌC (không có CREATE, MERGE, SET, DELETE, REMOVE, DETACH).\n"
        "3. Nếu cần lọc ticker, hãy so sánh ticker dạng chữ in hoa (ví dụ: MATCH (s:Stock {ticker: 'VIC'})).\n"
        "4. Nếu người dùng hỏi 'tại sao giảm' hoặc 'tại sao tăng', hãy truy vấn các Article liên quan ([:MENTIONS]) có sentimentScore âm (giảm) hoặc dương (tăng).\n"
        "5. Nếu không chắc chắn hoặc không thể dịch, trả về chuỗi rỗng.\n\n"
        "Ví dụ:\n"
        "Q: 'Tại sao VIC giảm hôm nay?'\n"
        "Cypher: MATCH (s:Stock {ticker: 'VIC'})<-[m:MENTIONS]-(a:Article) WHERE a.sentimentScore < -0.1 RETURN a.title, a.sentimentScore, a.url ORDER BY a.publishedAt DESC LIMIT 5\n"
        "Q: 'Tin tức mới nhất về FPT'\n"
        "Cypher: MATCH (s:Stock {ticker: 'FPT'})<-[m:MENTIONS]-(a:Article) RETURN a.title, a.sentimentScore, a.url ORDER BY a.publishedAt DESC LIMIT 5"
    )
    
    messages = [
        {"role": "system", "content": schema_context},
        {"role": "user", "content": f"Dịch câu hỏi sau sang Cypher:\nQ: '{question}'"}
    ]
    
    try:
        kwargs = {}
        if settings.LITELLM_API_KEY:
            kwargs["api_key"] = settings.LITELLM_API_KEY
        if settings.LITELLM_API_BASE:
            kwargs["api_base"] = settings.LITELLM_API_BASE
            
        response = await litellm.acompletion(
            model=settings.LITELLM_MODEL,
            messages=messages,
            temperature=0.0,
            **kwargs
        )
        content = response.choices[0].message.content.strip()
        
        # Làm sạch markdown nếu LLM bọc trong ```cypher ... ```
        if "```" in content:
            content = re.sub(r"```(cypher)?", "", content).strip()
            
        return content if content else None
    except Exception as e:
        logger.error(f"Lỗi khi gọi LiteLLM translate_to_cypher: {str(e)}", exc_info=True)
        return None

def validate_cypher_query(query: str) -> bool:
    """
    Kiểm tra bảo mật Cypher (Cypher validation) để chặn câu lệnh thay đổi/ghi dữ liệu.
    """
    if not query:
        return False
    dangerous_keywords = ["CREATE", "SET", "DELETE", "MERGE", "REMOVE", "DETACH", "LOAD", "CALL"]
    pattern = r"\b(" + "|".join(dangerous_keywords) + r")\b"
    
    # Kiểm tra truy vấn gốc để bắt các từ khóa trong comment dòng (ví dụ: // CREATE)
    if re.search(pattern, query, re.IGNORECASE):
        return False
        
    # Kiểm tra truy vấn sau khi xóa comment đa dòng để tránh WAF bypass (ví dụ: C/**/REATE)
    query_clean = re.sub(r"/\*.*?\*/", "", query)
    if re.search(pattern, query_clean, re.IGNORECASE):
        return False
        
    return True

def execute_cypher_query(query: str) -> Optional[List[Dict[str, Any]]]:
    """
    Thực thi câu lệnh Cypher chỉ đọc trên database Neo4j.
    Trả về None nếu xảy ra lỗi ngoại lệ để phân biệt với trường hợp kết quả rỗng.
    """
    driver = neo4j_manager.get_driver()
    try:
        with driver.session() as session:
            def read_tx(tx):
                result = tx.run(query)
                return [dict(record) for record in result]
            return session.execute_read(read_tx)
    except Exception as e:
        logger.error(f"Lỗi khi thực thi câu lệnh Cypher trên Neo4j: {str(e)}", exc_info=True)
        return None

async def synthesize_response(question: str, graph_data: List[Dict[str, Any]]) -> str:
    """
    Tổng hợp dữ liệu kết quả từ Neo4j thành câu trả lời tiếng Việt mạch lạc, an sau HTML.
    """
    # Escape dữ liệu đồ thị trước khi đưa vào prompt của LLM để tránh chèn ký tự HTML lạ
    escaped_graph_data = []
    for item in graph_data:
        escaped_item = {}
        for k, v in item.items():
            if isinstance(v, str):
                escaped_item[k] = html.escape(v)
            else:
                escaped_item[k] = v
        escaped_graph_data.append(escaped_item)

    formatted_data = []
    for i, item in enumerate(escaped_graph_data[:10]):
        item_str = ", ".join(f"{k}: {v}" for k, v in item.items())
        formatted_data.append(f"Dòng {i+1}: {item_str}")
    data_context = "\n".join(formatted_data) if formatted_data else "Không tìm thấy dữ liệu nào trong Neo4j."

    system_prompt = (
        "Bạn là một trợ lý tài chính thông minh của quantyFin AI.\n"
        "Nhiệm vụ của bạn là tổng hợp kết quả truy vấn từ cơ sở dữ liệu đồ thị Neo4j thành một câu trả lời tiếng Việt mạch lạc, chuyên nghiệp.\n\n"
        "Yêu cầu:\n"
        "1. Trả lời trực tiếp câu hỏi của người dùng dựa trên dữ liệu đồ thị được cung cấp.\n"
        "2. Đưa ra các thông tin chi tiết có sẵn trong dữ liệu (ví dụ: tên thực thể, điểm cảm xúc sentimentScore, tiêu đề bài viết và link bài viết).\n"
        "3. Sử dụng các định dạng HTML được Telegram hỗ trợ để làm nổi bật thông tin (như <b>in đậm</b>, <i>in nghiêng</i>, <code>mã code</code>, <a href='url'>link</a>). TUYỆT ĐỐI không sử dụng các tag HTML khác như <ul>, <li>, <div>, <p>, v.v. Chỉ được dùng: <b>, <i>, <code>, <pre>, <a>.\n"
        "4. Hãy đảm bảo nội dung phản hồi dễ hiểu, trực quan, chuyên nghiệp cho nhà đầu tư.\n"
        "5. Nếu không có dữ liệu, hãy trả lời lịch sự rằng hiện tại hệ thống chưa cập nhật tin tức hoặc dữ liệu cho câu hỏi này."
    )
    
    user_content = (
        f"Câu hỏi của người dùng: '{question}'\n\n"
        f"Dữ liệu đồ thị thu được:\n{data_context}"
    )
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content}
    ]
    
    try:
        kwargs = {}
        if settings.LITELLM_API_KEY:
            kwargs["api_key"] = settings.LITELLM_API_KEY
        if settings.LITELLM_API_BASE:
            kwargs["api_base"] = settings.LITELLM_API_BASE
            
        response = await litellm.acompletion(
            model=settings.LITELLM_MODEL,
            messages=messages,
            temperature=0.3,
            **kwargs
        )
        raw_content = response.choices[0].message.content.strip()
        # Đảm bảo đầu ra HTML được làm sạch an toàn
        return sanitize_telegram_html(raw_content)
    except Exception as e:
        logger.error(f"Lỗi khi gọi LiteLLM synthesize_response: {str(e)}", exc_info=True)
        return (
            "Hiện tại hệ thống đang gặp lỗi khi tổng hợp câu trả lời.\n"
            f"Kết quả thô thu được từ cơ sở dữ liệu: {len(graph_data)} dòng dữ liệu."
        )

async def process_update_message(chat_id: int, text: str, client: httpx.AsyncClient):
    """
    Xử lý tin nhắn đến trong bối cảnh trace_id riêng biệt.
    """
    trace_id = f"tg-{uuid.uuid4()}"
    token = trace_id_var.set(trace_id)
    try:
        logger.info(f"Nhận được tin nhắn từ chat_id={chat_id}: '{text}'")
        
        # Xử lý các lệnh hệ thống
        if text.strip().startswith("/"):
            cmd = text.strip().split()[0].lower()
            if cmd == "/start":
                reply = (
                    "<b>Chào mừng bạn đến với quantyFin AI Bot!</b>\n\n"
                    "Tôi là trợ lý ảo hỗ trợ truy vấn thông tin thị trường chứng khoán dựa trên Đồ thị Tri thức.\n"
                    "Bạn có thể đặt các câu hỏi như:\n"
                    "- <i>Tại sao VIC giảm hôm nay?</i>\n"
                    "- <i>VNM có tin tức xấu gì không?</i>\n\n"
                    "Gõ /help để xem thêm chi tiết."
                )
                await send_telegram_message_async(reply, chat_id, client)
                return
            elif cmd == "/help":
                reply = (
                    "<b>Hướng dẫn sử dụng quantyFin AI Bot:</b>\n\n"
                    "Bạn chỉ cần nhập câu hỏi bằng tiếng Việt tự nhiên.\n"
                    "Tôi sẽ tự động phân tích câu hỏi, truy vấn dữ liệu từ Neo4j và tổng hợp câu trả lời.\n\n"
                    "Các câu hỏi mẫu:\n"
                    "- <code>Tại sao FPT tăng giá hôm nay?</code>\n"
                    "- <code>Tin tức mới nhất về VNM</code>"
                )
                await send_telegram_message_async(reply, chat_id, client)
                return
            else:
                reply = "Lệnh không hợp lệ. Vui lòng nhập câu hỏi thông thường hoặc dùng /help."
                await send_telegram_message_async(reply, chat_id, client)
                return
        
        # 1. Dịch câu hỏi sang Cypher
        logger.info(f"Bắt đầu dịch câu hỏi sang Cypher: '{text}'")
        cypher_query = await translate_to_cypher(text)
        if not cypher_query:
            logger.warning(f"Không thể dịch câu hỏi sang Cypher: '{text}'")
            await send_telegram_message_async(
                f"Không tìm thấy thông tin phù hợp hoặc có lỗi xảy ra khi phân tích câu hỏi (Mã lỗi: {trace_id}).",
                chat_id,
                client
            )
            return
            
        logger.info(f"Cypher query đã dịch: '{cypher_query}'")
        
        # 2. Kiểm tra bảo mật
        if not validate_cypher_query(cypher_query):
            logger.warning(f"Từ chối thực thi câu lệnh Cypher nghi ngờ injection: {cypher_query}")
            await send_telegram_message_async(
                "Yêu cầu của bạn chứa các từ khóa thay đổi dữ liệu hoặc hành vi không được phép vì lý do bảo mật. Vui lòng thử lại với câu hỏi khác.",
                chat_id,
                client
            )
            return
            
        # 3. Thực thi Cypher
        logger.info(f"Bắt đầu thực thi Cypher trên Neo4j: {cypher_query}")
        graph_data = await asyncio.to_thread(execute_cypher_query, cypher_query)
        if graph_data is None:
            logger.error(f"Lỗi truy vấn cơ sở dữ liệu Neo4j cho trace_id={trace_id}")
            await send_telegram_message_async(
                f"Không tìm thấy thông tin phù hợp hoặc có lỗi xảy ra khi truy vấn dữ liệu (Mã lỗi: {trace_id}). Vui lòng thử lại sau.",
                chat_id,
                client
            )
            return
            
        logger.info(f"Kết quả truy vấn Neo4j: {len(graph_data)} dòng")
        
        # 4. Tổng hợp phản hồi
        logger.info("Bắt đầu tổng hợp phản hồi từ kết quả đồ thị")
        response_text = await synthesize_response(text, graph_data)
        
        # 5. Gửi phản hồi
        await send_telegram_message_async(response_text, chat_id, client)
        
    except Exception as e:
        logger.error(f"Lỗi khi xử lý tin nhắn từ chat_id={chat_id}: {str(e)}", exc_info=True)
        try:
            await send_telegram_message_async(
                f"Đã xảy ra lỗi khi xử lý yêu cầu của bạn (Mã lỗi: {trace_id}). Vui lòng thử lại sau.",
                chat_id,
                client
            )
        except Exception:
            pass
    finally:
        trace_id_var.reset(token)

async def run_telegram_bot_polling(app_state: Any = None):
    """
    Vòng lặp không đồng bộ Long Polling lấy tin nhắn mới từ Telegram và xử lý.
    """
    logger.info("Khởi động Telegram Bot Polling task...")
    token = settings.TELEGRAM_BOT_TOKEN
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN không được cấu hình. Bỏ qua chạy Telegram Bot Polling.")
        return

    offset = None
    url = f"https://api.telegram.org/bot{token}/getUpdates"
    
    # Giới hạn 10 luồng xử lý tin nhắn đồng thời tránh bị spam nghẽn hệ thống
    semaphore = asyncio.Semaphore(10)
    active_tasks = set()

    async def process_with_sem(c_id: int, msg_txt: str, http_clt: httpx.AsyncClient):
        async with semaphore:
            await process_update_message(c_id, msg_txt, http_clt)
    
    async with httpx.AsyncClient(timeout=40.0) as client:
        while True:
            try:
                params = {"timeout": 30}
                if offset is not None:
                    params["offset"] = offset
                    
                response = await client.get(url, params=params)
                if response.status_code != 200:
                    logger.warning(
                        f"Lấy cập nhật từ Telegram thất bại. HTTP Status: {response.status_code}, "
                        f"Response: {response.text}"
                    )
                    await asyncio.sleep(5)
                    continue
                    
                data = response.json()
                if not data.get("ok"):
                    logger.warning(f"Telegram API trả về ok=False: {data}")
                    await asyncio.sleep(5)
                    continue
                    
                updates = data.get("result", [])
                for update in updates:
                    update_id = update.get("update_id")
                    if update_id is not None:
                        offset = update_id + 1
                    
                    message = update.get("message")
                    if not message:
                        continue
                        
                    chat = message.get("chat")
                    if not chat:
                        continue
                        
                    chat_id = chat.get("id")
                    text = message.get("text")
                    if not text or chat_id is None:
                        continue
                        
                    # Chạy không đồng bộ dưới sự kiểm soát của semaphore
                    task = asyncio.create_task(process_with_sem(chat_id, text, client))
                    active_tasks.add(task)
                    task.add_done_callback(active_tasks.discard)
                    
            except asyncio.CancelledError:
                logger.info("Tác vụ Telegram Bot Polling nhận tín hiệu hủy, đang đợi các task con hoàn thành...")
                if active_tasks:
                    try:
                        await asyncio.wait_for(asyncio.gather(*active_tasks, return_exceptions=True), timeout=10.0)
                    except asyncio.TimeoutError:
                        logger.warning("Một số tác vụ xử lý tin nhắn không hoàn thành kịp thời và bị buộc hủy.")
                logger.info("Đã dừng toàn bộ tác vụ xử lý tin nhắn Telegram.")
                raise
            except Exception as e:
                logger.error(f"Lỗi không mong muốn trong vòng lặp Polling: {str(e)}", exc_info=True)
                await asyncio.sleep(5)
