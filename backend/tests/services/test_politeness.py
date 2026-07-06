"""Test cho module Politeness của news crawler (R11).

Bao gồm:
- Property 19: ``RateLimiter`` đảm bảo khoảng cách tối thiểu giữa hai yêu cầu
  liên tiếp tới cùng một host (kiểm bằng đồng hồ giả lập, không sleep thật).
- Unit test ``get_user_agent``: có cấu hình → dùng UA cấu hình; rỗng → dùng UA
  mặc định của hệ thống.
"""

from hypothesis import given, settings as hp_settings, strategies as st

from app.core.config import settings
from app.services.extraction.politeness import (
    DEFAULT_USER_AGENT,
    RateLimiter,
    get_user_agent,
)


class FakeClock:
    """Đồng hồ giả lập: ``sleep`` chỉ tua thời gian thay vì chờ thật.

    Cho phép kiểm thử rate limit tức thời mà vẫn phản ánh trung thực dòng thời
    gian mà ``RateLimiter`` quan sát qua ``clock``/``sleep`` được inject.
    """

    def __init__(self) -> None:
        self.now = 0.0

    def time(self) -> float:
        return self.now

    def sleep(self, duration: float) -> None:
        if duration > 0:
            self.now += duration

    def advance(self, duration: float) -> None:
        if duration > 0:
            self.now += duration


# Tập host dùng để kiểm tính per-site (mỗi host có hạn mức độc lập).
HOSTS = ["host-a.example", "host-b.example", "host-c.example"]


# Feature: news-crawler-fulltext, Property 19: Rate limit per-site đảm bảo
# khoảng cách tối thiểu. Với mọi dãy yêu cầu tới cùng một host qua
# RateLimiter.acquire(host) với cấu hình per_second, khoảng cách thời gian giữa
# hai yêu cầu liên tiếp tới cùng host luôn >= 1 / per_second (đồng hồ giả lập).
# Validates: Requirements 11.3, 11.4
@hp_settings(max_examples=100)
@given(
    per_second=st.floats(
        min_value=0.1, max_value=10, allow_nan=False, allow_infinity=False
    ),
    events=st.lists(
        st.tuples(
            st.sampled_from(HOSTS),
            # Khoảng thời gian "thế giới thực" trôi qua trước mỗi yêu cầu, mô
            # phỏng việc các yêu cầu đến tại các thời điểm tùy ý.
            st.floats(
                min_value=0, max_value=5, allow_nan=False, allow_infinity=False
            ),
        ),
        min_size=1,
        max_size=30,
    ),
)
def test_rate_limit_min_spacing_per_host(per_second, events):
    clock = FakeClock()
    limiter = RateLimiter(per_second, clock=clock.time, sleep=clock.sleep)
    interval = 1.0 / per_second

    last_send: dict[str, float] = {}
    for host, gap in events:
        # Thời gian trôi qua trước khi yêu cầu kế tiếp được phát.
        clock.advance(gap)
        limiter.acquire(host)
        # Thời điểm yêu cầu thực sự được phép gửi (sau khi acquire trả về).
        send_time = clock.time()

        if host in last_send:
            # Khoảng cách giữa 2 yêu cầu liên tiếp cùng host >= interval.
            # Nới epsilon nhỏ để bỏ qua sai số dấu phẩy động.
            assert send_time - last_send[host] >= interval - 1e-9

        last_send[host] = send_time


def test_rate_limit_different_hosts_independent():
    """Yêu cầu tới các host khác nhau không bị trì hoãn lẫn nhau (per-site)."""
    clock = FakeClock()
    limiter = RateLimiter(1.0, clock=clock.time, sleep=clock.sleep)

    start = clock.time()
    limiter.acquire("host-a.example")
    limiter.acquire("host-b.example")
    limiter.acquire("host-c.example")

    # 3 host khác nhau, mỗi host yêu cầu lần đầu => không phải chờ.
    assert clock.time() == start


def test_user_agent_uses_configured_value(monkeypatch):
    """Có cấu hình User-Agent → dùng đúng UA đã cấu hình (R11.1)."""
    monkeypatch.setattr(settings, "CRAWLER_USER_AGENT", "MyCustomCrawler/2.0")
    assert get_user_agent() == "MyCustomCrawler/2.0"


def test_user_agent_falls_back_to_default_when_empty(monkeypatch):
    """UA cấu hình rỗng → dùng UA mặc định của hệ thống (R11.2)."""
    monkeypatch.setattr(settings, "CRAWLER_USER_AGENT", "")
    assert get_user_agent() == DEFAULT_USER_AGENT


def test_user_agent_falls_back_to_default_when_whitespace(monkeypatch):
    """UA cấu hình chỉ có khoảng trắng → coi như rỗng → UA mặc định (R11.2)."""
    monkeypatch.setattr(settings, "CRAWLER_USER_AGENT", "   ")
    assert get_user_agent() == DEFAULT_USER_AGENT
