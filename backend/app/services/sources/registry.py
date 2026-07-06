"""Cấu hình nguồn tin tập trung (Source Registry).

Khai báo các nguồn tin qua một danh sách `SourceConfig` thay vì hard-code từng
class scraper, cho phép thêm/sửa/xóa nguồn mà không đụng mã điều phối.
"""

from dataclasses import dataclass
from typing import Literal, Optional

SourceType = Literal["rss", "playwright"]

VALID_SOURCE_TYPES = {"rss", "playwright"}

VALID_TOPICS = {
    "kinh tế",
    "kinh doanh",
    "đầu tư",
    "chứng khoán",
    "xã hội",
    "chính trị",
}


@dataclass(frozen=True)
class SourceConfig:
    """Khai báo một nguồn tin.

    Attributes:
        name: Tên hiển thị duy nhất, độ dài 1..100 ký tự. Lưu vào `NewsArticle.source`.
        type: Loại nguồn, thuộc {"rss", "playwright"}.
        url: URL của nguồn, theo giao thức http hoặc https.
        topics: Danh sách chủ đề (>= 1), mỗi chủ đề thuộc `VALID_TOPICS`.
        tier: Tầng ưu tiên, số nguyên 1..5.
        top_n: Số bài top/hot cần lấy full body; None => dùng DEFAULT_TOP_N.
    """

    name: str
    type: SourceType
    url: str
    topics: tuple[str, ...]
    tier: int
    top_n: Optional[int] = None


# Tập nguồn khởi đầu theo bảng thiết kế.
# Lưu ý: CafeF dùng `https://cafef.vn/thi-truong-chung-khoan.rss` (KHÔNG có `/rss/`).
SOURCE_REGISTRY: list[SourceConfig] = [
    SourceConfig(
        name="CafeF",
        type="rss",
        url="https://cafef.vn/thi-truong-chung-khoan.rss",
        topics=("chứng khoán", "kinh tế"),
        tier=1,
    ),
    SourceConfig(
        name="TuoiTre",
        type="rss",
        url="https://tuoitre.vn/rss/kinh-doanh.rss",
        topics=("kinh doanh", "kinh tế"),
        tier=1,
    ),
    SourceConfig(
        name="ThanhNien",
        type="rss",
        url="https://thanhnien.vn/rss/kinh-te.rss",
        topics=("kinh tế", "kinh doanh"),
        tier=2,
    ),
    SourceConfig(
        name="VnBusiness",
        type="rss",
        url="https://vnbusiness.vn/rss/chung-khoan.rss",
        topics=("chứng khoán", "đầu tư"),
        tier=2,
    ),
    SourceConfig(
        name="VnExpressKinhDoanh",
        type="rss",
        url="https://vnexpress.net/rss/kinh-doanh.rss",
        topics=("kinh doanh", "kinh tế"),
        tier=1,
    ),
]


def validate_source(src: SourceConfig) -> Optional[str]:
    """Kiểm tra tính hợp lệ của một khai báo nguồn.

    Trả về None nếu nguồn hợp lệ, hoặc một chuỗi mô tả lỗi nếu vi phạm ràng buộc
    (R1.1, R1.7, R3.1, R3.4).

    Các ràng buộc:
    - name: chuỗi không rỗng, độ dài 1..100 ký tự.
    - type: thuộc {"rss", "playwright"}.
    - url: chuỗi không rỗng theo giao thức http/https.
    - topics: không rỗng và mọi phần tử thuộc VALID_TOPICS.
    - tier: số nguyên trong khoảng 1..5.
    """
    # name: bắt buộc, 1..100 ký tự
    if not src.name or not isinstance(src.name, str):
        return "name rỗng hoặc thiếu"
    if len(src.name) > 100:
        return f"name dài {len(src.name)} ký tự, vượt giới hạn 100"

    # type: thuộc tập hợp lệ
    if src.type not in VALID_SOURCE_TYPES:
        return f"type '{src.type}' không thuộc {sorted(VALID_SOURCE_TYPES)}"

    # url: bắt buộc, http/https
    if not src.url or not isinstance(src.url, str):
        return "url rỗng hoặc thiếu"
    if not (src.url.startswith("http://") or src.url.startswith("https://")):
        return f"url '{src.url}' không theo giao thức http/https"

    # topics: không rỗng, mọi phần tử hợp lệ
    if not src.topics:
        return "topics rỗng hoặc thiếu"
    invalid_topics = [t for t in src.topics if t not in VALID_TOPICS]
    if invalid_topics:
        return f"topics không hợp lệ: {invalid_topics}"

    # tier: số nguyên 1..5 (bool là subclass của int nên loại trừ rõ ràng)
    if not isinstance(src.tier, int) or isinstance(src.tier, bool):
        return "tier thiếu hoặc không phải số nguyên"
    if src.tier < 1 or src.tier > 5:
        return f"tier {src.tier} ngoài khoảng 1..5"

    return None


def _source_key(name: str) -> str:
    """Suy ra key khớp `active_sources` từ tên nguồn (chuẩn hóa lowercase, trim)."""
    return name.strip().lower()


def load_sources() -> tuple[dict[str, SourceConfig], list[str]]:
    """Nạp registry và lọc ra các nguồn hợp lệ.

    - Validate từng nguồn; nguồn lỗi bị loại, sinh một cảnh báo/lỗi cho mỗi
      nguồn bị loại (R1.7).
    - Trùng tên dùng bản khai báo xuất hiện đầu tiên, sinh một cảnh báo cho
      mỗi tên trùng (R1.8).

    Returns:
        Tuple gồm:
        - map name -> SourceConfig của các nguồn hợp lệ (giữ thứ tự khai báo).
        - danh sách thông điệp cảnh báo/lỗi.
    """
    valid: dict[str, SourceConfig] = {}
    messages: list[str] = []

    for src in SOURCE_REGISTRY:
        error = validate_source(src)
        if error is not None:
            messages.append(f"Bỏ qua nguồn '{src.name}': {error}")
            continue
        if src.name in valid:
            messages.append(
                f"Tên nguồn trùng '{src.name}': dùng bản khai báo đầu tiên, "
                "bỏ qua bản sau"
            )
            continue
        valid[src.name] = src

    return valid, messages


def resolve_active_sources(
    active_sources: str,
) -> tuple[list[SourceConfig], list[str]]:
    """Lọc registry hợp lệ theo chuỗi `active_sources` (R1.2, R1.5, R13.1).

    Chuỗi `active_sources` là danh sách tên nguồn phân tách bằng dấu phẩy. Mỗi
    token được chuẩn hóa (trim + lowercase) rồi khớp với key của các nguồn hợp
    lệ. Token không khớp nguồn nào sinh một cảnh báo và bị bỏ qua. Token trùng
    nhau chỉ được xử lý một lần.

    Returns:
        Tuple gồm:
        - danh sách SourceConfig cần chạy (giữ thứ tự xuất hiện trong chuỗi).
        - danh sách cảnh báo cho các tên nguồn không tồn tại.
    """
    valid_map, _ = load_sources()
    key_map = {_source_key(name): cfg for name, cfg in valid_map.items()}

    resolved: list[SourceConfig] = []
    warnings: list[str] = []
    seen_keys: set[str] = set()

    if not active_sources:
        return resolved, warnings

    for token in active_sources.split(","):
        key = token.strip().lower()
        if not key or key in seen_keys:
            continue
        seen_keys.add(key)

        cfg = key_map.get(key)
        if cfg is None:
            warnings.append(
                f"Nguồn '{token.strip()}' không tồn tại trong registry, bỏ qua"
            )
            continue
        resolved.append(cfg)

    return resolved, warnings


def supported_sources_map() -> dict[str, str]:
    """Suy ra map key -> tên hiển thị từ các nguồn hợp lệ trong registry (R1).

    Dùng cho `SUPPORTED_SOURCES_MAP` ở `settings.py`. Key là tên nguồn đã chuẩn
    hóa (lowercase, trim), value là tên hiển thị gốc.
    """
    valid_map, _ = load_sources()
    return {_source_key(cfg.name): cfg.name for cfg in valid_map.values()}
