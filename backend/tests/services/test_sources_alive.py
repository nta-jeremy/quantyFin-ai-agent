"""Smoke test xác nhận URL nguồn RSS trong registry còn sống (qua pipeline).

Kiểm thử mạng thật (không mock): với mỗi nguồn ``type=rss`` trong
``SOURCE_REGISTRY``, gọi thật URL feed thông qua chính tầng ``discover_rss`` của
hệ thống và khẳng định nguồn còn sống — trả về XML hợp lệ, parse được, và có ít
nhất một bài (``SourceStatus == "ok"``). Đây là sự thật về dịch vụ ngoài
(Req 2.2), không phải logic hệ thống, nên test được đánh dấu
``@pytest.mark.network``.

Khác biệt với ``test_sources_smoke.py`` (kiểm XML thô qua ``ElementTree``): file
này xác nhận URL sống dưới góc nhìn pipeline — feed phải đủ tốt để
``discover_rss`` ánh xạ thành ``ok`` và sinh ra ``ArticleStub``.

Hành vi:
- Mặc định bị LOẠI khỏi suite qua cấu hình ``addopts = "-m 'not network'"`` trong
  ``pyproject.toml`` => chạy offline/CI không làm fail/treo suite.
- Chạy tường minh khi có mạng:
  ``pytest -m network tests/services/test_sources_alive.py``.
"""

import httpx
import pytest

from app.services.extraction.rss import discover_rss
from app.services.sources.registry import SourceConfig, load_sources

# Toàn bộ test trong module này cần mạng thật.
pytestmark = pytest.mark.network

FETCH_TIMEOUT = 30.0

# Các nguồn RSS hợp lệ trong registry (đã qua validate).
_VALID_SOURCES, _ = load_sources()
_RSS_SOURCES = [cfg for cfg in _VALID_SOURCES.values() if cfg.type == "rss"]


@pytest.mark.parametrize(
    "source",
    _RSS_SOURCES,
    ids=[cfg.name for cfg in _RSS_SOURCES],
)
def test_rss_source_is_alive_via_discover(source: SourceConfig) -> None:
    """Mỗi URL RSS phải còn sống và được pipeline parse thành status 'ok'.

    Gọi thật qua ``discover_rss`` (không mock): nếu URL chết, bị chặn, hoặc trả
    nội dung không phải XML hợp lệ thì status sẽ là dead/blocked/parse_error và
    test fail; feed sống đúng định dạng phải cho ``ok`` kèm ít nhất một stub.

    Requirements: 2.2
    """
    with httpx.Client(timeout=FETCH_TIMEOUT, follow_redirects=True) as client:
        stubs, status = discover_rss(source, client)

    assert status == "ok", (
        f"[{source.name}] {source.url} không sống: status '{status}' "
        f"(kỳ vọng 'ok')"
    )
    assert stubs, (
        f"[{source.name}] {source.url} cho status 'ok' nhưng không có bài nào"
    )
