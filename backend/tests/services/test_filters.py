"""Property tests cho bộ lọc hai giai đoạn (R4).

Hai property kiểm chứng rằng khi orchestrator dùng ``pre_filter`` và
``full_content_filter`` làm bước chọn lọc, tập bài đi tiếp luôn là tập con
của các bài thỏa predicate tương ứng, và không bài nào bị loại lại lọt qua.

- Property 8: ``pre_filter(title, teaser)`` quyết định bài nào được tải full body.
- Property 9: ``full_content_filter(title, body)`` quyết định bài nào được lưu.

Cả hai bộ lọc tái sử dụng ``zero_cost_filter`` (ticker + financial keyword), nên
generator được dựng để sinh hỗn hợp bài đạt và không đạt một cách tự nhiên.
"""

from hypothesis import given, settings, strategies as st

from app.services.extraction.filters import pre_filter, full_content_filter

# Tập ticker mẫu dùng cho cả văn bản và danh sách ticker hoạt động.
TICKER_POOL = ["VIC", "VNM", "FPT", "HPG", "VCB", "MWG", "SSI"]

# Một vài financial keyword theo đúng danh sách trong ``zero_cost_filter``.
FINANCIAL_KEYWORDS = [
    "chứng khoán",
    "cổ phiếu",
    "lợi nhuận",
    "thị trường",
    "đầu tư",
    "giao dịch",
]

# Từ nhiễu không phải ticker cũng không phải keyword tài chính.
NOISE_WORDS = ["hôm", "nay", "thời", "tiết", "bóng", "đá", "ABC", "xyz", "tin"]

# Token có thể xuất hiện trong văn bản: trộn ticker, keyword và nhiễu để
# sinh ra cả bài đạt lẫn không đạt bộ lọc.
TEXT_TOKENS = TICKER_POOL + FINANCIAL_KEYWORDS + NOISE_WORDS


# Văn bản (title/teaser/body) ghép từ 0..8 token ngẫu nhiên.
text_strategy = st.builds(
    lambda parts: " ".join(parts),
    st.lists(st.sampled_from(TEXT_TOKENS), min_size=0, max_size=8),
)

# Danh sách ticker hoạt động: có thể rỗng (mọi bài bị loại) hoặc gồm các
# ticker trong pool; bao phủ cả trường hợp ticker không khớp văn bản.
active_tickers_strategy = st.lists(
    st.sampled_from(TICKER_POOL), min_size=0, max_size=5, unique=True
)

# Một "bài" cho pre_filter: title + teaser.
pre_item_strategy = st.fixed_dictionaries(
    {"title": text_strategy, "teaser": text_strategy}
)

# Một "bài" cho full_content_filter: title + body.
full_item_strategy = st.fixed_dictionaries(
    {"title": text_strategy, "body": text_strategy}
)


# Feature: news-crawler-fulltext, Property 8: Pre_Filter loại bài không thỏa
# tiêu chí. Với mọi danh sách stub và tập ticker hoạt động, tập bài được đưa
# vào bước tải full body là tập con của các stub thỏa pre_filter(title, teaser);
# không stub nào có pre_filter=False lọt vào bước tải.
# Validates: Requirements 4.1, 4.2
@settings(max_examples=100)
@given(
    items=st.lists(pre_item_strategy, min_size=0, max_size=12),
    active_tickers=active_tickers_strategy,
)
def test_pre_filter_excludes_non_matching(items, active_tickers):
    # Bước chọn lọc của orchestrator: chỉ giữ bài đạt pre_filter.
    selected_indices = [
        i
        for i, it in enumerate(items)
        if pre_filter(it["title"], it["teaser"], active_tickers)
    ]

    # 1. Mọi bài được chọn đều thỏa pre_filter (không có False lọt qua) (R4.2).
    for i in selected_indices:
        assert pre_filter(items[i]["title"], items[i]["teaser"], active_tickers)

    # 2. Tập được chọn là tập con của danh sách đầu vào (theo chỉ số).
    assert set(selected_indices).issubset(set(range(len(items))))

    # 3. Completeness: mọi bài thỏa pre_filter đều được giữ lại (R4.1).
    expected_indices = [
        i
        for i, it in enumerate(items)
        if pre_filter(it["title"], it["teaser"], active_tickers)
    ]
    assert selected_indices == expected_indices

    # 4. Không bài nào pre_filter=False nằm trong tập được chọn.
    for i in range(len(items)):
        if not pre_filter(items[i]["title"], items[i]["teaser"], active_tickers):
            assert i not in selected_indices


# Feature: news-crawler-fulltext, Property 9: Full_Content_Filter chặn trước
# khi lưu. Với mọi danh sách bài đã có full body và tập ticker hoạt động, tập
# bài được đưa vào bước lưu là tập con của các bài thỏa full_content_filter(
# title, body); không bài nào có full_content_filter=False được lưu.
# Validates: Requirements 4.7, 4.8
@settings(max_examples=100)
@given(
    items=st.lists(full_item_strategy, min_size=0, max_size=12),
    active_tickers=active_tickers_strategy,
)
def test_full_content_filter_blocks_before_save(items, active_tickers):
    # Bước chọn lọc trước khi lưu: chỉ giữ bài đạt full_content_filter.
    to_save_indices = [
        i
        for i, it in enumerate(items)
        if full_content_filter(it["title"], it["body"], active_tickers)
    ]

    # 1. Mọi bài được lưu đều thỏa full_content_filter (R4.8).
    for i in to_save_indices:
        assert full_content_filter(items[i]["title"], items[i]["body"], active_tickers)

    # 2. Tập được lưu là tập con của danh sách đầu vào (theo chỉ số).
    assert set(to_save_indices).issubset(set(range(len(items))))

    # 3. Completeness: mọi bài thỏa full_content_filter đều được giữ lại (R4.7).
    expected_indices = [
        i
        for i, it in enumerate(items)
        if full_content_filter(it["title"], it["body"], active_tickers)
    ]
    assert to_save_indices == expected_indices

    # 4. Không bài nào full_content_filter=False được đưa vào bước lưu.
    for i in range(len(items)):
        if not full_content_filter(items[i]["title"], items[i]["body"], active_tickers):
            assert i not in to_save_indices
