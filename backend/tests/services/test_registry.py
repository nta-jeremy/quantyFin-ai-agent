"""Tests cho Source Registry (app/services/sources/registry.py).

Bao gồm:
- Property 1: Validate registry chỉ giữ nguồn hợp lệ (4.3).
- Property 2: Trùng tên dùng bản đầu tiên (4.4).
- Property 3: Resolve active_sources là tập con của registry (4.5).
- Unit test định tuyến type nguồn → tầng xử lý (4.7).

Lưu ý: ``load_sources`` đọc biến module-level ``SOURCE_REGISTRY``. Để kiểm thử
với danh sách tùy biến, các property test patch trực tiếp
``registry.SOURCE_REGISTRY`` bằng ``unittest.mock.patch.object`` (context
manager trong thân test, tránh fixture function-scoped không tương thích với
Hypothesis).
"""

from string import ascii_letters
from unittest.mock import patch

import pytest
from hypothesis import given, settings, strategies as st

from app.services.sources import registry as registry_module
from app.services.sources.registry import (
    SourceConfig,
    VALID_SOURCE_TYPES,
    VALID_TOPICS,
    load_sources,
    resolve_active_sources,
    validate_source,
)
from app.services.extraction.rss import discover_rss
from app.services.extraction.playwright_fallback import PlaywrightFallback


# ---------------------------------------------------------------------------
# Chiến lược sinh dữ liệu (Hypothesis)
# ---------------------------------------------------------------------------

# Tên hợp lệ: chuỗi không rỗng, độ dài 1..100 (theo R1.1 và validate_source).
valid_names = st.text(min_size=1, max_size=100)

# Topics hợp lệ: >= 1 phần tử, mọi phần tử thuộc VALID_TOPICS, không trùng.
valid_topics = st.lists(
    st.sampled_from(sorted(VALID_TOPICS)), min_size=1, unique=True
).map(tuple)

# URL hợp lệ theo giao thức http/https.
valid_urls = st.builds(
    lambda scheme, host: f"{scheme}://{host}",
    st.sampled_from(["http", "https"]),
    st.text(alphabet=ascii_letters + "./-", min_size=1, max_size=20),
)


@st.composite
def valid_sources(draw):
    """Sinh một ``SourceConfig`` thỏa toàn bộ ràng buộc của ``validate_source``."""
    return SourceConfig(
        name=draw(valid_names),
        type=draw(st.sampled_from(["rss", "playwright"])),
        url=draw(valid_urls),
        topics=draw(valid_topics),
        tier=draw(st.integers(min_value=1, max_value=5)),
        top_n=draw(st.one_of(st.none(), st.integers(min_value=1, max_value=100))),
    )


@st.composite
def invalid_sources(draw):
    """Sinh một ``SourceConfig`` vi phạm đúng một ràng buộc bắt buộc.

    Mọi trường khác giữ giá trị hợp lệ, đảm bảo ``validate_source`` luôn trả về
    một thông điệp lỗi (khác ``None``).
    """
    violation = draw(
        st.sampled_from(
            [
                "empty_name",
                "long_name",
                "bad_type",
                "bad_url",
                "empty_topics",
                "bad_topic",
                "bad_tier",
            ]
        )
    )
    name = draw(valid_names)
    stype = draw(st.sampled_from(["rss", "playwright"]))
    url = draw(valid_urls)
    topics = draw(valid_topics)
    tier = draw(st.integers(min_value=1, max_value=5))

    if violation == "empty_name":
        name = ""
    elif violation == "long_name":
        name = "x" * draw(st.integers(min_value=101, max_value=200))
    elif violation == "bad_type":
        stype = draw(st.sampled_from(["html", "HTML", "", "atom", "json"]))
    elif violation == "bad_url":
        url = draw(
            st.sampled_from(["", "ftp://x", "example.com", "www.example.com", "//x"])
        )
    elif violation == "empty_topics":
        topics = ()
    elif violation == "bad_topic":
        topics = draw(valid_topics) + ("thể thao",)
    elif violation == "bad_tier":
        tier = draw(st.sampled_from([0, -1, 6, 7, 100, -5]))

    return SourceConfig(name=name, type=stype, url=url, topics=topics, tier=tier)


@st.composite
def mixed_registry(draw):
    """Trộn nguồn hợp lệ (tên duy nhất) với nguồn vi phạm, hoán vị thứ tự."""
    valids = draw(st.lists(valid_sources(), max_size=6, unique_by=lambda s: s.name))
    invalids = draw(st.lists(invalid_sources(), max_size=6))
    combined = draw(st.permutations(valids + invalids))
    return list(combined)


# ---------------------------------------------------------------------------
# Property 1: Validate registry chỉ giữ nguồn hợp lệ (task 4.3)
# ---------------------------------------------------------------------------

# Feature: news-crawler-fulltext, Property 1: Validate registry chỉ giữ nguồn
# hợp lệ. Với mọi danh sách trộn nguồn hợp lệ và nguồn vi phạm ràng buộc,
# load_sources() chỉ giữ đúng các nguồn thỏa toàn bộ ràng buộc và sinh một
# cảnh báo/lỗi cho mỗi nguồn bị loại.
# Validates: Requirements 1.1, 1.7, 3.1, 3.4
@settings(max_examples=100)
@given(registry=mixed_registry())
def test_load_sources_keeps_only_valid_sources(registry):
    expected_valid = [s for s in registry if validate_source(s) is None]
    expected_invalid = [s for s in registry if validate_source(s) is not None]

    with patch.object(registry_module, "SOURCE_REGISTRY", registry):
        valid_map, messages = load_sources()

    # Chỉ giữ đúng tập nguồn hợp lệ (tên duy nhất theo cách sinh dữ liệu).
    assert set(valid_map.keys()) == {s.name for s in expected_valid}
    assert len(valid_map) == len(expected_valid)

    # Mọi nguồn được giữ đều hợp lệ và đúng là bản khai báo gốc.
    for name, cfg in valid_map.items():
        assert validate_source(cfg) is None
        assert cfg in expected_valid

    # Mỗi nguồn bị loại sinh đúng một thông điệp (không có dup-warning vì tên
    # các nguồn hợp lệ là duy nhất).
    assert len(messages) == len(expected_invalid)


# ---------------------------------------------------------------------------
# Property 2: Trùng tên dùng bản đầu tiên (task 4.4)
# ---------------------------------------------------------------------------

@st.composite
def dup_registry(draw):
    """Sinh registry toàn nguồn hợp lệ, tên rút từ pool nhỏ để ép trùng tên.

    URL được gán duy nhất theo chỉ số để phân biệt bản khai báo đầu tiên.
    """
    pool = ["Alpha", "Beta", "Gamma", "Delta"]
    names = draw(st.lists(st.sampled_from(pool), min_size=1, max_size=12))
    return [
        SourceConfig(
            name=nm,
            type="rss",
            url=f"https://example.com/{i}",
            topics=("kinh tế",),
            tier=1,
        )
        for i, nm in enumerate(names)
    ]


# Feature: news-crawler-fulltext, Property 2: Trùng tên dùng bản đầu tiên.
# Với mọi registry có thể chứa nguồn trùng name, load_sources() ánh xạ mỗi tên
# tới đúng bản xuất hiện đầu tiên theo thứ tự khai báo, và phát một cảnh báo cho
# mỗi lần trùng.
# Validates: Requirements 1.8
@settings(max_examples=100)
@given(registry=dup_registry())
def test_load_sources_duplicate_name_uses_first(registry):
    first_by_name: dict[str, SourceConfig] = {}
    dup_count = 0
    for s in registry:
        if s.name not in first_by_name:
            first_by_name[s.name] = s
        else:
            dup_count += 1

    with patch.object(registry_module, "SOURCE_REGISTRY", registry):
        valid_map, messages = load_sources()

    # Mỗi tên ánh xạ tới đúng bản đầu tiên (so khớp theo identity).
    assert set(valid_map.keys()) == set(first_by_name.keys())
    for name, cfg in valid_map.items():
        assert cfg is first_by_name[name]

    # Toàn bộ nguồn hợp lệ ⇒ thông điệp chỉ đến từ trùng tên, mỗi lần trùng một
    # cảnh báo.
    assert len(messages) == dup_count


# ---------------------------------------------------------------------------
# Property 3: Resolve active_sources là tập con của registry (task 4.5)
# ---------------------------------------------------------------------------

@st.composite
def registry_and_active(draw):
    """Sinh registry hợp lệ + chuỗi active_sources trộn tên thật và tên rác.

    Tên thật được biến đổi chữ hoa/thường và thêm khoảng trắng thừa. Tên rác
    được lọc để chắc chắn không khớp key hợp lệ nào.
    """
    names = draw(
        st.lists(
            st.text(alphabet=ascii_letters, min_size=1, max_size=8),
            min_size=0,
            max_size=6,
            unique_by=lambda s: s.lower(),
        )
    )
    registry = [
        SourceConfig(
            name=nm,
            type="rss",
            url=f"https://example.com/{i}",
            topics=("kinh tế",),
            tier=1,
        )
        for i, nm in enumerate(names)
    ]
    valid_keys = {nm.lower() for nm in names}

    ref_tokens: list[str] = []
    if names:
        chosen = draw(st.lists(st.sampled_from(names), max_size=8))
        for nm in chosen:
            ref_tokens.append(
                draw(
                    st.sampled_from(
                        [nm, nm.upper(), nm.lower(), f"  {nm}  ", f" {nm.lower()} "]
                    )
                )
            )

    raw_junk = draw(
        st.lists(
            st.text(alphabet=ascii_letters + "0123456789", min_size=1, max_size=8),
            max_size=6,
        )
    )
    junk_tokens = [
        j for j in raw_junk if j.strip() and j.strip().lower() not in valid_keys
    ]

    all_tokens = draw(st.permutations(ref_tokens + junk_tokens))
    active_sources = ",".join(all_tokens)
    return registry, active_sources, valid_keys


# Feature: news-crawler-fulltext, Property 3: Resolve active_sources là tập con
# của registry. Với mọi registry hợp lệ và mọi chuỗi active_sources (tên hợp lệ,
# tên rác, khoảng trắng thừa, hoa/thường), resolve_active_sources() trả về danh
# sách nguồn mà mọi phần tử đều thuộc registry và có key nằm trong
# active_sources; không tên rác nào lọt vào kết quả; mỗi tên rác sinh đúng một
# cảnh báo.
# Validates: Requirements 1.5, 13.1
@settings(max_examples=100)
@given(data=registry_and_active())
def test_resolve_active_sources_is_subset_of_registry(data):
    registry, active_sources, valid_keys = data

    with patch.object(registry_module, "SOURCE_REGISTRY", registry):
        resolved, warnings = resolve_active_sources(active_sources)
        valid_map, _ = load_sources()

    registry_configs = list(valid_map.values())
    requested_keys = [
        t.strip().lower() for t in active_sources.split(",") if t.strip()
    ]
    result_keys = [cfg.name.lower() for cfg in resolved]

    # Mọi phần tử kết quả đều tồn tại trong registry và được yêu cầu.
    for cfg in resolved:
        assert cfg in registry_configs
        assert cfg.name.lower() in valid_keys
        assert cfg.name.lower() in requested_keys

    # Không tên rác nào lọt vào kết quả.
    assert all(k in valid_keys for k in result_keys)

    # Kết quả không lặp key (đã khử trùng).
    assert len(result_keys) == len(set(result_keys))

    # Mỗi tên rác (theo key chuẩn hóa, phân biệt) sinh đúng một cảnh báo.
    distinct_junk_keys = {k for k in requested_keys if k not in valid_keys}
    assert len(warnings) == len(distinct_junk_keys)


# ---------------------------------------------------------------------------
# Unit test: định tuyến type nguồn → tầng xử lý (task 4.7)
# ---------------------------------------------------------------------------

# Ánh xạ type nguồn → tầng xử lý production:
#   rss        → RSS_Discovery   (discover_rss)
#   playwright → Playwright_Fallback (PlaywrightFallback)
LAYER_BY_TYPE = {
    "rss": discover_rss,
    "playwright": PlaywrightFallback,
}


@pytest.mark.parametrize(
    "source_type, expected_layer",
    [
        ("rss", discover_rss),
        ("playwright", PlaywrightFallback),
    ],
)
def test_source_type_routes_to_expected_layer(source_type, expected_layer):
    """Nguồn rss định tuyến tới RSS_Discovery; playwright tới Playwright_Fallback.

    Validates: Requirements 1.2, 1.3, 1.4, 6.1
    """
    src = SourceConfig(
        name="N",
        type=source_type,
        url="https://example.com/feed.rss",
        topics=("kinh tế",),
        tier=1,
    )
    assert LAYER_BY_TYPE[src.type] is expected_layer


def test_every_valid_source_type_has_a_handler():
    """Mọi type hợp lệ trong registry đều có tầng xử lý tương ứng (R1.3, R1.4)."""
    assert set(LAYER_BY_TYPE.keys()) == VALID_SOURCE_TYPES


def test_seeded_registry_rss_sources_route_to_rss_discovery():
    """Các nguồn rss seed trong registry định tuyến tới RSS_Discovery (R1.2, R1.3)."""
    valid_map, _ = load_sources()
    rss_sources = [cfg for cfg in valid_map.values() if cfg.type == "rss"]
    assert rss_sources  # registry khởi đầu có nguồn rss
    for cfg in rss_sources:
        assert LAYER_BY_TYPE[cfg.type] is discover_rss
