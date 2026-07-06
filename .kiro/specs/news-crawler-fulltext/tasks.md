# Implementation Plan: news-crawler-fulltext

## Overview

Kế hoạch chuyển thiết kế kiến trúc 3 tầng (RSS Discovery → Content Extractor → Playwright Fallback) thành các bước coding tăng dần trên codebase hiện có (FastAPI + Python 3.11, `httpx.Client` đồng bộ, SQLModel, migration thủ công idempotent trong `init_db`, test SQLite in-memory qua `conftest.py`).

Nguyên tắc xuyên suốt:

- Giữ tương thích ngược tuyệt đối: không đổi chữ ký `ingest_news_articles(session, active_sources)` và `upsert_news_articles(session, articles)`; giữ nguyên các trường phản hồi hiện có của `/ingest`, chỉ bổ sung `sourceHealth`.
- Pipeline chạy đồng bộ trong thread; song song HTTP bằng `ThreadPoolExecutor(max_workers=FETCH_CONCURRENCY_LIMIT)`; Playwright sync tuần tự, 1 browser, tắt ảnh, đóng cuối lần chạy.
- Migration cột `summary` idempotent trong `init_db()` (KHÔNG dùng Alembic).
- Registry là Python module (`SOURCE_REGISTRY: list[SourceConfig]`).
- Property-based testing dùng **Hypothesis** (thêm vào dev deps), mỗi property test `@settings(max_examples=100)` và gắn comment `# Feature: news-crawler-fulltext, Property N: ...`.
- Test dùng SQLite in-memory; mock `httpx` cho discovery/extractor; mock hoặc `@pytest.mark.skipif` cho Playwright khi chưa cài chromium.

Ngôn ngữ triển khai: **Python** (theo thiết kế, không dùng pseudocode).

## Tasks

- [x] 1. Thêm dependencies cho tính năng
  - [x] 1.1 Khai báo phụ thuộc runtime và dev trong `pyproject.toml`
    - Thêm `trafilatura` và `playwright` vào `[project].dependencies`
    - Thêm `hypothesis` vào `[dependency-groups].dev`
    - Ghi chú trong README/comment phần dev rằng cần chạy `playwright install chromium` một lần sau khi cài
    - _Requirements: 5.1, 6.1_

- [x] 2. Mở rộng schema NewsArticle và migration cột `summary`
  - [x] 2.1 Thêm cột `summary` vào model `NewsArticle`
    - Thêm `summary: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))` trong `app/models/news.py`, giữ nguyên các cột khác
    - _Requirements: 7.1, 7.4_
  - [x] 2.2 Thêm bước migration idempotent cột `summary` trong `init_db()`
    - Trong `app/main.py`, bổ sung `summary` vào danh sách cột kiểm tra; chỉ `ALTER TABLE news_articles ADD COLUMN summary TEXT` khi cột chưa tồn tại
    - Bọc trong try/except: rollback toàn bộ và `raise` kèm thông báo nguyên nhân khi lỗi; không đụng cột `content`
    - _Requirements: 7.2, 7.3, 7.5, 7.6, 7.7_
  - [x] 2.3 Viết property test migration idempotent (SQLite)
    - **Property 18: Migration cột summary là idempotent**
    - **Validates: Requirements 7.7**
  - [x] 2.4 Viết unit test migration
    - Thêm cột vào bảng cũ; giữ nguyên `content` của bản ghi cũ; `summary` = NULL sau migration; rollback và log nguyên nhân khi lỗi
    - _Requirements: 7.2, 7.3, 7.4, 7.5, 7.6_

- [x] 3. Thêm tham số cấu hình crawler
  - [x] 3.1 Bổ sung tham số vào `app/core/config.py`
    - Thêm `FETCH_CONCURRENCY_LIMIT` (mặc định 4, 1..10), `DEFAULT_TOP_N` (mặc định 20, 1..100), `MIN_CONTENT_LENGTH` (mặc định 500), `FETCH_TIMEOUT` (mặc định 30, 5..120), `PER_SITE_RATE_LIMIT` (mặc định 1.0, 0.1..10), `CRAWLER_USER_AGENT` (mặc định chuỗi UA hệ thống)
    - _Requirements: 3.5, 3.7, 5.1, 5.6, 9.2, 11.1, 11.2, 11.3, 11.5_

- [x] 4. Xây dựng Source Registry
  - [x] 4.1 Tạo `app/services/sources/registry.py` với `SourceConfig`, `SOURCE_REGISTRY`, `validate_source`
    - `SourceConfig` dataclass (name, type, url, topics, tier, top_n); `VALID_TOPICS`; tập nguồn khởi đầu theo bảng thiết kế (CafeF `https://cafef.vn/thi-truong-chung-khoan.rss`, TuoiTre, ThanhNien, VnBusiness, VnExpressKinhDoanh)
    - `validate_source` trả `None` nếu hợp lệ hoặc chuỗi mô tả lỗi (thiếu thuộc tính, type ngoài {rss, playwright}, topics rỗng/ngoài tập, tier ngoài 1..5, name rỗng/>100)
    - _Requirements: 1.1, 1.6, 1.7, 3.1, 3.4_
  - [x] 4.2 Hiện thực `load_sources`, `resolve_active_sources`, `supported_sources_map`
    - `load_sources()`: validate từng nguồn, loại nguồn lỗi (sinh cảnh báo/lỗi mỗi nguồn), trùng tên dùng bản đầu tiên (sinh cảnh báo)
    - `resolve_active_sources(active_sources)`: lọc theo chuỗi (chuẩn hóa lowercase, trim), tên rác → cảnh báo + bỏ qua
    - `supported_sources_map()`: suy ra map key→name từ registry hợp lệ
    - _Requirements: 1.2, 1.5, 1.8, 13.1_
  - [x] 4.3 Viết property test validate registry chỉ giữ nguồn hợp lệ
    - **Property 1: Validate registry chỉ giữ nguồn hợp lệ**
    - **Validates: Requirements 1.1, 1.7, 3.1, 3.4**
  - [x] 4.4 Viết property test trùng tên dùng bản đầu tiên
    - **Property 2: Trùng tên dùng bản đầu tiên**
    - **Validates: Requirements 1.8**
  - [x] 4.5 Viết property test resolve active_sources là tập con của registry
    - **Property 3: Resolve active_sources là tập con của registry**
    - **Validates: Requirements 1.5, 13.1**
  - [x] 4.6 Cập nhật `app/api/v1/settings.py` dùng `supported_sources_map()`
    - Thay `SUPPORTED_SOURCES_MAP` hard-code bằng giá trị suy ra từ registry; giữ nguyên hành vi validate/response của endpoint crawler
    - _Requirements: 1.6_
  - [x] 4.7 Viết unit test định tuyến type nguồn → tầng xử lý
    - Nguồn type=rss → RSS_Discovery; type=playwright → Playwright_Fallback
    - _Requirements: 1.2, 1.3, 1.4, 6.1_

- [x] 5. Xây dựng module Health
  - [x] 5.1 Tạo `app/services/health.py` với `SourceStatus`, `SourceHealth`, `to_camel`
    - `SourceStatus` Literal {ok, empty, dead, parse_error, blocked}; dataclass `SourceHealth` (source, status, articles_count, duration_ms, error_message); `to_camel()` xuất khóa camelCase
    - _Requirements: 8.1, 8.2_
  - [x] 5.2 Hiện thực hàm ánh xạ điều kiện truy cập feed → `SourceStatus`
    - Đầu vào: mã HTTP, cờ "nội dung là XML hợp lệ", số mục hợp lệ, cờ timeout/DNS-fail; áp quy tắc ưu tiên `dead` theo thiết kế
    - _Requirements: 2.4, 2.5, 2.6, 2.7, 2.8, 2.9, 8.3, 8.4, 8.5, 8.6, 8.7_
  - [x] 5.3 Viết property test ánh xạ điều kiện → SourceStatus
    - **Property 4: Ánh xạ điều kiện → SourceStatus là xác định**
    - **Validates: Requirements 2.4, 2.5, 2.6, 2.7, 2.8, 2.9, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7**
  - [x] 5.4 Viết property test bất biến của SourceHealth
    - **Property 16: Bất biến của SourceHealth**
    - **Validates: Requirements 8.1, 8.2, 10.1**

- [x] 6. Xây dựng RSS Discovery
  - [x] 6.1 Tạo `app/services/extraction/rss.py` với `ArticleStub` và `discover_rss`
    - Chuyển logic parse XML/`clean_html`/`parse_pub_date` từ `BaseScraper` sang đây; lấy tối đa 100 mục theo thứ tự feed; chuẩn hóa URL tuyệt đối; bỏ mục thiếu title/url; teaser rỗng khi thiếu
    - Không raise ra ngoài: trả `(list[ArticleStub], SourceStatus)` dùng hàm ánh xạ ở 5.2
    - _Requirements: 2.1, 2.2, 2.3, 2.10_
  - [x] 6.2 Viết property test giới hạn và làm sạch mục
    - **Property 5: RSS Discovery giới hạn và làm sạch mục**
    - **Validates: Requirements 2.1, 2.10**
  - [x] 6.3 Viết property test URL bài viết luôn tuyệt đối
    - **Property 6: URL bài viết luôn được chuẩn hóa tuyệt đối**
    - **Validates: Requirements 2.3**
  - [x] 6.4 Viết unit test discover_rss với httpx mock
    - Mock các phản hồi: XML hợp lệ, channel rỗng, HTML thay XML, HTTP 403/429, HTTP ≥400, timeout/DNS → SourceStatus tương ứng
    - _Requirements: 2.4, 2.5, 2.6, 2.7, 2.8, 2.9_

- [x] 7. Xây dựng bộ lọc hai giai đoạn
  - [x] 7.1 Tạo `app/services/extraction/filters.py` với `pre_filter`, `full_content_filter`
    - Tái sử dụng `zero_cost_filter`; `pre_filter` chạy trên `title + teaser`; `full_content_filter` chạy trên `title + body`
    - _Requirements: 4.1, 4.2, 4.7, 4.8_
  - [x] 7.2 Viết property test Pre_Filter loại bài không thỏa
    - **Property 8: Pre_Filter loại bài không thỏa tiêu chí**
    - **Validates: Requirements 4.1, 4.2**
  - [x] 7.3 Viết property test Full_Content_Filter chặn trước khi lưu
    - **Property 9: Full_Content_Filter chặn trước khi lưu**
    - **Validates: Requirements 4.7, 4.8**

- [x] 8. Xây dựng Content Extractor (HTTP tĩnh)
  - [x] 8.1 Tạo `app/services/extraction/content.py` với `ExtractionResult` và `extract_full_content`
    - Tải trang qua `httpx.Client` (timeout từ `FETCH_TIMEOUT`), trích xuất bằng `trafilatura.extract`
    - HTTP ≥400 → `ok=False`, `error="http_<code>"`, `http_status` set, không ghi đè; timeout/network → `ok=False`, `error∈{timeout,network}`; `needs_fallback=True` khi body < `MIN_CONTENT_LENGTH`
    - _Requirements: 5.1, 5.4, 5.5, 5.6, 11.5_
  - [x] 8.2 Viết property test needs_fallback theo ngưỡng
    - **Property 11: needs_fallback theo ngưỡng độ dài**
    - **Validates: Requirements 5.6**
  - [x] 8.3 Viết unit test extract_full_content với mock HTTP
    - Body hợp lệ; HTTP ≥400 kèm mã lỗi không ghi đè; timeout; lỗi mạng
    - _Requirements: 5.1, 5.2, 5.4, 5.5_

- [x] 9. Xây dựng Politeness (rate limit + User-Agent)
  - [x] 9.1 Tạo `app/services/extraction/politeness.py` với `RateLimiter`
    - `RateLimiter(per_second)` khóa per-host an toàn luồng (threading.Lock + thời điểm cho phép tiếp theo theo host); helper lấy User-Agent từ `settings.CRAWLER_USER_AGENT`, rỗng → UA mặc định
    - _Requirements: 11.1, 11.2, 11.3, 11.4_
  - [x] 9.2 Viết property test rate limit per-site
    - **Property 19: Rate limit per-site đảm bảo khoảng cách tối thiểu**
    - **Validates: Requirements 11.3, 11.4**
  - [x] 9.3 Viết unit test User-Agent header
    - Có cấu hình → dùng UA cấu hình; rỗng → dùng UA mặc định hệ thống
    - _Requirements: 11.1, 11.2_

- [x] 10. Xây dựng Playwright Fallback
  - [x] 10.1 Tạo `app/services/extraction/playwright_fallback.py` với `PlaywrightFallback`
    - Context manager mở đúng 1 chromium (sync API), tắt tải ảnh; `extract(url)` thử tối đa 1 lần, timeout 30s → `error=timeout`, lỗi xử lý → `ok=False`; `__exit__` đóng browser
    - Đóng gói chạy trong thread riêng để an toàn khi gọi từ handler async `/ingest`
    - _Requirements: 6.2, 6.3, 6.4, 6.5, 6.6, 6.8, 9.4, 9.5, 9.6_
  - [x] 10.2 Viết unit test Playwright (mock hoặc skipif)
    - Mock Playwright hoặc `@pytest.mark.skipif` khi chưa cài chromium; kiểm ≤1 lần thử, timeout, lỗi xử lý, chỉ 1 browser và đóng cuối lần chạy
    - _Requirements: 6.2, 6.3, 6.4, 6.5, 6.6, 6.8, 9.4, 9.5, 9.6_

- [x] 11. Sửa Orchestrator `app/services/crawler.py`
  - [x] 11.1 Hiện thực `select_top_n`
    - Chọn `min(top_n_hiệu_dụng, len(stubs))` bài đầu danh sách theo thứ hạng feed; `top_n=None` dùng `DEFAULT_TOP_N`
    - _Requirements: 3.2, 3.3, 3.6, 3.7_
  - [x] 11.2 Hiện thực `filter_new_urls`
    - Loại stub có `url` đã tồn tại trong `NewsArticle`, giữ thứ tự tương đối các url mới
    - _Requirements: 4.3, 4.4, 4.5_
  - [x] 11.3 Viết lại `upsert_news_articles` giữ chữ ký, bổ sung `summary` và cắt teaser ≤ 5.000 ký tự
    - Upsert idempotent theo `url` nguyên văn; bỏ url rỗng/thiếu; trùng url giữ bài đầu tiên; gán `status="pending_entity_extraction"` khi chưa chỉ định; lưu `summary` độc lập với `content`; giữ `begin_nested()` cô lập lỗi từng bản ghi
    - _Requirements: 5.3, 7.1, 12.1, 12.2, 12.3, 12.4, 12.5, 13.3_
  - [x] 11.4 Viết lại `ingest_news_articles` điều phối 3 tầng giữ chữ ký
    - Dùng `resolve_active_sources`; dừng lần chạy khi `active_sources` không đọc/áp dụng được (ghi log lỗi, không sửa dữ liệu); lặp từng nguồn → discovery → `select_top_n` → `pre_filter` → `filter_new_urls` → `ThreadPoolExecutor(max_workers=FETCH_CONCURRENCY_LIMIT)` gọi `extract_full_content` → hàng đợi Playwright tuần tự → `full_content_filter` → loại bài body < ngưỡng (không lưu một phần) → `upsert_news_articles`
    - Tổng hợp `source_health`; truyền `parent_trace_id` vào worker; đánh dấu thất bại toàn phần khi mọi nguồn `status != ok`; trả dict mở rộng thêm `source_health` (giữ nguyên `total_scraped/total_filtered/total_saved/errors`)
    - _Requirements: 3.6, 4.6, 6.7, 8.9, 9.1, 9.3, 10.1, 10.2, 10.3, 10.4, 10.5, 13.1, 13.2_
  - [x] 11.5 Viết property test chọn Top-N là tiền tố
    - **Property 7: Chọn Top-N là tiền tố và bị chặn bởi min(top_n, len)**
    - **Validates: Requirements 3.2, 3.3, 3.7**
  - [x] 11.6 Viết property test dedup giữ URL mới theo thứ tự
    - **Property 10: Dedup loại URL đã tồn tại, giữ URL mới theo thứ tự**
    - **Validates: Requirements 4.3, 4.4, 4.5**
  - [x] 11.7 Viết property test upsert idempotent theo URL
    - **Property 13: Upsert idempotent theo URL nguyên văn**
    - **Validates: Requirements 12.1, 12.2, 12.3, 12.4**
  - [x] 11.8 Viết property test lưu summary round-trip và giới hạn độ dài
    - **Property 14: Lưu summary round-trip và giới hạn độ dài**
    - **Validates: Requirements 5.3, 7.1**
  - [x] 11.9 Viết property test bài mới lưu mang trạng thái pending
    - **Property 15: Bài mới lưu mang trạng thái pending**
    - **Validates: Requirements 13.3**
  - [x] 11.10 Viết property test bài đã lưu luôn có content đủ dài
    - **Property 12: Bài đã lưu luôn có content đủ dài**
    - **Validates: Requirements 6.7**
  - [x] 11.11 Viết property test báo cáo phản ánh mọi nguồn và cô lập lỗi
    - **Property 17: Báo cáo phản ánh mọi nguồn và cô lập lỗi**
    - **Validates: Requirements 8.9, 10.3, 10.5**
  - [x] 11.12 Viết unit test các nhánh wiring orchestrator
    - Cô lập lỗi một bài/một nguồn (4.6, 12.5, 10.5); dừng khi config hỏng (13.2); RSS rỗng → 0 fetch + log (3.6); biên Top_N 1/100/ngoài range (3.5); worker nhận đúng parent trace_id (10.2, 10.4)
    - _Requirements: 3.5, 3.6, 4.6, 10.2, 10.4, 10.5, 12.5, 13.2_

- [x] 12. Checkpoint - Đảm bảo toàn bộ test lõi pipeline đạt
  - Đảm bảo tất cả test đã viết tới bước này đạt; hỏi người dùng nếu phát sinh thắc mắc.

- [x] 13. Bổ sung Source Health vào endpoint `/ingest`
  - [x] 13.1 Bổ sung `sourceHealth` vào phản hồi `POST /api/v1/news/ingest`
    - Trong `app/api/v1/news.py`, giữ nguyên `totalScraped/totalFiltered/totalSaved/errors`; thêm `sourceHealth` từ `source_health` (camelCase)
    - _Requirements: 8.8, 13.6_
  - [x] 13.2 Viết unit test endpoint `/ingest` với TestClient
    - Kiểm giữ đủ trường cũ và có thêm `sourceHealth`
    - _Requirements: 8.8, 13.6_
  - [x] 13.3 (Tùy chọn) Thêm `GET /api/v1/news/source-health` trả snapshot lần chạy gần nhất
    - Chỉ làm nếu cần cho Jobs_View truy vấn độc lập; giữ `sourceHealth` trong `/ingest` là mặc định
    - _Requirements: 8.8_

- [x] 14. Cập nhật AI Pipeline xử lý content rỗng/null
  - [x] 14.1 Bỏ qua bài có `content` rỗng/null trong `process_pending_news_articles`
    - Trong `app/services/ai_pipeline.py`, trước khi gọi `run_extraction`, nếu `content` rỗng/null → gán trạng thái biểu thị không xử lý được, bỏ qua, tiếp tục bài khác
    - _Requirements: 13.4, 13.5_
  - [x] 14.2 Viết unit test AI pipeline tương thích
    - Bài `content=""`/NULL → bỏ qua + status không xử lý được; bài full body → chạy `run_extraction(content)` (mock CrewAI như conftest)
    - _Requirements: 13.4, 13.5_

- [x] 15. Kiểm thử tích hợp và xác nhận nguồn sống
  - [x] 15.1 Viết smoke test xác nhận URL nguồn trong registry còn sống
    - Đánh dấu `@pytest.mark.network`/integration (có thể skip trên CI); gọi thật từng URL RSS, khẳng định trả XML hợp lệ
    - _Requirements: 2.2_
  - [x] 15.2 Viết integration test end-to-end trên SQLite in-memory
    - Dựng feed RSS giả + trang bài viết giả (httpx mock/transport), chạy `ingest_news_articles()`; kiểm bài được lọc → tải → lưu với `content` + `summary`, `source_health` đầy đủ, status `pending_entity_extraction`
    - _Requirements: 4.1, 4.7, 5.2, 5.3, 8.1, 13.3_

- [x] 16. Checkpoint cuối - Đảm bảo toàn bộ test đạt
  - Đảm bảo tất cả test đạt; hỏi người dùng nếu phát sinh thắc mắc.

## Notes

- Task gắn `*` là tùy chọn (chủ yếu là test) và có thể bỏ qua khi cần MVP nhanh; task lõi không gắn `*`.
- Mỗi task tham chiếu requirement và/hoặc property cụ thể để truy vết.
- Property test dùng Hypothesis với tối thiểu 100 ví dụ và comment `# Feature: news-crawler-fulltext, Property N: ...`.
- Checkpoint đảm bảo kiểm chứng tăng dần.
- Tương thích ngược: chữ ký `ingest_news_articles`/`upsert_news_articles` và trường phản hồi `/ingest` cũ được giữ nguyên.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "2.1", "3.1", "4.1", "5.1", "7.1", "8.1", "9.1"] },
    { "id": 1, "tasks": ["2.2", "4.2", "5.2", "10.1"] },
    { "id": 2, "tasks": ["4.6", "6.1", "2.3", "2.4", "4.3", "4.4", "4.5", "4.7", "5.3", "5.4", "7.2", "7.3", "8.2", "8.3", "9.2", "9.3", "10.2"] },
    { "id": 3, "tasks": ["6.2", "6.3", "6.4", "11.1"] },
    { "id": 4, "tasks": ["11.2"] },
    { "id": 5, "tasks": ["11.3"] },
    { "id": 6, "tasks": ["11.4"] },
    { "id": 7, "tasks": ["11.5", "11.6", "11.7", "11.8", "11.9", "11.10", "11.11", "11.12", "13.1", "14.1"] },
    { "id": 8, "tasks": ["13.2", "13.3", "14.2", "15.1", "15.2"] }
  ]
}
```
