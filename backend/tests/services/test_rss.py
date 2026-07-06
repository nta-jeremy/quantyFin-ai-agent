"""Test cho RSS Discovery (tầng 1): app.services.extraction.rss.

Gồm:
- Property 5: RSS Discovery giới hạn và làm sạch mục (Hypothesis).
- Property 6: URL bài viết luôn được chuẩn hóa tuyệt đối (Hypothesis).
- Unit test discover_rss với HTTP mock (httpx.MockTransport).

Mock HTTP bằng httpx.MockTransport: dựng một httpx.Client với transport giả,
truyền trực tiếp vào discover_rss theo đúng chữ ký
discover_rss(source, client).
"""

from urllib.parse import urlparse

import httpx
from hypothesis import given, settings as hyp_settings, strategies as st

from app.services.extraction.rss import ArticleStub, discover_rss
from app.services.sources.registry import SourceConfig

FEED_URL = "https://example.com/feed.rss"


def _source(url: str = FEED_URL) -> SourceConfig:
    """Tạo một SourceConfig type=rss tối giản cho test."""
    return SourceConfig(
        name="TestSource",
        type="rss",
        url=url,
        topics=("kinh tế",),
        tier=1,
    )


def _client(handler) -> httpx.Client:
    """Tạo httpx.Client dùng MockTransport với handler tùy biến."""
    return httpx.Client(transport=httpx.MockTransport(handler))


def _xml_handler(xml_body: str):
    """Handler trả về 200 kèm nội dung XML cho trước."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=xml_body)

    return handler


# ---------------------------------------------------------------------------
# Hypothesis strategies cho feed XML
# ---------------------------------------------------------------------------

# Từ an toàn: chỉ chữ/số, không chứa khoảng trắng hay ký tự đặc biệt XML
# (<, >, &) nên không cần escape khi dựng XML và strip() là phép đồng nhất.
_word = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
    min_size=1,
    max_size=15,
)

# URL bài viết: tương đối ("/a/b") hoặc tuyệt đối ("https://host.vn/p").
_rel_url = st.builds(lambda a, b: f"/{a}/{b}", _word, _word)
_abs_url = st.builds(lambda h, p: f"https://{h}.vn/{p}", _word, _word)
_any_url = st.one_of(_rel_url, _abs_url)

# Một mục feed: title/url có thể vắng (None) để mô phỏng mục thiếu trường;
# teaser có thể vắng để kiểm teaser rỗng.
_item = st.fixed_dictionaries(
    {
        "title": st.one_of(st.none(), _word),
        "url": st.one_of(st.none(), _any_url),
        "teaser": st.one_of(st.none(), _word),
    }
)


def _build_feed(items: list[dict]) -> str:
    """Dựng chuỗi XML RSS hợp lệ từ danh sách mục.

    Mục có giá trị None cho một trường nghĩa là phần tử đó vắng mặt trong XML.
    """
    parts = ['<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel>']
    for it in items:
        parts.append("<item>")
        if it["title"] is not None:
            parts.append(f"<title>{it['title']}</title>")
        if it["url"] is not None:
            parts.append(f"<link>{it['url']}</link>")
        if it["teaser"] is not None:
            parts.append(f"<description>{it['teaser']}</description>")
        parts.append("</item>")
    parts.append("</channel></rss>")
    return "".join(parts)


# ---------------------------------------------------------------------------
# Property 5: RSS Discovery giới hạn và làm sạch mục
# ---------------------------------------------------------------------------

# Feature: news-crawler-fulltext, Property 5: RSS Discovery giới hạn và làm sạch mục.
# Với mọi feed XML hợp lệ chứa n mục (một số thiếu title/url/teaser),
# discover_rss() trả về danh sách stub sao cho: độ dài <= 100; mọi stub có
# title và url khác rỗng (mục thiếu title/url bị loại); teaser luôn là chuỗi
# (rỗng khi thiếu); và thứ tự stub giữ nguyên thứ tự xuất hiện trong feed.
# Validates: Requirements 2.1, 2.10
@hyp_settings(max_examples=100)
@given(items=st.lists(_item, min_size=0, max_size=130))
def test_property_5_limit_and_clean_items(items):
    feed = _build_feed(items)
    source = _source()

    with _client(_xml_handler(feed)) as client:
        stubs, status = discover_rss(source, client)

    # Chỉ 100 mục đầu được xem xét, sau đó lọc mục thiếu title/url.
    considered = items[:100]
    expected = [
        it for it in considered if it["title"] is not None and it["url"] is not None
    ]

    # Độ dài <= 100.
    assert len(stubs) <= 100
    # Mọi stub có title và url khác rỗng; teaser luôn là chuỗi.
    for s in stubs:
        assert s.title != ""
        assert s.url != ""
        assert isinstance(s.teaser, str)
    # Số lượng và thứ tự khớp đúng danh sách mục hợp lệ trong 100 mục đầu.
    assert len(stubs) == len(expected)
    assert [s.title for s in stubs] == [it["title"] for it in expected]


# ---------------------------------------------------------------------------
# Property 6: URL bài viết luôn được chuẩn hóa tuyệt đối
# ---------------------------------------------------------------------------

# Feature: news-crawler-fulltext, Property 6: URL bài viết luôn được chuẩn hóa tuyệt đối.
# Với mọi feed có URL bài viết ở dạng tương đối hoặc tuyệt đối, mọi
# ArticleStub.url trả về từ discover_rss() đều là URL tuyệt đối (scheme
# http/https).
# Validates: Requirements 2.3
@hyp_settings(max_examples=100)
@given(
    titles=st.lists(_word, min_size=1, max_size=20),
    urls=st.lists(_any_url, min_size=1, max_size=20),
)
def test_property_6_urls_absolute(titles, urls):
    # Ghép title với url để mọi mục đều hợp lệ (có đủ title + url).
    n = min(len(titles), len(urls))
    items = [
        {"title": titles[i], "url": urls[i], "teaser": None} for i in range(n)
    ]
    feed = _build_feed(items)
    source = _source()

    with _client(_xml_handler(feed)) as client:
        stubs, status = discover_rss(source, client)

    assert len(stubs) == n
    for s in stubs:
        scheme = urlparse(s.url).scheme
        assert scheme in ("http", "https"), f"URL không tuyệt đối: {s.url!r}"


# ---------------------------------------------------------------------------
# Unit test discover_rss với HTTP mock (Task 6.4)
# ---------------------------------------------------------------------------

_VALID_FEED = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    "<rss version=\"2.0\"><channel>"
    "<title>Kênh tin</title>"
    "<item><title>Bài 1</title><link>https://example.com/bai-1</link>"
    "<description>Teaser 1</description></item>"
    "<item><title>Bài 2</title><link>/bai-2</link></item>"
    "</channel></rss>"
)


# Validates: Requirements 2.8 — feed XML hợp lệ với >=1 mục đủ title+url => ok.
def test_discover_rss_valid_feed_ok():
    with _client(_xml_handler(_VALID_FEED)) as client:
        stubs, status = discover_rss(_source(), client)

    assert status == "ok"
    assert len(stubs) == 2
    assert all(isinstance(s, ArticleStub) for s in stubs)
    # URL tương đối được chuẩn hóa tuyệt đối.
    assert stubs[1].url == "https://example.com/bai-2"
    # Mục không có description => teaser rỗng.
    assert stubs[1].teaser == ""


# Validates: Requirements 2.5 — feed XML hợp lệ nhưng không có mục => empty.
def test_discover_rss_empty_channel():
    empty_feed = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<rss version="2.0"><channel><title>Rỗng</title></channel></rss>'
    )
    with _client(_xml_handler(empty_feed)) as client:
        stubs, status = discover_rss(_source(), client)

    assert status == "empty"
    assert stubs == []


# Validates: Requirements 2.4 — nội dung không phải XML hợp lệ (HTML) => parse_error.
def test_discover_rss_html_instead_of_xml():
    html_body = "<html><body><br>Không phải XML hợp lệ</body></html>"
    with _client(_xml_handler(html_body)) as client:
        stubs, status = discover_rss(_source(), client)

    assert status == "parse_error"
    assert stubs == []


# Validates: Requirements 2.9 — HTTP 403 => blocked.
def test_discover_rss_http_403_blocked():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(403, text="Forbidden")

    with _client(handler) as client:
        stubs, status = discover_rss(_source(), client)

    assert status == "blocked"
    assert stubs == []


# Validates: Requirements 2.9 — HTTP 429 => blocked.
def test_discover_rss_http_429_blocked():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, text="Too Many Requests")

    with _client(handler) as client:
        stubs, status = discover_rss(_source(), client)

    assert status == "blocked"
    assert stubs == []


# Validates: Requirements 2.6 — HTTP >= 400 ngoài {401,403,429} => dead.
def test_discover_rss_http_500_dead():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="Server Error")

    with _client(handler) as client:
        stubs, status = discover_rss(_source(), client)

    assert status == "dead"
    assert stubs == []


# Validates: Requirements 2.6 — timeout 30s => dead.
def test_discover_rss_timeout_dead():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("request timed out", request=request)

    with _client(handler) as client:
        stubs, status = discover_rss(_source(), client)

    assert status == "dead"
    assert stubs == []


# Validates: Requirements 2.6 — không phân giải DNS / lỗi kết nối => dead.
def test_discover_rss_dns_failure_dead():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("name resolution failed", request=request)

    with _client(handler) as client:
        stubs, status = discover_rss(_source(), client)

    assert status == "dead"
    assert stubs == []
