"""Test cho Content Extractor (tầng 2): app.services.extraction.content.

Gồm:
- Property 11: needs_fallback theo ngưỡng độ dài (Hypothesis).
- Unit test extract_full_content với HTTP mock (httpx.MockTransport).

Mock HTTP bằng httpx.MockTransport: dựng một httpx.Client với transport giả,
truyền trực tiếp vào extract_full_content theo đúng chữ ký
extract_full_content(url, client).
"""

from unittest import mock

import httpx
from hypothesis import given, settings as hyp_settings, strategies as st

from app.core.config import settings
from app.services.extraction import content as content_module
from app.services.extraction.content import ExtractionResult, extract_full_content

URL = "https://example.com/bai-viet"


def _client(handler) -> httpx.Client:
    """Tạo httpx.Client dùng MockTransport với handler tùy biến."""
    return httpx.Client(transport=httpx.MockTransport(handler))


# ---------------------------------------------------------------------------
# Property 11: needs_fallback theo ngưỡng độ dài
# ---------------------------------------------------------------------------

# Feature: news-crawler-fulltext, Property 11: needs_fallback theo ngưỡng độ dài.
# Với mọi chuỗi full body, extract_full_content() đặt needs_fallback = True khi
# và chỉ khi độ dài body nhỏ hơn MIN_CONTENT_LENGTH. Body do trafilatura.extract
# trả về được kiểm soát qua patch để cô lập đúng logic so sánh ngưỡng.
# Validates: Requirements 5.6
@hyp_settings(max_examples=100)
@given(body=st.text(min_size=0, max_size=settings.MIN_CONTENT_LENGTH + 100))
def test_property_11_needs_fallback_threshold(body):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="<html><body>ignored</body></html>")

    # trafilatura.extract trả về body đã sinh => cô lập logic ngưỡng.
    with mock.patch.object(content_module.trafilatura, "extract", return_value=body):
        with _client(handler) as client:
            result = extract_full_content(URL, client)

    assert result.ok is True
    assert result.body == body
    # Bất biến cốt lõi: needs_fallback đúng bằng (len(body) < ngưỡng).
    assert result.needs_fallback == (len(body) < settings.MIN_CONTENT_LENGTH)


# ---------------------------------------------------------------------------
# Unit test extract_full_content với HTTP mock
# ---------------------------------------------------------------------------

# Validates: Requirements 5.1, 5.2 — body hợp lệ được trích xuất qua HTTP tĩnh.
def test_extract_full_content_valid_body():
    # HTML bài viết đủ dài để trafilatura trích xuất ra full body thực sự.
    paragraph = (
        "Thị trường chứng khoán Việt Nam ghi nhận phiên giao dịch sôi động khi "
        "dòng tiền nội tiếp tục đổ vào nhóm cổ phiếu vốn hóa lớn. Nhiều nhà đầu tư "
        "kỳ vọng lợi nhuận quý này sẽ tăng trưởng mạnh nhờ kết quả kinh doanh khả "
        "quan của các doanh nghiệp đầu ngành. Chỉ số chính bứt phá qua vùng kháng "
        "cự quan trọng trong bối cảnh thanh khoản cải thiện rõ rệt so với tuần trước."
    )
    html = (
        "<html><head><title>Bài viết</title></head><body><article>"
        + "".join(f"<p>{paragraph}</p>" for _ in range(4))
        + "</article></body></html>"
    )

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=html)

    with _client(handler) as client:
        result = extract_full_content(URL, client)

    assert result.ok is True
    assert result.http_status == 200
    assert result.error is None
    assert result.body != ""
    assert "chứng khoán" in result.body
    # Body dài hơn ngưỡng => không cần fallback.
    assert result.needs_fallback is False


# Validates: Requirements 5.4 — HTTP >= 400 ghi nhận mã lỗi, không ghi đè dữ liệu.
def test_extract_full_content_http_error_does_not_overwrite():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, text="Not Found")

    with _client(handler) as client:
        result = extract_full_content(URL, client)

    assert result.ok is False
    assert result.error == "http_404"
    assert result.http_status == 404
    # Không trích xuất nội dung => không có body để ghi đè dữ liệu hiện có.
    assert result.body == ""
    assert result.needs_fallback is False


# Validates: Requirements 5.5 — timeout ghi nhận không trích xuất được kèm lý do.
def test_extract_full_content_timeout():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("request timed out", request=request)

    with _client(handler) as client:
        result = extract_full_content(URL, client)

    assert result.ok is False
    assert result.error == "timeout"
    assert result.http_status is None
    assert result.body == ""


# Validates: Requirements 5.5 — lỗi kết nối mạng ghi nhận không trích xuất được.
def test_extract_full_content_network_error():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection failed", request=request)

    with _client(handler) as client:
        result = extract_full_content(URL, client)

    assert result.ok is False
    assert result.error == "network"
    assert result.http_status is None
    assert result.body == ""


# Bổ sung: HTTP >= 400 trả về cũng cần đúng kiểu ExtractionResult (an toàn kiểu).
def test_extract_full_content_returns_extraction_result_type():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="<html><body><p>x</p></body></html>")

    with _client(handler) as client:
        result = extract_full_content(URL, client)

    assert isinstance(result, ExtractionResult)
