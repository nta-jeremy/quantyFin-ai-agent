"""Property test cho khâu chọn lọc của orchestrator: app.services.crawler.

Gồm:
- Property 7: Chọn Top-N là tiền tố và bị chặn bởi min(top_n, len) (Hypothesis).
- Property 10: Dedup loại URL đã tồn tại, giữ URL mới theo thứ tự (Hypothesis + DB).

Lưu ý về Hypothesis + DB: fixture ``session`` của conftest là function-scoped
nên sẽ bị tái dùng giữa các example của cùng một hàm ``@given`` (gây rò rỉ
trạng thái giữa các example). Vì vậy Property 10 tự dựng một engine/session
SQLite in-memory MỚI trong thân test cho mỗi example để đảm bảo mỗi example
chạy trên DB sạch.
"""

import datetime as dt

from hypothesis import given, settings as hyp_settings, strategies as st
from sqlmodel import SQLModel, Session, create_engine
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.models.news import NewsArticle
from app.services.crawler import select_top_n, filter_new_urls
from app.services.extraction.rss import ArticleStub


_FIXED_PUBLISHED_AT = dt.datetime(2024, 1, 1, 0, 0, 0)


def _make_stub(title: str, url: str, teaser: str = "") -> ArticleStub:
    """Tạo một ArticleStub tối giản cho test."""
    return ArticleStub(
        title=title,
        url=url,
        teaser=teaser,
        published_at=_FIXED_PUBLISHED_AT,
        source="TestSource",
    )


# Từ an toàn cho title/teaser.
_word = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
    min_size=1,
    max_size=12,
)

# URL lấy từ một dải số nhỏ để các tập (đã tồn tại / mới) có khả năng giao nhau.
_url = st.builds(lambda n: f"https://example.com/{n}", st.integers(min_value=0, max_value=20))

# Một stub bất kỳ (url có thể trùng nhau giữa các stub).
_stub = st.builds(_make_stub, _word, _url, _word)


# ---------------------------------------------------------------------------
# Property 7: Chọn Top-N là tiền tố và bị chặn bởi min(top_n, len)
# ---------------------------------------------------------------------------

# Feature: news-crawler-fulltext, Property 7: Chọn Top-N là tiền tố và bị chặn
# bởi min(top_n, len).
# Với mọi danh sách stub và với mọi giá trị top_n (kể cả top_n=None thì dùng
# settings.DEFAULT_TOP_N), select_top_n() trả về đúng min(top_n_hiệu_dụng,
# len(stubs)) phần tử và kết quả là tiền tố của danh sách đầu vào (giữ thứ hạng
# theo thứ tự feed).
# Validates: Requirements 3.2, 3.3, 3.7
@hyp_settings(max_examples=100)
@given(
    stubs=st.lists(_stub, min_size=0, max_size=130),
    top_n=st.one_of(st.none(), st.integers(min_value=0, max_value=150)),
)
def test_property_7_select_top_n_is_bounded_prefix(stubs, top_n):
    result = select_top_n(stubs, top_n)

    effective_top_n = settings.DEFAULT_TOP_N if top_n is None else top_n
    expected_count = min(effective_top_n, len(stubs))

    # Đúng min(top_n_hiệu_dụng, len) phần tử.
    assert len(result) == expected_count
    # Kết quả là tiền tố của danh sách đầu vào (giữ nguyên thứ tự feed).
    assert result == stubs[:expected_count]


# ---------------------------------------------------------------------------
# Property 10: Dedup loại URL đã tồn tại, giữ URL mới theo thứ tự
# ---------------------------------------------------------------------------


def _seeded_engine(existing_urls):
    """Tạo engine SQLite in-memory MỚI với bảng news_articles + seed các url đã
    tồn tại. Mỗi example gọi hàm này để có DB sạch (tránh rò rỉ trạng thái giữa
    các example của Hypothesis)."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        for idx, url in enumerate(existing_urls):
            session.add(
                NewsArticle(
                    title=f"existing-{idx}",
                    content="seed-body",
                    url=url,
                    source="Seed",
                    published_at=_FIXED_PUBLISHED_AT,
                )
            )
        session.commit()
    return engine


# Feature: news-crawler-fulltext, Property 10: Dedup loại URL đã tồn tại, giữ
# URL mới theo thứ tự.
# Với mọi tập URL đã có trong DB và với mọi danh sách stub, filter_new_urls()
# trả về đúng các stub có url không thuộc tập đã tồn tại, giữ nguyên thứ tự
# tương đối, và giao của kết quả với tập URL đã tồn tại là rỗng.
# Validates: Requirements 4.3, 4.4, 4.5
@hyp_settings(max_examples=100)
@given(
    # st.sets đảm bảo url đã tồn tại là duy nhất (cột url là unique trong DB).
    existing_urls=st.sets(_url, max_size=21),
    stubs=st.lists(_stub, min_size=0, max_size=30),
)
def test_property_10_filter_new_urls_keeps_new_in_order(existing_urls, stubs):
    existing_list = list(existing_urls)
    engine = _seeded_engine(existing_list)
    try:
        with Session(engine) as session:
            result = filter_new_urls(session, stubs)
    finally:
        engine.dispose()

    existing_set = set(existing_list)

    # Kết quả đúng bằng các stub có url chưa tồn tại, giữ nguyên thứ tự tương đối.
    expected = [stub for stub in stubs if stub.url not in existing_set]
    assert result == expected

    # Giao của kết quả với tập URL đã tồn tại là rỗng.
    assert all(stub.url not in existing_set for stub in result)
