"""Politeness helpers for the news crawler.

Cung cấp:
- ``RateLimiter``: giới hạn tần suất yêu cầu theo từng host (per-site), an toàn
  luồng, đảm bảo khoảng cách tối thiểu ``1 / per_second`` giữa hai yêu cầu liên
  tiếp tới cùng một host (R11.3, R11.4).
- ``get_user_agent``: lấy chuỗi User-Agent đã cấu hình, dùng UA mặc định của hệ
  thống khi cấu hình rỗng (R11.1, R11.2).
"""

from __future__ import annotations

import threading
import time
from typing import Callable

from app.core.config import settings

# UA mặc định của hệ thống, dùng khi settings.CRAWLER_USER_AGENT rỗng (R11.2).
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (compatible; quantyFin-ai-news-crawler/1.0; "
    "+https://github.com/quantyfin)"
)


def get_user_agent() -> str:
    """Trả về User-Agent cấu hình; rỗng → UA mặc định hệ thống (R11.1, R11.2)."""
    configured = (settings.CRAWLER_USER_AGENT or "").strip()
    return configured if configured else DEFAULT_USER_AGENT


class RateLimiter:
    """Giới hạn tần suất theo từng host (per-site), mặc định 1 req/s.

    An toàn luồng: dùng ``threading.Lock`` để bảo vệ bản đồ "thời điểm cho phép
    tiếp theo" theo host. ``acquire(host)`` chặn (sleep) cho tới khi được phép gửi
    yêu cầu tiếp theo tới host đó, nhưng không chặn các host khác.

    ``clock`` và ``sleep`` có thể inject để phục vụ kiểm thử với đồng hồ giả lập;
    mặc định dùng ``time.monotonic`` và ``time.sleep``.
    """

    def __init__(
        self,
        per_second: float = 1.0,
        *,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        if per_second <= 0:
            raise ValueError("per_second phải lớn hơn 0")
        self._interval = 1.0 / per_second
        self._clock = clock
        self._sleep = sleep
        self._lock = threading.Lock()
        # host -> thời điểm sớm nhất được phép gửi yêu cầu kế tiếp.
        self._next_allowed: dict[str, float] = {}

    def acquire(self, host: str) -> None:
        """Chặn cho tới khi được phép gửi yêu cầu tiếp theo tới ``host``."""
        with self._lock:
            now = self._clock()
            next_allowed = self._next_allowed.get(host, now)
            if next_allowed <= now:
                # Được phép gửi ngay; đặt mốc cho yêu cầu kế tiếp.
                wait = 0.0
                self._next_allowed[host] = now + self._interval
            else:
                # Phải chờ; đặt chỗ mốc kế tiếp ngay để các yêu cầu song song
                # tới cùng host xếp hàng đúng khoảng cách tối thiểu.
                wait = next_allowed - now
                self._next_allowed[host] = next_allowed + self._interval

        # Sleep ngoài lock để không chặn các host khác.
        if wait > 0:
            self._sleep(wait)
