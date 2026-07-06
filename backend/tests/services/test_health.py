from hypothesis import given, settings, strategies as st

from app.services.health import SourceHealth, map_feed_status

# Tập giá trị Source_Status hợp lệ theo Requirements 8.2.
VALID_STATUSES = {"ok", "empty", "dead", "parse_error", "blocked"}

# Tên nguồn không rỗng (sau khi trim) làm định danh nguồn.
source_names = st.text(min_size=1, max_size=100).filter(lambda s: s.strip() != "")


def assemble_source_health(
    source: str,
    http_status,
    is_valid_xml: bool,
    valid_item_count: int,
    timeout_or_dns_fail: bool,
    duration_ms: int,
) -> SourceHealth:
    """Lắp ráp một ``SourceHealth`` theo đúng hợp đồng của một lần chạy crawl.

    Phản ánh cách orchestrator dựng bản ghi sức khỏe nguồn: trạng thái suy ra
    từ ``map_feed_status`` (mã production), và khi trạng thái khác ``ok`` thì
    đính kèm thông điệp lỗi không rỗng có chứa định danh nguồn (R8.1, R10.1).
    """
    status = map_feed_status(
        http_status=http_status,
        is_valid_xml=is_valid_xml,
        valid_item_count=valid_item_count,
        timeout_or_dns_fail=timeout_or_dns_fail,
    )
    error_message = None
    if status != "ok":
        error_message = f"[{source}] feed status={status}"
    return SourceHealth(
        source=source,
        status=status,
        articles_count=valid_item_count,
        duration_ms=duration_ms,
        error_message=error_message,
    )


# Feature: news-crawler-fulltext, Property 16: Bất biến của SourceHealth.
# Với mọi SourceHealth sinh ra trong một lần chạy: status thuộc tập hợp lệ;
# articles_count >= 0; duration_ms >= 0; và nếu status != ok thì error_message
# là chuỗi khác rỗng có chứa định danh nguồn.
# Validates: Requirements 8.1, 8.2, 10.1
@settings(max_examples=100)
@given(
    source=source_names,
    http_status=st.one_of(st.none(), st.integers(min_value=100, max_value=599)),
    is_valid_xml=st.booleans(),
    valid_item_count=st.integers(min_value=0, max_value=100),
    timeout_or_dns_fail=st.booleans(),
    duration_ms=st.integers(min_value=0, max_value=600_000),
)
def test_source_health_invariant(
    source,
    http_status,
    is_valid_xml,
    valid_item_count,
    timeout_or_dns_fail,
    duration_ms,
):
    health = assemble_source_health(
        source=source,
        http_status=http_status,
        is_valid_xml=is_valid_xml,
        valid_item_count=valid_item_count,
        timeout_or_dns_fail=timeout_or_dns_fail,
        duration_ms=duration_ms,
    )

    # status luôn thuộc tập giá trị hợp lệ (R8.2).
    assert health.status in VALID_STATUSES

    # articles_count là số nguyên không âm (R8.1).
    assert isinstance(health.articles_count, int)
    assert health.articles_count >= 0

    # duration_ms là số nguyên không âm tính bằng mili-giây (R8.1).
    assert isinstance(health.duration_ms, int)
    assert health.duration_ms >= 0

    # Khi status != ok: error_message là chuỗi khác rỗng chứa định danh nguồn
    # (R8.1, R10.1).
    if health.status != "ok":
        assert isinstance(health.error_message, str)
        assert health.error_message.strip() != ""
        assert health.source in health.error_message

    # to_camel phải phản ánh trung thực các giá trị bất biến.
    camel = health.to_camel()
    assert camel["status"] in VALID_STATUSES
    assert camel["articlesCount"] == health.articles_count
    assert camel["durationMs"] == health.duration_ms
    assert camel["errorMessage"] == health.error_message


BLOCKED_CODES = {401, 403, 429}


# Feature: news-crawler-fulltext, Property 4: Ánh xạ điều kiện → SourceStatus
# là xác định. Với mọi kết quả truy cập feed (mã HTTP 200..599, cờ XML hợp lệ,
# số mục hợp lệ >= 0, cờ timeout/DNS-fail), map_feed_status trả về đúng một
# SourceStatus thuộc {ok, empty, dead, parse_error, blocked} theo quy tắc ưu
# tiên: blocked (401/403/429) > dead (timeout/DNS/HTTP>=400) > parse_error
# (không phải XML) > empty (XML, 0 mục) > ok (XML, >=1 mục).
# Validates: Requirements 2.4, 2.5, 2.6, 2.7, 2.8, 2.9, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7
@settings(max_examples=100)
@given(
    http_status=st.integers(min_value=200, max_value=599),
    is_valid_xml=st.booleans(),
    valid_item_count=st.integers(min_value=0, max_value=200),
    timeout_or_dns_fail=st.booleans(),
)
def test_map_feed_status_deterministic_rules(
    http_status, is_valid_xml, valid_item_count, timeout_or_dns_fail
):
    result = map_feed_status(
        http_status=http_status,
        is_valid_xml=is_valid_xml,
        valid_item_count=valid_item_count,
        timeout_or_dns_fail=timeout_or_dns_fail,
    )

    # Kết quả luôn thuộc tập hợp lệ.
    assert result in VALID_STATUSES

    # Hàm xác định: cùng đầu vào cho cùng kết quả.
    assert result == map_feed_status(
        http_status=http_status,
        is_valid_xml=is_valid_xml,
        valid_item_count=valid_item_count,
        timeout_or_dns_fail=timeout_or_dns_fail,
    )

    is_dead_condition = timeout_or_dns_fail or http_status >= 400

    if http_status in BLOCKED_CODES:
        assert result == "blocked"
    elif is_dead_condition:
        # dead ưu tiên hơn parse_error khi đồng thời xảy ra.
        assert result == "dead"
    elif not is_valid_xml:
        assert result == "parse_error"
    elif valid_item_count == 0:
        assert result == "empty"
    else:
        assert result == "ok"


# Feature: news-crawler-fulltext, Property 4: dead ưu tiên hơn parse_error.
# Khi HTTP >= 400 (ngoài mã blocked) và nội dung không phải XML hợp lệ đồng
# thời xảy ra, kết quả phải là `dead` chứ không phải `parse_error`.
# Validates: Requirements 2.7
@settings(max_examples=100)
@given(
    http_status=st.integers(min_value=400, max_value=599).filter(
        lambda c: c not in BLOCKED_CODES
    ),
    valid_item_count=st.integers(min_value=0, max_value=200),
)
def test_map_feed_status_dead_priority_over_parse_error(http_status, valid_item_count):
    result = map_feed_status(
        http_status=http_status,
        is_valid_xml=False,  # nội dung không phải XML hợp lệ
        valid_item_count=valid_item_count,
        timeout_or_dns_fail=False,
    )
    assert result == "dead"
