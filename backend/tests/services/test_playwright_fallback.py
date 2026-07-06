"""Test cho Playwright Fallback (tầng 3): app.services.extraction.playwright_fallback.

Playwright sync API được import lazy bên trong thread worker, nên ta tiêm một
module ``playwright.sync_api`` giả vào ``sys.modules`` để kiểm thử logic mà không
cần binary chromium thật (test nhanh, tất định). Khi vì lý do nào đó không tiêm
được, các test dựa trên trình duyệt sẽ ``skip`` thay vì treo.

Phạm vi kiểm:
- ≤ 1 lần thử cho mỗi bài (R6.2): mỗi ``extract`` chỉ gọi ``goto`` đúng một lần.
- Timeout => ``ok=False, error="timeout"`` (R6.6, R9 -- chờ tối đa 30s).
- Lỗi xử lý khác => ``ok=False`` kèm mô tả lỗi (R6.8).
- Chỉ mở đúng 1 trình duyệt và đóng vào cuối lần chạy (R6.4, R6.6, R9.4, R9.6).
- Tắt tải hình ảnh khi lấy nội dung (R6.5).
"""

import sys
import types

import pytest

from app.services.extraction import playwright_fallback as pf_module
from app.services.extraction.playwright_fallback import (
    PLAYWRIGHT_TIMEOUT_MS,
    PlaywrightFallback,
)


# ---------------------------------------------------------------------------
# Hạ tầng mock: module playwright.sync_api giả + recorder theo dõi hành vi
# ---------------------------------------------------------------------------


class _Recorder:
    """Theo dõi vòng đời trình duyệt và các lời gọi để khẳng định bất biến."""

    def __init__(self):
        self.launch_count = 0          # số trình duyệt được khởi tạo
        self.browser_close_count = 0   # số lần browser.close()
        self.playwright_stop_count = 0
        self.goto_calls = []           # mỗi phần tử = kwargs của một lần goto
        self.route_patterns = []       # các pattern đã đăng ký route (R6.5)
        self.image_route_handler = None
        # Hành vi của page.goto: "ok" | "timeout" | "error".
        self.goto_behavior = "ok"
        self.html = "<html><body><p>full body</p></body></html>"


class _FakeTimeoutError(Exception):
    """Đóng vai playwright.sync_api.TimeoutError."""


class _FakeRequest:
    def __init__(self, resource_type):
        self.resource_type = resource_type


class _FakeRoute:
    def __init__(self, resource_type):
        self.request = _FakeRequest(resource_type)
        self.aborted = False
        self.continued = False

    def abort(self):
        self.aborted = True

    def continue_(self):
        self.continued = True


class _FakePage:
    def __init__(self, recorder):
        self._rec = recorder

    def goto(self, url, **kwargs):
        self._rec.goto_calls.append(kwargs)
        if self._rec.goto_behavior == "timeout":
            raise _FakeTimeoutError("navigation timeout")
        if self._rec.goto_behavior == "error":
            raise ValueError("boom while navigating")

    def content(self):
        return self._rec.html

    def close(self):
        pass


class _FakeContext:
    def __init__(self, recorder):
        self._rec = recorder

    def route(self, pattern, handler):
        self._rec.route_patterns.append(pattern)
        # Bắt handler để kiểm thử logic chặn ảnh (R6.5).
        self._rec.image_route_handler = handler

    def new_page(self):
        return _FakePage(self._rec)

    def close(self):
        pass


class _FakeBrowser:
    def __init__(self, recorder):
        self._rec = recorder

    def new_context(self, **kwargs):
        return _FakeContext(self._rec)

    def close(self):
        self._rec.browser_close_count += 1


class _FakeChromium:
    def __init__(self, recorder):
        self._rec = recorder

    def launch(self, **kwargs):
        self._rec.launch_count += 1
        return _FakeBrowser(self._rec)


class _FakePlaywrightInstance:
    def __init__(self, recorder):
        self._rec = recorder
        self.chromium = _FakeChromium(recorder)

    def stop(self):
        self._rec.playwright_stop_count += 1


class _FakeSyncPlaywrightFactory:
    def __init__(self, recorder):
        self._rec = recorder

    def start(self):
        return _FakePlaywrightInstance(self._rec)


@pytest.fixture
def recorder(monkeypatch):
    """Tiêm module ``playwright.sync_api`` giả; trả về recorder để khẳng định.

    Bọc trafilatura.extract để trả về body có kiểm soát theo recorder.html.
    """
    rec = _Recorder()

    fake_module = types.ModuleType("playwright.sync_api")
    fake_module.sync_playwright = lambda: _FakeSyncPlaywrightFactory(rec)
    fake_module.TimeoutError = _FakeTimeoutError

    # Đảm bảo gói cha tồn tại để `from playwright.sync_api import ...` hoạt động.
    if "playwright" not in sys.modules:
        monkeypatch.setitem(sys.modules, "playwright", types.ModuleType("playwright"))
    monkeypatch.setitem(sys.modules, "playwright.sync_api", fake_module)

    # trafilatura trả về thân bài đã trích xuất từ html (cô lập logic Playwright).
    monkeypatch.setattr(
        pf_module.trafilatura, "extract", lambda html: "extracted: " + html
    )
    return rec


URL = "https://example.com/bai-viet"


# ---------------------------------------------------------------------------
# Vòng đời trình duyệt: chỉ 1 browser, đóng vào cuối lần chạy (R6.4, R6.6, R9.4, R9.6)
# ---------------------------------------------------------------------------


# Validates: Requirements 6.4, 9.4 — tối đa một trình duyệt tại một thời điểm.
# Validates: Requirements 6.6, 9.6 — đóng trình duyệt cuối lần chạy.
def test_single_browser_launched_and_closed_at_end(recorder):
    with PlaywrightFallback() as pw:
        # Trong lúc đang chạy: đúng 1 trình duyệt mở, chưa đóng.
        assert recorder.launch_count == 1
        assert recorder.browser_close_count == 0
        # Nhiều bài vẫn dùng chung một trình duyệt (tuần tự, không mở thêm).
        pw.extract(URL)
        pw.extract(URL + "-2")
        assert recorder.launch_count == 1

    # Sau khi thoát context: trình duyệt đã đóng và playwright đã dừng.
    assert recorder.launch_count == 1
    assert recorder.browser_close_count == 1
    assert recorder.playwright_stop_count == 1


# ---------------------------------------------------------------------------
# ≤ 1 lần thử cho mỗi bài (R6.2)
# ---------------------------------------------------------------------------


# Validates: Requirements 6.2 — Playwright thử lấy full body tối đa một lần.
def test_extract_attempts_at_most_once(recorder):
    with PlaywrightFallback() as pw:
        result = pw.extract(URL)

    assert result.ok is True
    assert result.body == "extracted: " + recorder.html
    # Đúng một lần điều hướng cho một bài => không có retry.
    assert len(recorder.goto_calls) == 1


# Validates: Requirements 6.2 — timeout điều hướng dùng đúng ngưỡng 30s.
def test_extract_uses_configured_timeout(recorder):
    with PlaywrightFallback() as pw:
        pw.extract(URL)

    assert recorder.goto_calls[0]["timeout"] == PLAYWRIGHT_TIMEOUT_MS


# ---------------------------------------------------------------------------
# Timeout và lỗi xử lý (R6.6, R6.8)
# ---------------------------------------------------------------------------


# Validates: Requirements 6.6, 9.5 — quá thời gian chờ => error="timeout".
def test_extract_timeout_returns_error_timeout(recorder):
    recorder.goto_behavior = "timeout"
    with PlaywrightFallback() as pw:
        result = pw.extract(URL)

    assert result.ok is False
    assert result.error == "timeout"
    assert result.body == ""
    # Vẫn chỉ thử đúng một lần dù gặp timeout.
    assert len(recorder.goto_calls) == 1


# Validates: Requirements 6.8 — lỗi xử lý khác => ok=False kèm mô tả lỗi.
def test_extract_processing_error_returns_not_ok(recorder):
    recorder.goto_behavior = "error"
    with PlaywrightFallback() as pw:
        result = pw.extract(URL)

    assert result.ok is False
    assert result.error is not None
    assert result.error.startswith("playwright_error:")
    assert result.body == ""


# Validates: Requirements 6.6, 9.6 — lỗi không làm rò rỉ trình duyệt; vẫn đóng cuối.
def test_browser_closed_even_after_errors(recorder):
    recorder.goto_behavior = "error"
    with PlaywrightFallback() as pw:
        pw.extract(URL)
    assert recorder.browser_close_count == 1
    assert recorder.playwright_stop_count == 1


# ---------------------------------------------------------------------------
# Tắt tải hình ảnh (R6.5)
# ---------------------------------------------------------------------------


# Validates: Requirements 6.5 — vô hiệu hóa tải hình ảnh khi lấy nội dung.
def test_image_loading_disabled(recorder):
    with PlaywrightFallback() as pw:
        pw.extract(URL)

    # Có đăng ký route chặn (route cho mọi request).
    assert recorder.route_patterns, "phải đăng ký route để chặn tài nguyên"
    handler = recorder.image_route_handler
    assert handler is not None

    # Request ảnh bị abort; request khác được tiếp tục.
    image_route = _FakeRoute("image")
    handler(image_route)
    assert image_route.aborted is True
    assert image_route.continued is False

    doc_route = _FakeRoute("document")
    handler(doc_route)
    assert doc_route.aborted is False
    assert doc_route.continued is True


# ---------------------------------------------------------------------------
# Dùng ngoài context manager
# ---------------------------------------------------------------------------


# Validates: Requirements 6.8 — extract khi chưa khởi tạo trả lỗi an toàn, không raise.
def test_extract_without_context_returns_not_started():
    pw = PlaywrightFallback()
    result = pw.extract(URL)
    assert result.ok is False
    assert result.error == "not_started"
