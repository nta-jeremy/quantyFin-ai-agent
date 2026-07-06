"""Playwright Fallback: tầng 3 (dự phòng có điều kiện) của pipeline thu thập.

Dùng Playwright sync API để lấy full body cho các nguồn không có RSS hoặc khi
Content_Extractor không lấy đủ nội dung. Worker hoạt động tuần tự, tại mỗi thời
điểm chỉ mở tối đa một thực thể trình duyệt chromium (R6.3, R6.4, R9.4, R9.5),
tắt tải hình ảnh để tiết kiệm tài nguyên (R6.5), và đóng trình duyệt cuối lần
chạy để giải phóng bộ nhớ (R6.6, R9.6).

Toàn bộ thao tác Playwright được chạy trên một thread riêng (single-thread
executor). Điều này cần thiết vì sync API không thể chạy bên trong một event
loop asyncio đang hoạt động; orchestrator được gọi từ handler async ``/ingest``,
nên việc đóng gói trong thread riêng đảm bảo an toàn.

``playwright.sync_api`` được import lazy bên trong thread worker để module này
import được kể cả khi chưa cài đặt thư viện hoặc binary chromium.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from typing import Any, Optional

import trafilatura

from app.services.extraction.content import ExtractionResult
from app.services.extraction.politeness import get_user_agent

# Thời gian chờ tối đa khi xử lý một bài (R6.6).
PLAYWRIGHT_TIMEOUT_MS = 30_000


class PlaywrightFallback:
    """Worker tuần tự dùng Playwright sync API, tối đa 1 browser tại một thời điểm.

    Dùng làm context manager::

        with PlaywrightFallback() as pw:
            result = pw.extract(url)
    """

    def __init__(self) -> None:
        self._executor: Optional[ThreadPoolExecutor] = None
        self._playwright: Any = None
        self._browser: Any = None

    def __enter__(self) -> "PlaywrightFallback":
        # Một thread riêng cho mọi thao tác Playwright: sync API không chạy được
        # trong event loop asyncio đang hoạt động (handler async /ingest).
        self._executor = ThreadPoolExecutor(max_workers=1)
        self._executor.submit(self._start).result()
        return self

    def _start(self) -> None:
        # Lazy import: module vẫn import được khi chưa cài playwright/chromium.
        from playwright.sync_api import sync_playwright

        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(headless=True)

    def __exit__(self, *exc: Any) -> None:
        if self._executor is None:
            return
        try:
            self._executor.submit(self._stop).result()
        finally:
            self._executor.shutdown(wait=True)
            self._executor = None

    def _stop(self) -> None:
        # Đóng browser và dừng Playwright để giải phóng bộ nhớ (R6.6, R9.6).
        try:
            if self._browser is not None:
                self._browser.close()
        finally:
            self._browser = None
            if self._playwright is not None:
                self._playwright.stop()
                self._playwright = None

    def extract(self, url: str) -> ExtractionResult:
        """Lấy full body cho một bài, tối đa một lần thử (R6.2).

        - Quá ``PLAYWRIGHT_TIMEOUT_MS`` (30s) => ``ok=False, error="timeout"`` (R6.6).
        - Lỗi xử lý khác => ``ok=False`` kèm mô tả lỗi (R6.8).

        ``needs_fallback`` giữ giá trị mặc định: Playwright là tầng cuối, không có
        fallback tiếp theo; orchestrator thực thi kiểm tra độ dài cuối cùng (R6.7).
        """
        if self._executor is None:
            return ExtractionResult(ok=False, error="not_started")
        return self._executor.submit(self._extract, url).result()

    def _extract(self, url: str) -> ExtractionResult:
        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

        context = None
        page = None
        try:
            context = self._browser.new_context(user_agent=get_user_agent())
            # Tắt tải hình ảnh để tiết kiệm tài nguyên (R6.5).
            context.route(
                "**/*",
                lambda route: (
                    route.abort()
                    if route.request.resource_type == "image"
                    else route.continue_()
                ),
            )
            page = context.new_page()
            page.goto(
                url,
                timeout=PLAYWRIGHT_TIMEOUT_MS,
                wait_until="domcontentloaded",
            )
            html = page.content()
        except PlaywrightTimeoutError:
            return ExtractionResult(ok=False, error="timeout")
        except Exception as exc:  # lỗi xử lý khác (R6.8)
            return ExtractionResult(ok=False, error=f"playwright_error: {exc}")
        finally:
            if page is not None:
                try:
                    page.close()
                except Exception:
                    pass
            if context is not None:
                try:
                    context.close()
                except Exception:
                    pass

        body = trafilatura.extract(html) or ""
        return ExtractionResult(ok=True, body=body)
