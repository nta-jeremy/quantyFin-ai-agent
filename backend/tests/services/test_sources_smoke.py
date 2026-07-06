"""Smoke test xác nhận URL nguồn RSS trong registry còn sống.

Đây là kiểm thử mạng thật (không mock): với mỗi nguồn ``type=rss`` trong
``SOURCE_REGISTRY``, gọi thật URL feed và khẳng định nguồn trả về nội dung XML
hợp lệ có ít nhất một mục bài viết. Đây là sự thật về dịch vụ ngoài (Req 2.2),
không phải logic hệ thống, nên test được đánh dấu ``@pytest.mark.network``.

Hành vi:
- Mặc định bị LOẠI khỏi suite qua cấu hình ``addopts = "-m 'not network'"`` trong
  ``pyproject.toml`` => chạy offline/CI không làm fail suite.
- Chạy tường minh khi có mạng: ``pytest -m network tests/services/test_sources_smoke.py``.
"""

import xml.etree.ElementTree as ET

import httpx
import pytest

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
def test_rss_source_url_is_alive_and_returns_valid_xml(source: SourceConfig) -> None:
    """Mỗi URL RSS phải còn sống và trả về XML hợp lệ có ít nhất một <item>.

    Requirements: 2.2
    """
    with httpx.Client(
        timeout=FETCH_TIMEOUT, follow_redirects=True
    ) as client:
        response = client.get(source.url)

    # Còn sống: phản hồi HTTP thành công, không bị chặn/lỗi.
    assert response.status_code < 400, (
        f"[{source.name}] {source.url} trả HTTP {response.status_code}"
    )

    # XML hợp lệ: parse được bằng ElementTree.
    try:
        root = ET.fromstring(response.content)
    except ET.ParseError as exc:
        pytest.fail(
            f"[{source.name}] {source.url} không trả XML hợp lệ: {exc}"
        )

    # Feed có nội dung: tồn tại ít nhất một mục <item>.
    items = root.findall(".//item")
    assert items, (
        f"[{source.name}] {source.url} là XML hợp lệ nhưng không có <item> nào"
    )
