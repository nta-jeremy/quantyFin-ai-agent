"""Bộ lọc hai giai đoạn cho pipeline thu thập tin tức.

``pre_filter`` là bộ lọc nhẹ chạy trên ``title + teaser`` trước khi tải full body
(R4.1, R4.2). ``full_content_filter`` là bộ lọc chính xác chạy trên ``title + body``
trước khi lưu (R4.7, R4.8). Cả hai tái sử dụng ``zero_cost_filter`` hiện có
(ticker + financial keyword) làm tiêu chí nền.

``zero_cost_filter`` được import bên trong hàm để tránh circular import: orchestrator
``app.services.crawler`` sẽ import module này khi điều phối pipeline.
"""


def pre_filter(title: str, teaser: str, active_tickers: list[str]) -> bool:
    """Lọc nhẹ trên title + teaser trước khi tải full body (R4.1, R4.2)."""
    from app.services.crawler import zero_cost_filter

    return zero_cost_filter(title, teaser, active_tickers)


def full_content_filter(title: str, body: str, active_tickers: list[str]) -> bool:
    """Lọc chính xác trên full body trước khi lưu (R4.7, R4.8)."""
    from app.services.crawler import zero_cost_filter

    return zero_cost_filter(title, body, active_tickers)
