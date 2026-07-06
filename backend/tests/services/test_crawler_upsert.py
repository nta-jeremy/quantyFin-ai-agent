"""Property tests cho ``upsert_news_articles`` (app/services/crawler.py).

Bao gồm:
- Property 13: Upsert idempotent theo URL nguyên văn (task 11.7).
- Property 14: Lưu summary round-trip và giới hạn độ dài (task 11.8).
- Property 15: Bài mới lưu mang trạng thái pending (task 11.9).

Lưu ý thiết kế kiểm thử:
- ``upsert_news_articles`` KHÔNG tự commit (để caller giữ ranh giới giao dịch).
  Vì vậy trong test ta gọi ``session.commit()`` trước khi đọc lại để xác minh
  dữ liệu đã lưu.
- Mỗi ví dụ Hypothesis dùng một engine SQLite in-memory sạch (tạo trong thân
  test, không dùng fixture function-scoped). Tránh tái dùng session/DB giữa các
  ví dụ — cùng cách làm với ``test_migration.py``.
"""

import datetime as dt

from hypothesis import given, settings, strategies as st
from sqlmodel import SQLModel, Session, create_engine, select
from sqlalchemy.pool import StaticPool

from app.models.news import NewsArticle
from app.services.crawler import upsert_news_articles, SUMMARY_MAX_LENGTH


# Thời điểm cố định cho published_at (không liên quan tới property đang kiểm).
NOW = dt.datetime(2024, 1, 1, 0, 0, 0)

# Văn bản an toàn để lưu vào cột TEXT của SQLite: loại surrogate (Cs), control
# chars (Cc) và NUL để tránh lỗi mã hóa khi round-trip.
SAFE_CHARS = st.characters(blacklist_categories=("Cs", "Cc"), blacklist_characters="\x00")


def safe_text(min_size=0, max_size=200):
    return st.text(alphabet=SAFE_CHARS, min_size=min_size, max_size=max_size)


def _new_engine():
    """Tạo engine SQLite in-memory sạch kèm toàn bộ bảng cho một ví dụ."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return engine


# ---------------------------------------------------------------------------
# Property 13: Upsert idempotent theo URL nguyên văn (task 11.7)
# ---------------------------------------------------------------------------

# Pool URL nhỏ để ép trùng lặp; biến thể chữ HOA ở ký tự cuối tạo chuỗi KHÁC
# nhưng chỉ khác hoa/thường (kiểm tra so khớp nguyên văn, phân biệt hoa/thường).
URL_POOL = [
    "https://example.com/a",
    "https://example.com/b",
    "https://example.com/c",
    "https://example.com/d",
]
URL_CASE_VARIANTS = [u[:-1] + u[-1].upper() for u in URL_POOL]

# Sentinel: bài thiếu hẳn khóa "url".
_MISSING = "__MISSING__"

url_choices = st.sampled_from(URL_POOL + URL_CASE_VARIANTS + ["", None, _MISSING])


def _build_article(index, url_choice):
    """Dựng một bài với marker theo chỉ số để xác định bài "xuất hiện đầu tiên"."""
    art = {
        "title": f"title-{index}",
        "content": f"content-{index}",
        "published_at": NOW,
        "source": "src",
    }
    if url_choice == _MISSING:
        return art  # thiếu hẳn khóa url
    if url_choice is None:
        art["url"] = None
    else:
        art["url"] = url_choice
    return art


# Feature: news-crawler-fulltext, Property 13: Upsert idempotent theo URL nguyên
# văn. Với mọi tập bài viết: mỗi url xuất hiện đúng một lần trong DB; bài có url
# rỗng/thiếu bị loại; trùng url chỉ giữ bài xuất hiện đầu tiên; url khác nhau ở
# chữ hoa/thường được coi là khác nhau (không chuẩn hóa). Gọi lại với cùng tập
# không tạo bản ghi mới và không ghi đè (lần hai saved=0, số bản ghi không đổi).
# Validates: Requirements 12.1, 12.2, 12.3, 12.4
@settings(max_examples=100, deadline=None)
@given(choices=st.lists(url_choices, min_size=0, max_size=12))
def test_upsert_is_idempotent_by_verbatim_url(choices):
    articles = [_build_article(i, c) for i, c in enumerate(choices)]

    # Kỳ vọng: url -> chỉ số bài xuất hiện đầu tiên (bỏ url rỗng/thiếu).
    first_index_by_url: dict[str, int] = {}
    for i, art in enumerate(articles):
        url = art.get("url")
        if not url:
            continue
        if url not in first_index_by_url:
            first_index_by_url[url] = i

    engine = _new_engine()
    try:
        with Session(engine) as session:
            saved1 = upsert_news_articles(session, articles)
            session.commit()
            rows = session.exec(select(NewsArticle)).all()

            # Mỗi url xuất hiện đúng một lần; bỏ url rỗng/thiếu (R12.1, R12.4).
            assert saved1 == len(first_index_by_url)
            assert {r.url for r in rows} == set(first_index_by_url.keys())
            assert len(rows) == len(first_index_by_url)

            # Trùng url giữ bài đầu tiên; biến thể hoa/thường là url khác nhau
            # (R12.3, R12.1).
            for r in rows:
                expected_idx = first_index_by_url[r.url]
                assert r.content == f"content-{expected_idx}"
                assert r.title == f"title-{expected_idx}"

            # Gọi lại lần 2 cùng tập: không tạo bản ghi mới, không ghi đè
            # (R12.2).
            saved2 = upsert_news_articles(session, articles)
            session.commit()
            rows2 = session.exec(select(NewsArticle)).all()

            assert saved2 == 0
            assert len(rows2) == len(rows)
            for r in rows2:
                expected_idx = first_index_by_url[r.url]
                assert r.content == f"content-{expected_idx}"
    finally:
        engine.dispose()


# ---------------------------------------------------------------------------
# Property 14: Lưu summary round-trip và giới hạn độ dài (task 11.8)
# ---------------------------------------------------------------------------

# Teaser: trộn chuỗi ngắn và chuỗi dài vượt ngưỡng 5.000 ký tự để kiểm cắt.
teaser_strategy = st.one_of(
    safe_text(0, 200),
    st.builds(
        lambda ch, n: ch * n,
        st.sampled_from(["a", "á", "中", "x", "ñ"]),
        st.integers(min_value=SUMMARY_MAX_LENGTH - 10, max_value=SUMMARY_MAX_LENGTH + 100),
    ),
)


# Feature: news-crawler-fulltext, Property 14: Lưu summary round-trip và giới
# hạn độ dài. Với mọi bài có teaser, sau khi lưu rồi đọc lại, summary bằng
# teaser đã cắt còn tối đa 5.000 ký tự và độc lập với content; độ dài summary
# lưu trữ luôn ≤ 5.000.
# Validates: Requirements 5.3, 7.1
@settings(max_examples=100, deadline=None)
@given(pairs=st.lists(st.tuples(teaser_strategy, safe_text(0, 300)), min_size=0, max_size=6))
def test_summary_round_trip_and_length_limit(pairs):
    articles = [
        {
            "title": f"t-{i}",
            "content": f"body-{i}-{body}",  # content độc lập với teaser
            "summary": teaser,
            "url": f"https://example.com/{i}",
            "published_at": NOW,
            "source": "src",
        }
        for i, (teaser, body) in enumerate(pairs)
    ]

    engine = _new_engine()
    try:
        with Session(engine) as session:
            upsert_news_articles(session, articles)
            session.commit()
            rows = session.exec(select(NewsArticle)).all()

        by_url = {r.url: r for r in rows}
        assert len(by_url) == len(articles)

        for i, (teaser, body) in enumerate(pairs):
            r = by_url[f"https://example.com/{i}"]
            # summary = teaser đã cắt ≤ 5.000 ký tự (R5.3, R7.1).
            assert r.summary == teaser[:SUMMARY_MAX_LENGTH]
            assert len(r.summary) <= SUMMARY_MAX_LENGTH
            # summary độc lập với content.
            assert r.content == f"body-{i}-{body}"
    finally:
        engine.dispose()


# ---------------------------------------------------------------------------
# Property 15: Bài mới lưu mang trạng thái pending (task 11.9)
# ---------------------------------------------------------------------------

# Feature: news-crawler-fulltext, Property 15: Bài mới lưu mang trạng thái
# pending. Với mọi bài mới được lưu qua upsert_news_articles() mà không chỉ định
# status, bản ghi nhận status = "pending_entity_extraction".
# Validates: Requirements 13.3
@settings(max_examples=100, deadline=None)
@given(count=st.integers(min_value=0, max_value=8))
def test_new_articles_get_pending_status(count):
    # Không chỉ định status (bỏ hẳn khóa "status").
    articles = [
        {
            "title": f"t-{i}",
            "content": f"body-{i}",
            "url": f"https://example.com/{i}",
            "published_at": NOW,
            "source": "src",
        }
        for i in range(count)
    ]

    engine = _new_engine()
    try:
        with Session(engine) as session:
            upsert_news_articles(session, articles)
            session.commit()
            rows = session.exec(select(NewsArticle)).all()

        assert len(rows) == count
        for r in rows:
            assert r.status == "pending_entity_extraction"
    finally:
        engine.dispose()
