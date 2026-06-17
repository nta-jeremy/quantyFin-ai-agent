import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import httpx
import html
import asyncio
from app.services.telegram_bot import (
    translate_to_cypher,
    validate_cypher_query,
    execute_cypher_query,
    synthesize_response,
    run_telegram_bot_polling
)

@pytest.fixture
def mock_settings():
    with patch("app.services.telegram_bot.settings") as mock:
        mock.TELEGRAM_BOT_TOKEN = "mock_bot_token"
        mock.TELEGRAM_CHAT_ID = "mock_chat_id"
        mock.LITELLM_MODEL = "gemini/gemini-1.5-flash"
        mock.LITELLM_API_KEY = "mock_key"
        mock.LITELLM_API_BASE = "mock_base"
        yield mock

@pytest.fixture
def mock_litellm():
    with patch("app.services.telegram_bot.litellm") as mock:
        # Mock acompletion as an AsyncMock
        mock.acompletion = AsyncMock()
        yield mock

@pytest.fixture
def mock_neo4j():
    with patch("app.services.telegram_bot.neo4j_manager") as mock:
        yield mock


# 1. Test Cypher Translation (LLM call)
@pytest.mark.asyncio
async def test_translate_to_cypher_success(mock_litellm, mock_settings):
    # Mock LiteLLM acompletion response
    mock_completion = MagicMock()
    mock_choice = MagicMock()
    mock_message = MagicMock()
    mock_message.content = "MATCH (s:Stock {ticker: 'VIC'}) RETURN s"
    mock_choice.message = mock_message
    mock_completion.choices = [mock_choice]
    mock_litellm.acompletion.return_value = mock_completion

    query = await translate_to_cypher("Tại sao VIC giảm?")
    assert query == "MATCH (s:Stock {ticker: 'VIC'}) RETURN s"
    mock_litellm.acompletion.assert_called_once()

@pytest.mark.asyncio
async def test_translate_to_cypher_failure(mock_litellm, mock_settings):
    # Mock LiteLLM acompletion raising an exception
    mock_litellm.acompletion.side_effect = Exception("API Error")
    query = await translate_to_cypher("Tại sao VIC giảm?")
    assert query is None


# 2. Test Cypher Injection Validation (Security)
@pytest.mark.parametrize("query, expected", [
    ("MATCH (s:Stock) RETURN s", True),
    ("MATCH (s:Stock {ticker: 'VIC'})<-[:MENTIONS]-(a:Article) RETURN a", True),
    ("MATCH (s:Stock) CREATE (s)-[:REL]->(n) RETURN s", False),
    ("MATCH (s:Stock) SET s.price = 100 RETURN s", False),
    ("MATCH (s:Stock) DELETE s", False),
    ("MATCH (s:Stock) DETACH DELETE s", False),
    ("MERGE (s:Stock {ticker: 'FPT'})", False),
    ("MATCH (s) REMOVE s.prop", False),
    ("match (s) create (s)", False), # Case insensitivity check
    ("MATCH (s) // CREATE a new node\nRETURN s", False), # Bypass with comment
    ("MATCH (s) /* CREATE a new node */ RETURN s", False), # Bypass with multi-line comment
    ("LOAD CSV FROM 'https://leak.com' AS line RETURN line", False), # SSRF/Leak check
    ("CALL apoc.periodic.iterate()", False), # Procedure execution check
])
def test_validate_cypher_query(query, expected):
    assert validate_cypher_query(query) == expected


# 3. Test Neo4j Query Execution
def test_execute_cypher_query_success(mock_neo4j):
    # Mock Neo4j driver and session
    mock_driver = MagicMock()
    mock_session = MagicMock()
    mock_neo4j.get_driver.return_value = mock_driver
    mock_driver.session.return_value.__enter__.return_value = mock_session

    # Mock the read transaction
    mock_result = [{"a.title": "Tin test", "a.sentimentScore": -0.5}]
    mock_session.execute_read.return_value = mock_result

    results = execute_cypher_query("MATCH (s:Stock) RETURN s")
    assert results == mock_result
    mock_session.execute_read.assert_called_once()

def test_execute_cypher_query_error(mock_neo4j):
    mock_driver = MagicMock()
    mock_session = MagicMock()
    mock_neo4j.get_driver.return_value = mock_driver
    mock_driver.session.return_value.__enter__.return_value = mock_session
    mock_session.execute_read.side_effect = Exception("Neo4j syntax error")

    results = execute_cypher_query("MATCH (s:Stock) RETURN s")
    # Trả về None khi có lỗi để phân biệt với trường hợp không tìm thấy dữ liệu ([])
    assert results is None


# 4. Test Response Synthesis (LLM call)
@pytest.mark.asyncio
async def test_synthesize_response_success(mock_litellm, mock_settings):
    mock_completion = MagicMock()
    mock_choice = MagicMock()
    mock_message = MagicMock()
    mock_message.content = "Hôm nay cổ phiếu VIC giảm do tin tức & sự kiện..."
    mock_choice.message = mock_message
    mock_completion.choices = [mock_choice]
    mock_litellm.acompletion.return_value = mock_completion

    data = [{"title": "VIC giảm sâu", "url": "https://example.com"}]
    response = await synthesize_response("Tại sao VIC giảm?", data)
    # Ký tự & trong nội dung text phải được escape thành &amp; để gửi an toàn qua HTML parse mode
    assert "VIC" in response
    assert "&amp;" in response
    mock_litellm.acompletion.assert_called_once()


# 5. Test Telegram Polling and Command Handling
@pytest.mark.asyncio
async def test_run_telegram_bot_polling_start_command(mock_settings):
    # Mock update data for '/start' command
    mock_updates = {
        "ok": True,
        "result": [
            {
                "update_id": 1000,
                "message": {
                    "message_id": 1,
                    "chat": {"id": 9999},
                    "text": "/start"
                }
            }
        ]
    }

    # Mock HTTPX AsyncClient and send_telegram_message
    with patch("httpx.AsyncClient") as mock_async_client_class, \
         patch("app.services.telegram_bot.send_telegram_message") as mock_send:
         
        mock_client = AsyncMock()
        mock_async_client_class.return_value.__aenter__.return_value = mock_client
        mock_send.return_value = True
        
        # Return updates on first call, then raise CancelledError to stop loop
        mock_client.get.side_effect = [
            MagicMock(status_code=200, json=lambda: mock_updates),
            asyncio.CancelledError("Stop Loop")
        ]

        try:
            await run_telegram_bot_polling()
        except asyncio.CancelledError:
            pass

        # Đợi tất cả các task chạy ngầm hoàn thành thay vì dùng sleep cứng (anti-pattern)
        pending = [t for t in asyncio.all_tasks() if t != asyncio.current_task()]
        if pending:
            await asyncio.gather(*pending, return_exceptions=True)

        # Kiểm tra xem hàm send_telegram_message có được gọi đúng tham số không
        mock_send.assert_called_once()
        args, kwargs = mock_send.call_args
        assert kwargs["chat_id"] == "9999"
        assert "Chào mừng" in args[0]

@pytest.mark.asyncio
async def test_run_telegram_bot_polling_help_command(mock_settings):
    # Mock update data for '/help' command
    mock_updates = {
        "ok": True,
        "result": [
            {
                "update_id": 1001,
                "message": {
                    "message_id": 2,
                    "chat": {"id": 8888},
                    "text": "/help"
                }
            }
        ]
    }

    with patch("httpx.AsyncClient") as mock_async_client_class, \
         patch("app.services.telegram_bot.send_telegram_message") as mock_send:
         
        mock_client = AsyncMock()
        mock_async_client_class.return_value.__aenter__.return_value = mock_client
        mock_send.return_value = True
        
        mock_client.get.side_effect = [
            MagicMock(status_code=200, json=lambda: mock_updates),
            asyncio.CancelledError("Stop Loop")
        ]

        try:
            await run_telegram_bot_polling()
        except asyncio.CancelledError:
            pass

        pending = [t for t in asyncio.all_tasks() if t != asyncio.current_task()]
        if pending:
            await asyncio.gather(*pending, return_exceptions=True)

        mock_send.assert_called_once()
        args, kwargs = mock_send.call_args
        assert kwargs["chat_id"] == "8888"
        assert "Hướng dẫn sử dụng" in args[0]

@pytest.mark.asyncio
async def test_run_telegram_bot_polling_query_flow(mock_settings, mock_litellm, mock_neo4j):
    # Mock update data for user query "Tại sao VIC giảm?"
    mock_updates = {
        "ok": True,
        "result": [
            {
                "update_id": 1002,
                "message": {
                    "message_id": 3,
                    "chat": {"id": 12345},
                    "text": "Tại sao VIC giảm?"
                }
            }
        ]
    }

    # Mock LiteLLM acompletion for translation and synthesis
    mock_trans_comp = MagicMock()
    mock_trans_comp.choices = [MagicMock(message=MagicMock(content="MATCH (s) RETURN s"))]
    
    mock_synth_comp = MagicMock()
    mock_synth_comp.choices = [MagicMock(message=MagicMock(content="Đại diện cho kết quả tổng hợp"))]
    
    mock_litellm.acompletion.side_effect = [mock_trans_comp, mock_synth_comp]

    # Mock Neo4j
    mock_driver = MagicMock()
    mock_session = MagicMock()
    mock_neo4j.get_driver.return_value = mock_driver
    mock_driver.session.return_value.__enter__.return_value = mock_session
    mock_session.execute_read.return_value = [{"sentiment": -0.4, "title": "Tin xấu"}]

    with patch("httpx.AsyncClient") as mock_async_client_class, \
         patch("app.services.telegram_bot.send_telegram_message") as mock_send:
         
        mock_client = AsyncMock()
        mock_async_client_class.return_value.__aenter__.return_value = mock_client
        mock_send.return_value = True
        
        mock_client.get.side_effect = [
            MagicMock(status_code=200, json=lambda: mock_updates),
            asyncio.CancelledError("Stop Loop")
        ]

        try:
            await run_telegram_bot_polling()
        except asyncio.CancelledError:
            pass

        pending = [t for t in asyncio.all_tasks() if t != asyncio.current_task()]
        if pending:
            await asyncio.gather(*pending, return_exceptions=True)

        mock_send.assert_called_once()
        args, kwargs = mock_send.call_args
        assert "Đại diện cho kết quả tổng hợp" in args[0]
        assert kwargs["chat_id"] == "12345"

@pytest.mark.asyncio
async def test_run_telegram_bot_polling_query_llm_failure(mock_settings, mock_litellm):
    # Mock update data
    mock_updates = {
        "ok": True,
        "result": [
            {
                "update_id": 1003,
                "message": {
                    "message_id": 4,
                    "chat": {"id": 11111},
                    "text": "Tại sao VIC giảm?"
                }
            }
        ]
    }

    # Mock LiteLLM translation failure (returns None or raises Exception)
    mock_litellm.acompletion.side_effect = Exception("LLM connection timed out")

    with patch("httpx.AsyncClient") as mock_async_client_class, \
         patch("app.services.telegram_bot.send_telegram_message") as mock_send:
         
        mock_client = AsyncMock()
        mock_async_client_class.return_value.__aenter__.return_value = mock_client
        mock_send.return_value = True
        
        mock_client.get.side_effect = [
            MagicMock(status_code=200, json=lambda: mock_updates),
            asyncio.CancelledError("Stop Loop")
        ]

        try:
            await run_telegram_bot_polling()
        except asyncio.CancelledError:
            pass

        pending = [t for t in asyncio.all_tasks() if t != asyncio.current_task()]
        if pending:
            await asyncio.gather(*pending, return_exceptions=True)

        mock_send.assert_called_once()
        args, kwargs = mock_send.call_args
        assert kwargs["chat_id"] == "11111"
        assert "lỗi xảy ra khi phân tích câu hỏi" in args[0]

@pytest.mark.asyncio
async def test_run_telegram_bot_polling_query_db_failure(mock_settings, mock_litellm, mock_neo4j):
    # Mock update data
    mock_updates = {
        "ok": True,
        "result": [
            {
                "update_id": 1004,
                "message": {
                    "message_id": 5,
                    "chat": {"id": 22222},
                    "text": "Tại sao VIC giảm?"
                }
            }
        ]
    }

    # Mock LiteLLM translation success but Neo4j fails
    mock_trans_comp = MagicMock()
    mock_trans_comp.choices = [MagicMock(message=MagicMock(content="MATCH (s) RETURN s"))]
    mock_litellm.acompletion.return_value = mock_trans_comp

    # Mock Neo4j exception
    mock_driver = MagicMock()
    mock_session = MagicMock()
    mock_neo4j.get_driver.return_value = mock_driver
    mock_driver.session.return_value.__enter__.return_value = mock_session
    mock_session.execute_read.side_effect = Exception("Neo4j database down")

    with patch("httpx.AsyncClient") as mock_async_client_class, \
         patch("app.services.telegram_bot.send_telegram_message") as mock_send:
         
        mock_client = AsyncMock()
        mock_async_client_class.return_value.__aenter__.return_value = mock_client
        mock_send.return_value = True
        
        mock_client.get.side_effect = [
            MagicMock(status_code=200, json=lambda: mock_updates),
            asyncio.CancelledError("Stop Loop")
        ]

        try:
            await run_telegram_bot_polling()
        except asyncio.CancelledError:
            pass

        pending = [t for t in asyncio.all_tasks() if t != asyncio.current_task()]
        if pending:
            await asyncio.gather(*pending, return_exceptions=True)

        mock_send.assert_called_once()
        args, kwargs = mock_send.call_args
        assert kwargs["chat_id"] == "22222"
        # Bot phải thông báo lỗi hệ thống lịch sự (AC 8)
        assert "lỗi xảy ra khi truy vấn dữ liệu" in args[0]
