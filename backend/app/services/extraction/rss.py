"""RSS Discovery: tầng 1 của pipeline thu thập tin tức.

Đọc feed RSS của một nguồn ``type=rss`` để lấy danh sách bài gồm tiêu đề, URL
tuyệt đối và teaser. Logic parse XML / ``clean_html`` / ``parse_pub_date`` được
chuyển từ ``BaseScraper`` sang đây (không giữ class hierarchy).

Hàm ``discover_rss`` không raise ra ngoài: mọi lỗi nguồn được chuyển thành
``(list[ArticleStub], SourceStatus)`` thông qua ``map_feed_status``.
"""

import datetime as dt
import email.utils
import html
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from urllib.parse import urljoin

import httpx

from app.core.logging import logger
from app.services.health import SourceStatus, map_feed_status
from app.services.sources.registry import SourceConfig

MAX_ITEMS = 100
FETCH_TIMEOUT = 30.0


@dataclass
class ArticleStub:
    title: str
    url: str            # tuyệt đối (scheme http/https)
    teaser: str         # "" nếu mục feed không có teaser
    published_at: dt.datetime
    source: str         # SourceConfig.name


def clean_html(raw_html: str) -> str:
    """Loại bỏ thẻ HTML và giải mã entity, trả về chuỗi đã trim."""
    if not raw_html:
        return ""
    clean_re = re.compile("<.*?>")
    cleaned = re.sub(clean_re, "", raw_html).strip()
    return html.unescape(cleaned)


def parse_pub_date(pub_date_str: str) -> dt.datetime:
    """Parse chuỗi pubDate RSS sang ``datetime`` UTC naive; lỗi => thời điểm hiện tại."""
    if not pub_date_str:
        return dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)
    try:
        dt_obj = email.utils.parsedate_to_datetime(pub_date_str)
        if dt_obj.tzinfo:
            dt_obj = dt_obj.astimezone(dt.timezone.utc).replace(tzinfo=None)
        else:
            dt_obj = dt_obj.replace(tzinfo=None)
        return dt_obj
    except Exception as e:
        logger.warning(
            f"Failed to parse publication date '{pub_date_str}': {str(e)}. "
            "Using current time."
        )
        return dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)


def _parse_items(xml_content: bytes, source: SourceConfig) -> list[ArticleStub]:
    """Parse nội dung XML thành danh sách ``ArticleStub`` đã làm sạch.

    - Lấy tối đa ``MAX_ITEMS`` mục đầu theo thứ tự feed (R2.1).
    - Chuẩn hóa URL tuyệt đối qua ``urljoin`` (R2.3).
    - Bỏ mục thiếu title hoặc url (R2.10); teaser rỗng khi thiếu (R2.1).

    Raise ``ET.ParseError`` nếu nội dung không phải XML hợp lệ; caller chịu
    trách nhiệm bắt và ánh xạ sang ``parse_error``.
    """
    root = ET.fromstring(xml_content)
    items = root.findall(".//item")
    logger.info(f"[{source.name}] Found {len(items)} items in RSS feed.")

    stubs: list[ArticleStub] = []
    for item in items[:MAX_ITEMS]:
        title_el = item.find("title")
        link_el = item.find("link")
        desc_el = item.find("description")
        pub_date_el = item.find("pubDate")

        title = title_el.text if title_el is not None else ""
        url = link_el.text if link_el is not None else ""
        description = desc_el.text if desc_el is not None else ""
        pub_date_raw = pub_date_el.text if pub_date_el is not None else ""

        title = title[:500].strip() if title else ""
        url = url.strip() if url else ""
        if url:
            url = urljoin(source.url, url)

        if not title or not url:
            continue

        stubs.append(
            ArticleStub(
                title=title,
                url=url,
                teaser=clean_html(description) if description else "",
                published_at=parse_pub_date(pub_date_raw),
                source=source.name,
            )
        )

    return stubs


def discover_rss(
    source: SourceConfig, client: httpx.Client
) -> tuple[list[ArticleStub], SourceStatus]:
    """Tải và parse feed RSS của một nguồn ``type=rss``.

    Trả về ``(stubs, status)`` với ``status`` thuộc
    {ok, empty, dead, parse_error, blocked}. Không raise ra ngoài: mọi lỗi
    nguồn (timeout/DNS, HTTP lỗi, XML hỏng) được phản ánh qua ``status`` và
    danh sách stub rỗng.

    Requirements: 2.1, 2.2, 2.3, 2.10
    """
    try:
        response = client.get(
            source.url, timeout=FETCH_TIMEOUT, follow_redirects=True
        )
    except httpx.TimeoutException:
        logger.error(f"[{source.name}] RSS fetch timeout sau {FETCH_TIMEOUT}s")
        return [], map_feed_status(None, False, 0, True)
    except httpx.RequestError as e:
        # Bao gồm lỗi phân giải DNS và các lỗi kết nối mạng khác.
        logger.error(f"[{source.name}] RSS fetch lỗi kết nối: {str(e)}")
        return [], map_feed_status(None, False, 0, True)

    http_status = response.status_code

    # HTTP lỗi (blocked/dead) được ưu tiên: không cần parse nội dung.
    if http_status >= 400:
        status = map_feed_status(http_status, False, 0, False)
        logger.error(
            f"[{source.name}] RSS trả HTTP {http_status} => status '{status}'"
        )
        return [], status

    try:
        stubs = _parse_items(response.content, source)
    except ET.ParseError as e:
        logger.error(f"[{source.name}] XML parsing failed: {str(e)}")
        return [], map_feed_status(http_status, False, 0, False)

    status = map_feed_status(http_status, True, len(stubs), False)
    return stubs, status
