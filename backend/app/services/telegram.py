try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False
    import urllib.request
    import json
import time
from typing import Optional, Any
from app.core.config import settings
from app.core.logging import logger

def send_telegram_message(message: str, client: Optional[Any] = None, chat_id: Optional[str] = None, retries: int = 3) -> bool:
    """
    Gửi tin nhắn đến Telegram Chat ID qua Telegram Bot API sử dụng httpx (hoặc urllib làm fallback)
    kèm cơ chế Retry với Exponential Backoff khi gặp lỗi mạng tạm thời hoặc lỗi HTTP 5xx.
    """
    token = settings.TELEGRAM_BOT_TOKEN
    target_chat_id = chat_id or settings.TELEGRAM_CHAT_ID

    if not token or not target_chat_id:
        logger.warning("Telegram Bot Token hoặc Chat ID chưa được cấu hình. Bỏ qua gửi tin nhắn.")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": target_chat_id,
        "text": message,
        "parse_mode": "HTML"
    }

    backoff = 1.0
    for attempt in range(retries):
        if HAS_HTTPX:
            try:
                # Sử dụng client dùng chung nếu được truyền vào để tránh rò rỉ kết nối
                if client:
                    response = client.post(url, json=payload, timeout=10.0)
                else:
                    with httpx.Client(timeout=10.0) as temp_client:
                        response = temp_client.post(url, json=payload)
                
                if response.status_code == 200:
                    logger.info("Đã gửi tin nhắn Telegram thành công.")
                    return True
                elif 400 <= response.status_code < 500:
                    logger.warning(
                        f"Gửi tin nhắn Telegram thất bại với lỗi Client (HTTP {response.status_code}): {response.text}. Không thử lại."
                    )
                    return False
                else:
                    logger.warning(
                        f"Gửi tin nhắn Telegram thất bại (HTTP {response.status_code}): {response.text}. Lần thử {attempt + 1}/{retries}..."
                    )
            except Exception as e:
                logger.warning(f"Lỗi xảy ra khi gọi API Telegram qua httpx (Lần thử {attempt + 1}/{retries}): {str(e)}")
        else:
            # Fallback sang urllib.request
            try:
                import json
                import urllib.request
                import urllib.error
                req_data = json.dumps(payload).encode("utf-8")
                req = urllib.request.Request(
                    url,
                    data=req_data,
                    headers={"Content-Type": "application/json"},
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=10.0) as response:
                    resp_status = response.getcode()
                    if resp_status == 200:
                        logger.info("Đã gửi tin nhắn Telegram thành công qua urllib fallback.")
                        return True
                    else:
                        logger.warning(
                            f"Gửi tin nhắn Telegram thất bại qua urllib (Status: {resp_status}). Lần thử {attempt + 1}/{retries}..."
                        )
            except urllib.error.HTTPError as http_err:
                resp_text = http_err.read().decode("utf-8") if http_err.fp else ""
                if 400 <= http_err.code < 500:
                    logger.warning(
                        f"Gửi tin nhắn Telegram thất bại với lỗi Client qua urllib (HTTP {http_err.code}): {resp_text}. Không thử lại."
                    )
                    return False
                else:
                    logger.warning(
                        f"Gửi tin nhắn Telegram thất bại qua urllib (HTTP {http_err.code}): {resp_text}. Lần thử {attempt + 1}/{retries}..."
                    )
            except Exception as urllib_err:
                logger.warning(f"Lỗi xảy ra khi gọi API Telegram qua urllib fallback (Lần thử {attempt + 1}/{retries}): {str(urllib_err)}")

        if attempt < retries - 1:
            time.sleep(backoff)
            backoff *= 2.0

    return False

def send_triggered_alert_to_telegram(alert: Any, client: Optional[Any] = None) -> bool:
    """
    Định dạng và gửi tin nhắn cảnh báo đã kích hoạt đến Telegram sử dụng HTML parse mode để tránh lỗi Markdown.
    Hỗ trợ nhận cả dict thô lẫn đối tượng TriggeredAlert (ORM).
    """
    if isinstance(alert, dict):
        title = alert.get("title")
        message = alert.get("message")
    else:
        title = getattr(alert, "title", None)
        message = getattr(alert, "message", None)

    if not title or not message:
        logger.warning("Cảnh báo không có tiêu đề hoặc nội dung. Bỏ qua gửi tin nhắn.")
        return False

    import html
    safe_title = html.escape(str(title))
    safe_message = html.escape(str(message))
    formatted_message = f"<b>{safe_title}</b>\n\n{safe_message}"
    return send_telegram_message(formatted_message, client)
