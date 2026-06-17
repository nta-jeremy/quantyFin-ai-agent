import pytest
from unittest.mock import patch, MagicMock
import httpx
from app.core.config import settings
from app.models.alert import TriggeredAlert
from app.services.telegram import (
    send_telegram_message,
    send_triggered_alert_to_telegram
)

def test_send_telegram_message_success():
    """Test gửi tin nhắn Telegram thành công qua httpx"""
    with patch("app.services.telegram.settings") as mock_settings:
        mock_settings.TELEGRAM_BOT_TOKEN = "test_token"
        mock_settings.TELEGRAM_CHAT_ID = "test_chat_id"
        
        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value.__enter__.return_value = mock_client
            
            mock_response = MagicMock(spec=httpx.Response)
            mock_response.status_code = 200
            mock_response.text = "OK"
            mock_client.post.return_value = mock_response
            
            result = send_telegram_message("Hello World")
            
            assert result is True
            mock_client.post.assert_called_once_with(
                "https://api.telegram.org/bottest_token/sendMessage",
                json={"chat_id": "test_chat_id", "text": "Hello World", "parse_mode": "HTML"}
            )

def test_send_telegram_message_http_error():
    """Test gửi tin nhắn Telegram bị lỗi HTTP (ví dụ: status 400)"""
    with patch("app.services.telegram.settings") as mock_settings:
        mock_settings.TELEGRAM_BOT_TOKEN = "test_token"
        mock_settings.TELEGRAM_CHAT_ID = "test_chat_id"
        
        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value.__enter__.return_value = mock_client
            
            mock_response = MagicMock(spec=httpx.Response)
            mock_response.status_code = 400
            mock_response.text = "Bad Request"
            mock_client.post.return_value = mock_response
            
            result = send_telegram_message("Hello World")
            
            assert result is False
            mock_client.post.assert_called_once()

def test_send_telegram_message_exception():
    """Test gửi tin nhắn Telegram gặp lỗi mạng/Exception"""
    with patch("app.services.telegram.settings") as mock_settings:
        mock_settings.TELEGRAM_BOT_TOKEN = "test_token"
        mock_settings.TELEGRAM_CHAT_ID = "test_chat_id"
        
        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value.__enter__.return_value = mock_client
            mock_client.post.side_effect = httpx.RequestError("Network Connection Failed")
            
            result = send_telegram_message("Hello World", retries=1)
            
            assert result is False
            mock_client.post.assert_called_once()

def test_send_telegram_message_missing_config():
    """Test gửi tin nhắn khi chưa cấu hình token hoặc chat ID"""
    with patch("app.services.telegram.settings") as mock_settings:
        mock_settings.TELEGRAM_BOT_TOKEN = None
        mock_settings.TELEGRAM_CHAT_ID = None
        
        with patch("httpx.Client") as mock_client_class:
            result = send_telegram_message("Hello World")
            
            assert result is False
            mock_client_class.assert_not_called()

def test_send_triggered_alert_to_telegram():
    """Test định dạng và gửi tin nhắn cảnh báo thành công (kiểu HTML safe)"""
    alert = TriggeredAlert(
        id=123,
        ticker="VIC",
        level="critical",
        title="🔴 CẢNH BÁO NGUY CẤP: VIC & Vingroup",
        message="Giá giảm 5% và tin tức tiêu cực <đặc biệt>"
    )
    
    with patch("app.services.telegram.send_telegram_message") as mock_send_message:
        mock_send_message.return_value = True
        
        result = send_triggered_alert_to_telegram(alert)
        
        assert result is True
        # HTML special chars like & and <> should be escaped
        mock_send_message.assert_called_once_with(
            "<b>🔴 CẢNH BÁO NGUY CẤP: VIC &amp; Vingroup</b>\n\nGiá giảm 5% và tin tức tiêu cực &lt;đặc biệt&gt;",
            None
        )

def test_send_triggered_alert_to_telegram_dict():
    """Test định dạng và gửi tin nhắn cảnh báo thành công từ Dict thô"""
    alert = {
        "title": "🟡 CẢNH BÁO: FPT",
        "message": "Tin tức tiêu cực"
    }
    
    with patch("app.services.telegram.send_telegram_message") as mock_send_message:
        mock_send_message.return_value = True
        
        result = send_triggered_alert_to_telegram(alert)
        
        assert result is True
        mock_send_message.assert_called_once_with(
            "<b>🟡 CẢNH BÁO: FPT</b>\n\nTin tức tiêu cực",
            None
        )

def test_send_triggered_alert_to_telegram_empty():
    """Test gửi tin nhắn cảnh báo rỗng"""
    alert = TriggeredAlert(
        id=123,
        ticker="VIC",
        level="critical",
        title="",
        message=""
    )
    
    with patch("app.services.telegram.send_telegram_message") as mock_send_message:
        result = send_triggered_alert_to_telegram(alert)
        
        assert result is False
        mock_send_message.assert_not_called()

def test_send_telegram_message_urllib_fallback():
    """Test gửi tin nhắn Telegram thông qua urllib.request fallback"""
    with patch("app.services.telegram.HAS_HTTPX", False):
        with patch("app.services.telegram.settings") as mock_settings:
            mock_settings.TELEGRAM_BOT_TOKEN = "fallback_token"
            mock_settings.TELEGRAM_CHAT_ID = "fallback_chat_id"
            
            with patch("urllib.request.urlopen") as mock_urlopen:
                mock_response = MagicMock()
                mock_response.getcode.return_value = 200
                mock_response.read.return_value = b"OK"
                mock_urlopen.return_value.__enter__.return_value = mock_response
                
                result = send_telegram_message("Hello Fallback")
                
                assert result is True
                mock_urlopen.assert_called_once()
