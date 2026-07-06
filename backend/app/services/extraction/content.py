"""Content Extractor: tải trang bài viết qua HTTP tĩnh và trích xuất full body.

Tầng 2 của pipeline thu thập tin tức. Dùng ``httpx.Client`` đồng bộ để tải trang
và ``trafilatura`` để trích xuất thân bài. Hàm không raise ra ngoài: mọi lỗi tải
trang được chuyển thành ``ExtractionResult`` với ``ok=False`` và lý do thất bại.
"""

from dataclasses import dataclass
from typing import Optional

import httpx
import trafilatura

from app.core.config import settings


@dataclass
class ExtractionResult:
    ok: bool
    body: str = ""                 # full body trích xuất được
    error: Optional[str] = None    # lý do thất bại (http_<code> / timeout / network)
    http_status: Optional[int] = None
    needs_fallback: bool = False   # True nếu body < MIN_CONTENT_LENGTH (R5.6)


def extract_full_content(url: str, client: httpx.Client) -> ExtractionResult:
    """Tải trang bài viết qua HTTP tĩnh và trích xuất full body bằng trafilatura.

    - HTTP >= 400 => ok=False, error="http_<code>", http_status set, không ghi đè (R5.4).
    - Timeout => ok=False, error="timeout"; lỗi mạng khác => error="network" (R5.5, R11.5).
    - Trích xuất thành công => ok=True; needs_fallback=True khi
      len(body) < MIN_CONTENT_LENGTH (R5.6).
    """
    try:
        response = client.get(url, timeout=settings.FETCH_TIMEOUT)
    except httpx.TimeoutException:
        return ExtractionResult(ok=False, error="timeout")
    except httpx.RequestError:
        return ExtractionResult(ok=False, error="network")

    if response.status_code >= 400:
        return ExtractionResult(
            ok=False,
            error=f"http_{response.status_code}",
            http_status=response.status_code,
        )

    body = trafilatura.extract(response.text) or ""
    return ExtractionResult(
        ok=True,
        body=body,
        http_status=response.status_code,
        needs_fallback=len(body) < settings.MIN_CONTENT_LENGTH,
    )
