from sqlalchemy import inspect, text
from sqlmodel import Session, create_engine
from sqlalchemy.pool import StaticPool
from hypothesis import given, settings, strategies as st


# Bảng news_articles "cũ" (chưa có cột summary) để mô phỏng schema trước migration.
OLD_NEWS_ARTICLES_DDL = """
CREATE TABLE news_articles (
    id INTEGER PRIMARY KEY,
    title TEXT,
    content TEXT NOT NULL,
    url TEXT,
    source TEXT,
    status TEXT,
    published_at TIMESTAMP
)
"""


def _new_old_schema_engine(existing_contents):
    """Tạo engine SQLite in-memory với bảng news_articles cũ + vài bản ghi."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    with Session(engine) as session:
        session.execute(text(OLD_NEWS_ARTICLES_DDL))
        for idx, content in enumerate(existing_contents):
            session.execute(
                text(
                    "INSERT INTO news_articles (id, title, content, url, status) "
                    "VALUES (:id, :title, :content, :url, :status)"
                ),
                {
                    "id": idx + 1,
                    "title": f"title-{idx}",
                    "content": content,
                    "url": f"https://example.com/{idx}",
                    "status": "pending_entity_extraction",
                },
            )
        session.commit()
    return engine


def _apply_summary_migration(engine):
    """Áp dụng bước migration cột summary giống hệt init_db() trong app/main.py:
    chỉ ALTER TABLE ADD COLUMN summary TEXT khi cột chưa tồn tại."""
    inspector = inspect(engine)
    if "news_articles" in inspector.get_table_names():
        columns = [col["name"] for col in inspector.get_columns("news_articles")]
        if "summary" not in columns:
            with Session(engine) as session:
                try:
                    session.execute(
                        text("ALTER TABLE news_articles ADD COLUMN summary TEXT")
                    )
                    session.commit()
                except Exception:
                    session.rollback()
                    raise


def _summary_column_count(engine):
    inspector = inspect(engine)
    names = [col["name"] for col in inspector.get_columns("news_articles")]
    return names.count("summary")


# Feature: news-crawler-fulltext, Property 18: Migration cột summary là idempotent.
# Với mọi số lần áp dụng migration liên tiếp (>= 2) trên cùng một bảng
# news_articles, schema ổn định (cột summary tồn tại đúng một lần) và không phát
# sinh lỗi từ lần áp dụng thứ hai trở đi.
# Validates: Requirements 7.7
@settings(max_examples=100)
@given(
    apply_count=st.integers(min_value=2, max_value=6),
    existing_contents=st.lists(st.text(min_size=0, max_size=40), max_size=5),
)
def test_summary_migration_is_idempotent(apply_count, existing_contents):
    engine = _new_old_schema_engine(existing_contents)
    try:
        # Trước migration: cột summary chưa tồn tại.
        assert _summary_column_count(engine) == 0

        # Áp dụng migration nhiều lần liên tiếp; từ lần thứ 2 phải là no-op,
        # không được raise lỗi.
        for _ in range(apply_count):
            _apply_summary_migration(engine)

        # Sau N lần áp dụng: cột summary tồn tại đúng một lần (schema ổn định).
        assert _summary_column_count(engine) == 1

        # Dữ liệu cũ được bảo toàn: content giữ nguyên, summary = NULL.
        with Session(engine) as session:
            rows = session.execute(
                text("SELECT content, summary FROM news_articles ORDER BY id")
            ).all()
        assert [r[0] for r in rows] == existing_contents
        assert all(r[1] is None for r in rows)
    finally:
        engine.dispose()


# ---------------------------------------------------------------------------
# Unit test migration cột summary (Task 2.4)
# Requirements: 7.2 (thêm cột vào bảng cũ), 7.3 (giữ nguyên content bản ghi cũ),
# 7.4 (summary = NULL sau migration, cột nullable), 7.5 (rollback khi lỗi),
# 7.6 (log nguyên nhân khi lỗi).
# ---------------------------------------------------------------------------
import pytest
from unittest.mock import MagicMock, patch


def _run_summary_migration_logged(engine, logger):
    """Bản sao khối migration cột summary trong init_db() (app/main.py), kèm
    logging: thử ALTER + commit; nếu lỗi thì rollback toàn bộ, ghi log nguyên
    nhân rồi raise. Dùng để kiểm chứng hành vi rollback/log (R7.5, R7.6)."""
    inspector = inspect(engine)
    if "news_articles" in inspector.get_table_names():
        columns = [col["name"] for col in inspector.get_columns("news_articles")]
        if "summary" not in columns:
            with Session(engine) as session:
                try:
                    session.execute(
                        text("ALTER TABLE news_articles ADD COLUMN summary TEXT")
                    )
                    session.commit()
                except Exception as mig_err:
                    session.rollback()
                    logger.error(f"Migration news_articles thất bại: {str(mig_err)}")
                    raise


# R7.2: migration thêm cột summary vào bảng cũ chưa có cột này.
def test_migration_adds_summary_column_to_old_table():
    engine = _new_old_schema_engine(["body-a", "body-b"])
    try:
        assert _summary_column_count(engine) == 0
        _apply_summary_migration(engine)
        assert _summary_column_count(engine) == 1
    finally:
        engine.dispose()


# R7.3: migration giữ nguyên giá trị content của các bản ghi cũ.
def test_migration_preserves_existing_content():
    contents = ["nội dung cũ 1", "nội dung cũ 2", "nội dung cũ 3"]
    engine = _new_old_schema_engine(contents)
    try:
        _apply_summary_migration(engine)
        with Session(engine) as session:
            rows = session.execute(
                text("SELECT content FROM news_articles ORDER BY id")
            ).all()
        assert [r[0] for r in rows] == contents
    finally:
        engine.dispose()


# R7.4: sau migration, các bản ghi cũ mang summary = NULL.
def test_migration_old_rows_have_null_summary():
    engine = _new_old_schema_engine(["x", "y"])
    try:
        _apply_summary_migration(engine)
        with Session(engine) as session:
            summaries = session.execute(
                text("SELECT summary FROM news_articles ORDER BY id")
            ).all()
        assert all(s[0] is None for s in summaries)
    finally:
        engine.dispose()


# R7.4: cột summary cho phép giá trị NULL (nullable) — chèn bản ghi mới không
# cung cấp summary vẫn thành công và đọc lại là NULL.
def test_migration_summary_column_is_nullable():
    engine = _new_old_schema_engine(["seed"])
    try:
        _apply_summary_migration(engine)
        with Session(engine) as session:
            session.execute(
                text(
                    "INSERT INTO news_articles (id, title, content, url, status) "
                    "VALUES (99, 'new', 'new-body', 'https://example.com/99', 'pending_entity_extraction')"
                )
            )
            session.commit()
            value = session.execute(
                text("SELECT summary FROM news_articles WHERE id = 99")
            ).scalar_one()
        assert value is None
    finally:
        engine.dispose()


# R7.5 + R7.6: khi ALTER gặp lỗi, migration rollback toàn bộ (cột summary không
# được thêm, dữ liệu cũ giữ nguyên) và ghi log nêu nguyên nhân thất bại.
def test_migration_rolls_back_and_logs_on_error():
    contents = ["giữ nguyên 1", "giữ nguyên 2"]
    engine = _new_old_schema_engine(contents)
    mock_logger = MagicMock()
    try:
        with patch.object(
            Session,
            "execute",
            autospec=True,
            side_effect=RuntimeError("simulated DB failure"),
        ):
            with pytest.raises(RuntimeError):
                _run_summary_migration_logged(engine, mock_logger)

        # Đã ghi log nguyên nhân thất bại (R7.6).
        mock_logger.error.assert_called_once()
        logged_message = mock_logger.error.call_args.args[0]
        assert "simulated DB failure" in logged_message

        # Rollback: cột summary KHÔNG được thêm, dữ liệu cũ giữ nguyên (R7.5).
        assert _summary_column_count(engine) == 0
        with Session(engine) as session:
            rows = session.execute(
                text("SELECT content FROM news_articles ORDER BY id")
            ).all()
        assert [r[0] for r in rows] == contents
    finally:
        engine.dispose()
