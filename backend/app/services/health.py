import datetime as dt
from dataclasses import dataclass
from typing import Literal, Optional

SourceStatus = Literal["ok", "empty", "dead", "parse_error", "blocked"]


@dataclass
class SourceHealth:
    source: str
    status: SourceStatus
    articles_count: int
    duration_ms: int
    error_message: Optional[str] = None

    def to_camel(self) -> dict:
        return {
            "source": self.source,
            "status": self.status,
            "articlesCount": self.articles_count,
            "durationMs": self.duration_ms,
            "errorMessage": self.error_message,
        }


BLOCKED_HTTP_CODES = {401, 403, 429}


def map_feed_status(
    http_status: Optional[int],
    is_valid_xml: bool,
    valid_item_count: int,
    timeout_or_dns_fail: bool,
) -> SourceStatus:
    """Ánh xạ điều kiện truy cập feed RSS sang ``SourceStatus``.

    Hàm thuần, xác định: cùng đầu vào luôn cho cùng một kết quả thuộc
    {ok, empty, dead, parse_error, blocked}.

    Quy tắc áp dụng theo đúng thứ tự ưu tiên:

    1. HTTP ∈ {401, 403, 429} → ``blocked``.
    2. timeout/DNS-fail HOẶC HTTP ≥ 400 (ngoài {401,403,429}) → ``dead``.
       Quy tắc này ưu tiên hơn ``parse_error`` khi cùng xảy ra (R2.7).
    3. Nội dung không phải XML hợp lệ (và HTTP < 400) → ``parse_error``.
    4. XML hợp lệ với 0 mục hợp lệ → ``empty``.
    5. XML hợp lệ với ≥ 1 mục hợp lệ → ``ok``.

    Args:
        http_status: Mã HTTP của phản hồi feed, hoặc ``None`` nếu không có
            phản hồi (ví dụ timeout/DNS-fail trước khi nhận được mã).
        is_valid_xml: Cờ cho biết nội dung trả về có phải XML hợp lệ không.
        valid_item_count: Số mục feed hợp lệ (đủ title + url), ``>= 0``.
        timeout_or_dns_fail: Cờ cho biết feed bị timeout hoặc không phân
            giải được tên miền.

    Returns:
        Một ``SourceStatus`` trong {ok, empty, dead, parse_error, blocked}.

    Requirements: 2.4, 2.5, 2.6, 2.7, 2.8, 2.9, 8.3, 8.4, 8.5, 8.6, 8.7
    """
    # 1. Bị chặn: truy cập bị từ chối/giới hạn.
    if http_status in BLOCKED_HTTP_CODES:
        return "blocked"

    # 2. Nguồn chết: timeout/DNS-fail hoặc HTTP >= 400 (ngoài mã blocked).
    #    Ưu tiên hơn parse_error khi vừa lỗi HTTP vừa không phải XML (R2.7).
    if timeout_or_dns_fail or (
        http_status is not None and http_status >= 400
    ):
        return "dead"

    # 3. Phản hồi được nhưng nội dung không phải XML hợp lệ.
    if not is_valid_xml:
        return "parse_error"

    # 4. XML hợp lệ nhưng không có mục nào.
    if valid_item_count == 0:
        return "empty"

    # 5. XML hợp lệ với ít nhất một mục hợp lệ.
    return "ok"


# Snapshot in-memory của Source_Health_Report lần chạy gần nhất.
# Phục vụ Jobs_View truy vấn độc lập qua GET /api/v1/news/source-health mà không
# cần kích hoạt lại một lần crawl. Không dùng bảng DB (giữ KISS); snapshot reset
# khi tiến trình khởi động lại và chỉ phản ánh các lần chạy trong cùng tiến trình.
_latest_source_health: Optional[dict] = None


def set_latest_source_health(
    source_health: list[dict], trace_id: Optional[str] = None
) -> None:
    """Lưu snapshot Source_Health_Report của lần chạy vừa hoàn tất.

    Gán nguyên một dict đã dựng sẵn (thao tác nguyên tử dưới GIL) nên an toàn khi
    đọc/ghi từ luồng crawl và luồng phục vụ request mà không cần khóa.
    """
    global _latest_source_health
    _latest_source_health = {
        "sourceHealth": source_health,
        "generatedAt": dt.datetime.now(dt.timezone.utc).isoformat(),
        "traceId": trace_id,
    }


def get_latest_source_health() -> Optional[dict]:
    """Trả snapshot Source_Health_Report gần nhất, hoặc ``None`` nếu chưa có."""
    return _latest_source_health
