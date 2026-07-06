"""Integration test end-to-end cho pipeline thu thập tin tức (task 15.2).

Mục tiêu: chạy ``ingest_news_articles()`` đi qua các tầng THẬT (registry +
``resolve_active_sources`` thật → ``discover_rss`` parse XML thật → ``select_top_n``
→ ``pre_filter`` thật → ``filter_new_urls`` → ``extract_full_content`` trích xuất
bằng trafilatura thật → ``full_content_filter`` thật → ``upsert_news_articles``),
chỉ mock ở biên HTTP bằng ``httpx.MockTransport``.

Cách inject transport: orchestrator tự khởi tạo ``httpx.Client(...)`` bên trong
(cho cả tải RSS lẫn tải trang bài). Vì thế ta thay constructor ``httpx.Client``
tại biên ``app.services.crawler`` bằng một lớp con luôn gắn ``MockTransport``;
nhờ vậy mọi request của lần chạy được điều hướng tới feed/trang giả.

Các biên không phải HTTP được giữ tối thiểu:
- ``RateLimiter`` thay bằng no-op để tránh trễ 1 req/s khi nhiều bài cùng host.
- ``PlaywrightFallback`` thay bằng fake (phòng vệ, KHÔNG khởi chạy chromium
  thật). Với body đủ dài, hàng đợi Playwright rỗng nên fake cũng không bị gọi.

Validates: Requirements 4.1, 4.7, 5.2, 5.3, 8.1, 13.3
"""

from unittest.mock import patch

import httpx
from sqlmodel import Session, select

import app.services.crawler as crawler_mod
from app.core.config import settings
from app.models.news import NewsArticle
from app.models.stock import StockTicker

MIN = settings.MIN_CONTENT_LENGTH

RSS_URL = "https://cafef.vn/thi-truong-chung-khoan.rss"
ARTICLE_PASS_URL = "https://cafef.vn/vic-tang-tran.html"
ARTICLE_PREFILTER_REJECT_URL = "https://cafef.vn/thoi-tiet-cuoi-tuan.html"
ARTICLE_BODYFILTER_REJECT_URL = "https://cafef.vn/ban-tin-tong-hop.html"


# ---------------------------------------------------------------------------
# Fixtures dữ liệu giả
# ---------------------------------------------------------------------------

# Teaser bài đạt: chứa ticker VIC + từ khóa tài chính => qua được pre_filter.
TEASER_PASS = "Cổ phiếu VIC tăng trần trong phiên giao dịch chứng khoán sôi động."

# Teaser bài rớt pre_filter: không có ticker nào => bị loại trước khi tải.
TEASER_PREFILTER_REJECT = "Thời tiết cuối tuần nắng nóng diện rộng trên cả nước."

# Teaser bài qua pre_filter nhưng body sẽ rớt full_content_filter (body thiếu ticker).
TEASER_BODYFILTER_REJECT = (
    "Cổ phiếu VIC được nhà đầu tư quan tâm trên thị trường chứng khoán."
)

RSS_FEED = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>CafeF - Thị trường chứng khoán</title>
    <link>https://cafef.vn</link>
    <description>Tin chứng khoán</description>
    <item>
      <title>VIC tăng trần phiên chứng khoán hôm nay</title>
      <link>{ARTICLE_PASS_URL}</link>
      <description>{TEASER_PASS}</description>
      <pubDate>Mon, 01 Jul 2024 08:00:00 +0700</pubDate>
    </item>
    <item>
      <title>Dự báo thời tiết cuối tuần nắng nóng</title>
      <link>{ARTICLE_PREFILTER_REJECT_URL}</link>
      <description>{TEASER_PREFILTER_REJECT}</description>
      <pubDate>Mon, 01 Jul 2024 09:00:00 +0700</pubDate>
    </item>
    <item>
      <title>Bản tin tổng hợp cuối tuần</title>
      <link>{ARTICLE_BODYFILTER_REJECT_URL}</link>
      <description>{TEASER_BODYFILTER_REJECT}</description>
      <pubDate>Mon, 01 Jul 2024 10:00:00 +0700</pubDate>
    </item>
  </channel>
</rss>
"""

# Body bài đạt: đủ dài (> MIN_CONTENT_LENGTH) và chứa ticker VIC + từ khóa tài
# chính để qua full_content_filter.
_PASS_PARAGRAPH = (
    "Cổ phiếu VIC của Tập đoàn Vingroup ghi nhận phiên giao dịch chứng khoán "
    "sôi động khi dòng tiền nội tiếp tục đổ vào nhóm vốn hóa lớn. Nhiều nhà đầu "
    "tư kỳ vọng lợi nhuận quý này tăng trưởng mạnh nhờ kết quả kinh doanh khả "
    "quan của doanh nghiệp đầu ngành. Thanh khoản thị trường cải thiện rõ rệt "
    "so với tuần trước, khối ngoại trở lại mua ròng nhóm cổ phiếu trụ."
)
ARTICLE_PASS_HTML = (
    "<html><head><title>VIC tăng trần</title></head><body><article>"
    + "".join(f"<p>{_PASS_PARAGRAPH}</p>" for _ in range(4))
    + "</article></body></html>"
)

# Body bài rớt full_content_filter: đủ dài nhưng KHÔNG chứa ticker nào => bị loại
# ở tầng lọc full body (không phải bị loại vì quá ngắn).
_NO_TICKER_PARAGRAPH = (
    "Thời tiết cuối tuần trên cả nước nắng nóng diện rộng, nhiệt độ cao nhất phổ "
    "biến từ ba mươi lăm đến ba mươi tám độ. Người dân được khuyến cáo hạn chế ra "
    "đường vào giờ trưa và bổ sung đủ nước. Chiều tối nhiều khu vực có mưa dông "
    "rải rác kèm nguy cơ lốc, sét và mưa đá cục bộ trong thời gian ngắn."
)
ARTICLE_BODYFILTER_REJECT_HTML = (
    "<html><head><title>Bản tin tổng hợp</title></head><body><article>"
    + "".join(f"<p>{_NO_TICKER_PARAGRAPH}</p>" for _ in range(4))
    + "</article></body></html>"
)


class _NoRateLimiter:
    """RateLimiter no-op để giữ test nhanh và xác định (bỏ trễ per-host)."""

    def __init__(self, *args, **kwargs):
        pass

    def acquire(self, host):  # noqa: D401 - no-op
        pass


class _FakePlaywright:
    """Playwright fallback giả: KHÔNG khởi chạy chromium thật (phòng vệ)."""

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def extract(self, url):
        from app.services.extraction.content import ExtractionResult

        return ExtractionResult(ok=False, error="fake_no_browser")


def _mock_transport() -> httpx.MockTransport:
    """Transport định tuyến request theo URL tới feed/trang bài giả."""

    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if url == RSS_URL:
            return httpx.Response(
                200,
                content=RSS_FEED.encode("utf-8"),
                headers={"content-type": "application/rss+xml; charset=utf-8"},
            )
        if url == ARTICLE_PASS_URL:
            return httpx.Response(200, text=ARTICLE_PASS_HTML)
        if url == ARTICLE_BODYFILTER_REJECT_URL:
            return httpx.Response(200, text=ARTICLE_BODYFILTER_REJECT_HTML)
        # Bài rớt pre_filter không bao giờ được tải; mọi URL lạ trả 404.
        return httpx.Response(404, text="Not Found")

    return httpx.MockTransport(handler)


def _mock_client_cls(transport: httpx.MockTransport):
    """Tạo lớp con httpx.Client luôn gắn transport giả khi khởi tạo."""

    class _MockClient(httpx.Client):
        def __init__(self, *args, **kwargs):
            kwargs["transport"] = transport
            super().__init__(*args, **kwargs)

    return _MockClient


# ---------------------------------------------------------------------------
# Test end-to-end
# ---------------------------------------------------------------------------


def test_ingest_end_to_end_filters_fetches_and_saves(session: Session):
    """End-to-end: lọc → tải → lưu với content + summary; source_health đầy đủ.

    - Seed ticker VIC active để filter có thể đạt.
    - Feed có 3 bài: (A) đạt cả hai tầng lọc; (B) rớt pre_filter (không tải);
      (C) qua pre_filter nhưng rớt full_content_filter (body thiếu ticker).
    - Khẳng định chỉ bài A được lưu, mang content (full body) + summary (teaser),
      status pending; source_health phản ánh nguồn với status ok.
    """
    session.add(StockTicker(ticker="VIC", name="Vingroup", market="HOSE", is_active=True))
    session.commit()

    transport = _mock_transport()

    with patch.object(crawler_mod, "RateLimiter", _NoRateLimiter), \
            patch.object(crawler_mod, "PlaywrightFallback", _FakePlaywright), \
            patch.object(crawler_mod.httpx, "Client", _mock_client_cls(transport)):
        results = crawler_mod.ingest_news_articles(
            session, active_sources="cafef"
        )

    # --- Tổng hợp kết quả ---------------------------------------------------
    # 3 bài được khám phá từ feed (R2.1).
    assert results["total_scraped"] == 3
    # Chỉ 1 bài (A) qua được cả hai tầng lọc và được lưu (R4.1, R4.7).
    assert results["total_filtered"] == 1
    assert results["total_saved"] == 1

    # --- Bài đã lưu --------------------------------------------------------
    saved = session.exec(select(NewsArticle)).all()
    assert len(saved) == 1
    article = saved[0]

    # Chỉ bài A (đạt cả hai tầng lọc) được lưu.
    assert article.url == ARTICLE_PASS_URL
    assert article.source == "CafeF"

    # content = full body trích xuất thật từ HTML giả (R5.2), đủ dài.
    assert article.content
    assert len(article.content) >= MIN
    assert "VIC" in article.content
    assert "chứng khoán" in article.content

    # summary = teaser từ RSS, độc lập với content (R5.3).
    assert article.summary == TEASER_PASS
    assert article.summary != article.content

    # Trạng thái khởi tạo để AI_Pipeline nhận diện là chưa phân tích (R13.3).
    assert article.status == "pending_entity_extraction"

    # --- Bài bị lọc không được lưu ----------------------------------------
    saved_urls = {a.url for a in saved}
    assert ARTICLE_PREFILTER_REJECT_URL not in saved_urls  # rớt pre_filter (R4.1)
    assert ARTICLE_BODYFILTER_REJECT_URL not in saved_urls  # rớt full_content_filter (R4.7)

    # --- Source health -----------------------------------------------------
    health = results["source_health"]
    assert len(health) == 1
    entry = health[0]
    assert entry["source"] == "CafeF"
    assert entry["status"] == "ok"  # feed có >=1 mục đủ title+url
    assert entry["articlesCount"] == 3  # số mục khám phá được (R8.1)
    assert entry["durationMs"] >= 0
    assert entry["errorMessage"] is None  # status ok => error rỗng

    # Không đánh dấu thất bại toàn phần khi có nguồn ok.
    assert "all_sources_failed" not in results["errors"]
