---
stepsCompleted: [1, 2, 3]
inputDocuments:
  - "_bmad-output/planning-artifacts/prds/prd-quantyFin-ai-2026-06-03/prd.md"
  - "docs/design_ui_ux/PRD-QuantyFin-standalone.md"
  - "_bmad-output/planning-artifacts/architecture.md"
  - "_bmad-output/planning-artifacts/ux-designs/run-2026-06-05/DESIGN.md"
  - "_bmad-output/planning-artifacts/ux-designs/run-2026-06-05/EXPERIENCE.md"
---

# quantyFin-ai - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for quantyFin-ai, decomposing the requirements from the PRD, UX Design if it exists, and Architecture requirements into implementable stories.

## Requirements Inventory

### Functional Requirements

FR1: Thu thập Dữ liệu Giá & Chỉ số: Tự động lấy dữ liệu giao dịch hàng ngày (OHLCV) và chỉ báo kỹ thuật cơ bản từ thư viện vn-stock hoặc các nguồn dữ liệu tương đương.
FR2: Thu thập Tin tức (News Scraping): Tự động cào và làm sạch tin tức từ các nguồn hỗ trợ RSS hoặc cào trực tiếp (CafeF, NDH, VnEconomy, Vietstock, Tuổi Trẻ, Thanh Niên, VnBusiness).
FR3: Lập lịch chạy tự động (Scheduling): Pipeline thu thập tự động chạy định kỳ (batch 1 hoặc 2 lần/ngày, ví dụ sau giờ giao dịch 15:30).
FR4: Trích xuất thực thể (Entity Extraction): Sử dụng AI/NLP để đọc tin tức và trích xuất Ticker, Công ty, Lãnh đạo, Ngành nghề, Sự kiện vĩ mô.
FR5: Xây dựng mối quan hệ (Relationship Mapping): Kết nối các thực thể (Ví dụ: "Sự kiện A" -> [TÁC_ĐỘNG_TIÊU_CỰC_LÊN] -> "Ngành B" -> [CÓ_CỔ_PHIẾU] -> "Mã XYZ").
FR6: Lưu trữ cấu trúc Graph: Lưu trữ dữ liệu đồ thị dưới dạng Graph Database (Neo4j) kết hợp với Vector Database để phục vụ tìm kiếm ngữ nghĩa.
FR7: Đánh giá tâm lý thị trường (Sentiment Analysis): Chấm điểm cảm xúc (Positive - Tích cực, Neutral - Trung tính, Negative - Tiêu cực) của bài viết/sự kiện tác động lên mã cổ phiếu.
FR8: SideRail & Topbar (Navigation Shell): Shell điều hướng gồm SideRail (Dashboard, KG, Stock Detail, News, Chat, Alerts, Jobs, Settings) và Topbar (Logo, Scenario Switcher, Quick Search, Logout).
FR9: Màn hình Đăng nhập (Login Screen): Form xác thực email/username và password; tự động đăng nhập khi truy cập lần đầu nếu qf_auth = null, lưu trạng thái vào localStorage.
FR10: Màn hình Dashboard (Tổng quan thị trường): Hiển thị VN-Index, HNX, UPCoM theo kịch bản thị trường; danh sách Top Movers; Portfolio Snapshot; Recent Alerts & News Teaser.
FR11: Màn hình Sơ đồ Tri thức (Knowledge Graph Screen): Trực quan hóa đồ thị liên kết thực thể dạng force-directed bằng D3.js, hỗ trợ kéo thả, zoom, click chọn node chuyển sang Stock Detail hoặc xem panel chi tiết.
FR12: Màn hình Chi tiết Cổ phiếu (Stock Detail Screen): Hiển thị giá hiện tại, % thay đổi, volume; AI Confidence Indicator; biểu đồ giá lịch sử; chỉ số tài chính (P/E, EPS, Vốn hóa...) và phân tích của AI.
FR13: Màn hình Tin tức (News Screen): Danh sách tin tức có gán nhãn Sentiment; hỗ trợ bộ lọc tin theo ngành, mã cổ phiếu và loại tin tức.
FR14: Giao diện Chat với Trợ lý AI (Chat Screen): Giao diện bubble chat; gợi ý quick prompts; tự động nhận diện mã cổ phiếu bôi đậm và chuyển thành link click dẫn sang Stock Detail.
FR15: Màn hình Quản lý Cảnh báo (Alerts Screen): Hiển thị Triggered Alerts (Critical, Warning, Info); form tạo mới cảnh báo; nút đóng (Dismiss) hoặc xem chi tiết.
FR16: Màn hình Tác vụ Chạy nền (Background Jobs Screen): Quản lý các tác vụ AI nền (phân tích portfolio, quét sentiment, tổng hợp báo cáo) và hiển thị tiến trình (progress bar).
FR17: Màn hình Cấu hình Hệ thống (Settings Screen): Cấu hình chia theo nhóm (AI & Dữ liệu, Giao diện, Thông báo, Tài khoản, Nâng cao), cho phép cấu hình LLM Gateway (API Endpoint, API Key, Model, Temperature).
FR18: Tích hợp Telegram Bot: Tự động gửi cảnh báo rủi ro danh mục và hỗ trợ truy vấn nhanh thông qua kênh Telegram dành cho các nhà đầu tư nội bộ.

### NonFunctional Requirements

NFR1: Chi phí (Cost-efficiency): Tối đa sử dụng nguồn mở và API miễn phí. Lọc rác trước khi đưa qua LLM.
NFR2: Bảo mật nội bộ: Dữ liệu là tài sản nội bộ, chỉ giới hạn quyền truy cập, xác thực cơ bản (OAuth2PasswordBearer).
NFR3: Khả năng mở rộng: Kiến trúc module hóa, dễ thêm crawler mới.
NFR4: Tối ưu chi phí API LLM: Cơ chế caching, batching, rate-limiting để kiểm soát token (thông qua LiteLLM).
NFR5: Sự cố cô lập (Fault Isolation): Lỗi crawler hoặc API LLM chạy ngầm không được ảnh hưởng đến uptime của Telegram bot và Web Dashboard.
NFR6: Triển khai đơn giản: Chạy trọn vẹn trên một máy chủ duy nhất qua Docker Compose.

### Additional Requirements

- Starter Template: Custom Full-Stack Integration (FastAPI Backend + Vite/React Frontend). Việc thiết lập phải cấu hình Docker Compose liên kết FastAPI, React, Postgres, Neo4j.
- Backend Core: Python/FastAPI sử dụng `uv` để quản lý package. Yêu cầu `sqlmodel`, `psycopg2-binary`, `neo4j`, `pydantic-settings`.
- Frontend Core: Vite/React/TypeScript sử dụng Tailwind CSS v4 và `shadcn/ui`.
- Database & ORM: SQLModel + Alembic cho PostgreSQL. Bảng lưu trữ công việc (jobs) phải có Index cho `status` và `job_id` để polling.
- AI Orchestration & Gateway: CrewAI cho agents và LiteLLM đứng làm Gateway chặn rate limit/quản lý chi phí.
- Frontend State & Routing: TanStack Router + TanStack Query + Zustand để quản lý State/Data fetching Type-safe.
- Data Integration Boundary: Tách biệt lớp "Zero-Cost Filter" cào thô và lớp "AI Engine". Giao tiếp qua `BackgroundTasks` và lưu trạng thái ở bảng jobs.
- API Schema & Error Handling: Tất cả API phải bọc bằng `ApiResponse<T>`, xử lý lỗi global và kèm `trace_id` (UUID). Auto-gen types client.
- Kiểm thử (Testing): Bắt buộc setup Pytest (Backend) với các mock cho LLM và Playwright (Frontend) ở ngay Epic đầu tiên.

### UX Design Requirements

UX-DR1: Bảng màu thương hiệu & Trạng thái: Áp dụng các Token màu `--brand` (navy `#2a2b86`), `--iris` (AI/tech default `#7c6cf5`), `--mint` (LIVE/thành công `#10b981`), `--rose` (REVIEW `#f472b6`) và `--gap` (Alert/cảnh báo `#ef4444`).
UX-DR2: Typography hiển thị: Áp dụng font Be Vietnam Pro cho văn bản thông thường, Montserrat cho tiêu đề lớn, và JetBrains Mono cho dữ liệu số, Ticker, log lỗi, trạng thái.
UX-DR3: Giao diện thẻ & Border: Triển khai hệ thống CSS/Tailwind theo Layout Grid 12 cột, dùng viền hairline 1px phân tách thay cho đổ bóng mờ kính.
UX-DR4: Các UI Component cơ bản: Xây dựng các component tái sử dụng (button-primary, button-secondary, dashboard-card, input-field) dựa trên thiết kế tokens.
UX-DR5: Status Badge Component: Xây dựng component Badge với 2 trạng thái thành công/lỗi rõ ràng để thông báo hoạt động crawler và pipeline.

### FR Coverage Map

FR1: Epic 1 - Thu thập dữ liệu giao dịch hàng ngày (OHLCV) và các chỉ số kỹ thuật.
FR2: Epic 1 - Cào và làm sạch tin tức từ RSS/cào trực tiếp.
FR3: Epic 1 - Lên lịch chạy batch tự động.
FR4: Epic 2 - Sử dụng AI/NLP để trích xuất thực thể.
FR5: Epic 2 - Kết nối các thực thể thành quan hệ đồ thị.
FR6: Epic 2 - Lưu trữ cấu trúc Graph vào Neo4j và Vector DB.
FR7: Epic 2 - Chấm điểm cảm xúc (Sentiment) của tin tức tác động lên mã cổ phiếu.
FR8: Epic 4 - Giao diện khung điều hướng (SideRail & Topbar).
FR9: Epic 4 - Màn hình Đăng nhập (Login Screen).
FR10: Epic 4 - Màn hình Dashboard (Tổng quan thị trường).
FR11: Epic 4 - Màn hình Sơ đồ Tri thức (Knowledge Graph Screen).
FR12: Epic 4 - Màn hình Chi tiết Cổ phiếu (Stock Detail Screen).
FR13: Epic 4 - Màn hình Tin tức (News Screen).
FR14: Epic 4 - Màn hình Chat với Trợ lý AI.
FR15: Epic 4 - Màn hình Quản lý Cảnh báo.
FR16: Epic 4 - Màn hình Tác vụ Chạy nền (Background Jobs).
FR17: Epic 4 - Màn hình Cấu hình Hệ thống (Settings).
FR18: Epic 3 - Tích hợp Telegram Bot và lắng nghe/gửi cảnh báo rủi ro tự động.

## Epic List

### Epic 1: Tự động hóa Thu thập Dữ liệu (Automated Data Ingestion)
Đảm bảo hệ thống tự động gom đủ "nguyên liệu thô" (giá chứng khoán, tin tức tài chính) một cách liên tục và sạch sẽ mỗi ngày mà không tốn chi phí rác cho API AI.
**FRs covered:** FR1, FR2, FR3

#### Story 1.1: Thiết lập cấu trúc dự án và môi trường kiểm thử (Project & Test Setup)
**Là một** Lập trình viên (Developer),
**Tôi muốn** khởi tạo cấu trúc thư mục của dự án (backend & frontend) từ starter template, cài đặt các thư viện cần thiết và cấu hình môi trường chạy test tự động (Pytest và Playwright),
**Để** tôi có thể bắt đầu phát triển các tính năng với môi trường kiểm thử tự động được cấu hình hoàn chỉnh.

**Tiêu chí nghiệm thu (Acceptance Criteria):**
- **Cho trước (Given)** thư mục dự án trống.
- **Khi (When)** chạy lệnh khởi tạo backend (FastAPI, SQLModel, Uvicorn, uv) và frontend (Vite, React, TypeScript, Tailwind v4, shadcn/ui).
- **Thì (Then)** cấu trúc thư mục của dự án được tạo đúng theo tài liệu kiến trúc (gồm thư mục `backend/` và `frontend/`).
- **Và (And)** thiết lập file `docker-compose.yml` cấu hình mạng nội bộ kết nối Frontend, Backend, PostgreSQL và Neo4j thành công.
- **Và (And)** chạy thành công các test case mẫu (dummy tests) bằng `pytest` ở backend và `playwright` ở frontend để xác nhận môi trường kiểm thử đã sẵn sàng.

#### Story 1.2: Thu thập Dữ liệu Giao dịch & Chỉ số Chứng khoán
**Là một** Hệ thống thu thập dữ liệu (Data Ingestion Module),
**Tôi muốn** cào dữ liệu giao dịch cuối ngày và điểm số của VN-Index cùng các mã cổ phiếu trong danh mục theo dõi,
**Để** Đồ thị tri thức (Knowledge Graph) có các node dữ liệu tài chính chính xác để sẵn sàng liên kết với cảm xúc (sentiment) từ tin tức.

**Tiêu chí nghiệm thu (Acceptance Criteria):**
- **Cho trước (Given)** đến thời điểm thu thập dữ liệu do Admin cấu hình (mặc định là 22:00 đêm cùng ngày giao dịch).
- **Khi (When)** module thu thập dữ liệu được hệ thống kích hoạt.
- **Thì (Then)** hệ thống gọi API/cào web và lấy thành công dữ liệu OHLCV (Giá Mở cửa, Cao nhất, Thấp nhất, Đóng cửa, Khối lượng) cho danh sách cổ phiếu mục tiêu.
- **Và (And)** lưu trữ dữ liệu thô vào cơ sở dữ liệu quan hệ (PostgreSQL), có cơ chế kiểm tra và cập nhật an toàn (upsert) để không bị nhân bản dữ liệu trùng lặp.

#### Story 1.3: Cào Tin tức & Tiền lọc Không tốn phí (Zero-cost Filter)
**Là một** Hệ thống thu thập dữ liệu (Data Ingestion Module),
**Tôi muốn** cào các bài báo tin tức tài chính và áp dụng ngay một bộ lọc logic/từ khóa tốc độ cao,
**Để** chỉ giữ lại các tin tức thực sự liên quan đến danh mục, giúp tiết kiệm triệt để chi phí token LLM đắt đỏ cho khâu phân tích sau này.

**Tiêu chí nghiệm thu (Acceptance Criteria):**
- **Cho trước (Given)** một danh sách các nguồn tin tức tài chính mục tiêu và tập luật cào dữ liệu (được Admin thiết lập trong cấu hình hệ thống).
- **Khi (When)** trình cào tin tức (news scraper) chạy quét các trang nguồn.
- **Thì (Then)** hệ thống bóc tách thành công tiêu đề, nội dung chi tiết và thời gian xuất bản của bài báo dựa trên quy tắc cấu hình.
- **Và (And)** áp dụng "Bộ lọc Zero-cost" (chạy bằng thuật toán matching từ khóa thông thường, không gọi AI) để loại bỏ ngay lập tức các bài báo không chứa mã cổ phiếu mục tiêu hoặc không có từ khóa tài chính quan trọng.
- **Và (And)** lưu các bài báo đã lọt qua bộ lọc vào PostgreSQL với trạng thái `pending_entity_extraction` (chờ trích xuất thực thể).

#### Story 1.4: Thiết lập Lịch trình & Cấu hình Động cho Crawler (Dynamic Batch Scheduler)
**Là một** Quản trị viên hệ thống (System Administrator),
**Tôi muốn** thay đổi linh hoạt lịch chạy tác vụ và các tham số cấu hình của crawler (thời gian chạy, danh sách mã cổ phiếu, nguồn tin),
**Để** quản lý toàn bộ cách thức cào dữ liệu mà không cần phải can thiệp hay triển khai (deploy) lại mã nguồn (source code).

**Tiêu chí nghiệm thu (Acceptance Criteria):**
- **Cho trước (Given)** hệ thống backend có cung cấp cơ sở dữ liệu hoặc file cấu hình để quản lý thông số crawler.
- **Khi (When)** Admin thay đổi thời gian chạy (ví dụ: từ 16:00 sang 22:00) hoặc đổi cấu hình nguồn cào thông qua giao diện (Dashboard).
- **Thì (Then)** bộ lên lịch (scheduler) tự động cập nhật lịch chạy mới mà không cần khởi động lại toàn bộ server.
- **Và (And)** khi đồng hồ hệ thống điểm đúng thời gian cấu hình mới, scheduler sẽ tự động kích hoạt chuẩn xác Story 1.2 và Story 1.3 theo các tham số crawler mới nhất.
- **Và (And)** ghi log lại mọi tiến trình chạy tự động kèm theo `trace_id` để tiện truy vết lỗi.

### Epic 2: Xây dựng Đồ thị Tri thức & Cảm xúc (Knowledge Graph & Sentiment AI)
Chuyển hóa dữ liệu thô thành "Trí tuệ nhân tạo". Hệ thống có khả năng tự hiểu tin tức, kết nối các sự kiện, đánh giá độ tích cực/tiêu cực lên thị trường và sẵn sàng trả lời các câu hỏi phức tạp.
**FRs covered:** FR4, FR5, FR6, FR7

#### Story 2.1: Trích xuất Thực thể & Phân tích Cảm xúc bằng AI (Entity & Sentiment Extraction)
**Là một** Hệ thống xử lý Dữ liệu (AI Pipeline Module),
**Tôi muốn** sử dụng mô hình CrewAI và LiteLLM để phân tích các bài báo thô mới được thu thập,
**Để** bóc tách ra danh sách các thực thể (Công ty, Nhân vật, Sự kiện) và chấm điểm cảm xúc (Tích cực, Tiêu cực, Trung lập) đối với mã cổ phiếu liên quan.

**Tiêu chí nghiệm thu (Acceptance Criteria):**
- **Cho trước (Given)** có các bài báo mới trong PostgreSQL đang ở trạng thái `pending_entity_extraction`.
- **Khi (When)** tiến trình AI Pipeline được kích hoạt (chạy tự động theo lô).
- **Thì (Then)** hệ thống gửi nội dung bài báo qua cổng LiteLLM để các Agent của CrewAI phân tích.
- **Và (And)** nhận về một file cấu trúc JSON hợp lệ chứa: danh sách thực thể, mối quan hệ thô, và điểm số cảm xúc (sentiment score).
- **Và (And)** cập nhật trạng thái bài báo trong cơ sở dữ liệu thành `extraction_completed`.

#### Story 2.2: Chuẩn hóa Thực thể & Tránh trùng lặp (Entity Resolution)
**Là một** Hệ thống xử lý Dữ liệu (AI Pipeline Module),
**Tôi muốn** chuẩn hóa các tên gọi khác nhau của cùng một đối tượng (ví dụ: "Vingroup", "Tập đoàn Vượng", "VIC") về một ID danh tính chuẩn duy nhất,
**Để** đảm bảo Đồ thị Tri thức (Knowledge Graph) không bị loãng và các liên kết hội tụ chính xác vào đúng một Node thay vì tạo ra nhiều Node rác.

**Tiêu chí nghiệm thu (Acceptance Criteria):**
- **Cho trước (Given)** một danh sách các thực thể thô vừa được AI trích xuất ở Story 2.1.
- **Khi (When)** luồng dữ liệu đi qua module Chuẩn hóa Thực thể (Entity Resolution).
- **Thì (Then)** hệ thống sẽ tra cứu một từ điển đồng nghĩa (Synonyms/Alias DB) hoặc dùng thuật toán matching nhanh để đối chiếu thực thể thô với các Node đã tồn tại.
- **Và (And)** tự động gán một mã ID chuẩn (Canonical ID) cho thực thể thô đó trước khi chuyển sang bước tiếp theo.

#### Story 2.3: Xây dựng & Đồng bộ vào Đồ thị Tri thức (Graph Construction in Neo4j)
**Là một** Hệ thống lưu trữ (Graph Storage Module),
**Tôi muốn** lưu các thực thể đã chuẩn hóa cùng các dữ liệu thị trường vào cơ sở dữ liệu đồ thị Neo4j,
**Để** hình thành một mạng lưới quan hệ rõ ràng (Edges/Nodes) sẵn sàng cho việc truy vấn của Bot Telegram ở Epic sau.

**Tiêu chí nghiệm thu (Acceptance Criteria):**
- **Cho trước (Given)** các thực thể đã có Canonical ID (từ Story 2.2) và dữ liệu giá cổ phiếu OHLCV.
- **Khi (When)** hệ thống thực hiện thao tác ghi vào cơ sở dữ liệu đồ thị.
- **Thì (Then)** hệ thống tạo mới hoặc cập nhật các Node tương ứng trong Neo4j (ví dụ: `:Stock`, `:Company`, `:Article`).
- **Và (And)** tạo các Cạnh quan hệ (Edges) như `(Article)-[MENTIONS]->(Stock)` kèm theo trọng số (thuộc tính `sentiment_score`) ngay trên Cạnh đó.
- **Và (And)** đảm bảo quá trình ghi dữ liệu tuân thủ nghiêm ngặt Graph Schema đã thiết kế, ném ra lỗi (exception log) nếu có dữ liệu dị thường.

### Epic 3: Trợ lý Truy vấn & Cảnh báo Tự động (Proactive AI Alerts & Q&A)
Chủ động bảo vệ danh mục đầu tư. Thay vì phải vào web, nhà đầu tư nhận được cảnh báo rủi ro ngay lập tức qua Telegram và có thể chat, truy vấn thông tin thị trường linh hoạt.
**FRs covered:** FR18

#### Story 3.1: Hệ thống Lắng nghe & Phân tích Rủi ro tự động (Proactive Risk Monitor)
**Là một** Hệ thống theo dõi rủi ro (Risk Monitor Module),
**Tôi muốn** liên tục quét dữ liệu điểm cảm xúc (sentiment score) từ Neo4j kết hợp với độ sụt giảm/tăng giá từ dữ liệu thị trường,
**Để** phát hiện sớm các sự kiện bất thường hoặc điểm gãy xu hướng trước khi nó tác động xấu đến danh mục đầu tư.

**Tiêu chí nghiệm thu (Acceptance Criteria):**
- **Cho trước (Given)** dữ liệu thị trường và đồ thị tri thức Neo4j liên tục được cập nhật.
- **Khi (When)** một điều kiện ngưỡng (threshold) bị phá vỡ (ví dụ: một tin tức có Sentiment Score < -0.5 HOẶC Giá cổ phiếu giảm > 3% kèm theo một thực thể rủi ro).
- **Thì (Then)** hệ thống tự động kích hoạt một Sự kiện Cảnh báo (Alert Event).
- **Và (And)** đóng gói sự kiện này kèm theo luận điểm tóm tắt (nguyên nhân giảm/tăng) để đẩy sang module gửi tin nhắn.

#### Story 3.2: Tích hợp Gửi Cảnh báo qua Telegram (Telegram Alert Notification)
**Là một** Nhà đầu tư (Investor/User),
**Tôi muốn** nhận được tin nhắn cảnh báo tự động về điện thoại qua Telegram ngay khi có rủi ro/sự kiện liên quan đến mã chứng khoán tôi đang theo dõi,
**Để** tôi có thể đưa ra quyết định mua/bán kịp thời mà không cần phải canh chừng màn hình liên tục.

**Tiêu chí nghiệm thu (Acceptance Criteria):**
- **Cho trước (Given)** người dùng đã đăng ký Telegram ID và cấu hình danh mục mã cổ phiếu cần theo dõi (Watchlist).
- **Khi (When)** module gửi tin nhắn nhận được một Sự kiện Cảnh báo (Alert Event) từ Story 3.1.
- **Thì (Then)** hệ thống format nội dung cảnh báo thành tin nhắn dễ đọc (gồm: Mã cổ phiếu, Mức độ rủi ro, Tóm tắt sự kiện).
- **Và (And)** gọi API của Telegram Bot để gửi tin nhắn đến chính xác Telegram ID của người dùng.

#### Story 3.3: Chatbot Q&A truy vấn Đồ thị Tri thức (Telegram Q&A Bot)
**Là một** Nhà đầu tư (Investor/User),
**Tôi muốn** nhắn tin đặt câu hỏi bằng ngôn ngữ tự nhiên (ví dụ: "Tại sao cổ phiếu VIC hở gap giảm hôm nay?", "Các công ty con nào của Vingroup đang có tin xấu?") trực tiếp vào Bot Telegram,
**Để** nhận được câu trả lời tổng hợp nguyên nhân từ Đồ thị tri thức một cách trực quan và đầy đủ mà không phải tự đi tổng hợp thông tin.

**Tiêu chí nghiệm thu (Acceptance Criteria):**
- **Cho trước (Given)** người dùng gửi một tin nhắn văn bản vào chatbot Telegram.
- **Khi (When)** hệ thống tiếp nhận tin nhắn.
- **Thì (Then)** hệ thống sử dụng LLM để dịch ngôn ngữ tự nhiên thành câu lệnh truy vấn đồ thị (Cypher Query) và lấy dữ liệu từ Neo4j.
- **Và (And)** dùng LLM một lần nữa để tổng hợp kết quả thô thành câu trả lời tự nhiên, dễ hiểu.
- **Và (And)** gửi phản hồi lại cho người dùng trên Telegram với độ trễ (latency) tối ưu nhất có thể (lý tưởng là dưới 10 giây).

### Epic 4: Bảng Điều khiển Trực quan (Visual Admin Dashboard)
Cung cấp "Buồng lái" (Cockpit) cho người quản trị. Theo dõi sức khỏe hệ thống crawler, giám sát tiến trình phân tích AI và trực quan hóa bản đồ Knowledge Graph một cách trực quan, hiện đại, kế thừa 100% hệ thống thiết kế QuantyFin Design System.
**FRs covered:** FR8, FR9, FR10, FR11, FR12, FR13, FR14, FR15, FR16, FR17
**UX-DRs covered:** UX-DR1, UX-DR2, UX-DR3, UX-DR4, UX-DR5

#### Story 4.1: Xây dựng Hệ thống Giao diện Cơ sở (QuantyFin Design Tokens)
**Là một** Lập trình viên Frontend,
**Tôi muốn** thiết lập toàn bộ CSS/Tailwind theo đúng hệ thống token của QuantyFin Design System (từ file DESIGN.md),
**Để** đảm bảo tất cả các trang của Dashboard đều đồng nhất về màu sắc (Nền surface `[data-surface="app"]`, `--brand` navy `#2a2b86`, `--iris` `#7c6cf5`), phông chữ (Be Vietnam Pro, Montserrat & JetBrains Mono) và viền (hairline 1px).

**Tiêu chí nghiệm thu (Acceptance Criteria):**
- **Cho trước (Given)** môi trường dự án React/Vite.
- **Khi (When)** khởi tạo dự án.
- **Thì (Then)** toàn bộ biến màu (colors), phông chữ (typography), độ bo góc (rounded) được cấu hình chuẩn xác vào `tailwind.config.js`.
- **Và (And)** xây dựng sẵn các component nền tảng: `button-primary` (màu `--brand` chữ trắng), `dashboard-card` (nền surface `[data-surface="app"]`), `status-badge` (LIVE `--mint` / GAP `--gap` / REVIEW `--rose`).

#### Story 4.2: Giao diện Giám sát Crawler & Log (Crawler Terminal & Monitor)
**Là một** Quản trị viên hệ thống (Admin),
**Tôi muốn** có một màn hình quản lý Crawler với phong cách "Terminal / Trading Desk",
**Để** theo dõi log hệ thống real-time, cấu hình thời gian chạy và xem danh sách mã cổ phiếu đang cào một cách chuyên nghiệp.

**Tiêu chí nghiệm thu (Acceptance Criteria):**
- **Cho trước (Given)** Admin truy cập tab "Crawler Monitor".
- **Khi (When)** dữ liệu đang được cào.
- **Thì (Then)** hiển thị bảng danh sách các tiến trình với các cột sử dụng font `JetBrains Mono` để căn chỉnh chính xác.
- **Và (And)** các trạng thái thành công/thất bại sử dụng triệt để màu `--mint` (#10b981) và `--gap` (#ef4444).
- **Và (And)** có nút `button-primary` màu `--brand` (navy) để kích hoạt chạy Crawler ngay lập tức (Run Now).

#### Story 4.3: Giao diện Command Center cho AI Pipeline
**Là một** Quản trị viên hệ thống (Admin),
**Tôi muốn** một màn hình theo dõi số lượng Token LLM và hiệu suất trích xuất thực thể với các con số cực kỳ to lớn (Command Center style),
**Để** kiểm soát chi phí API và năng lực của CrewAI một cách trực quan nhất.

**Tiêu chí nghiệm thu (Acceptance Criteria):**
- **Cho trước (Given)** Admin truy cập tab "AI Pipeline Health".
- **Khi (When)** trang được tải.
- **Thì (Then)** hiển thị các thẻ (Cards) chứa các con số Metrics lớn (ví dụ: Tổng Token, Chi phí ước tính $) bằng phông chữ số liệu chuẩn.
- **Và (And)** hiển thị lưu đồ ngang (Pipeline Flow) cho thấy luồng dữ liệu từ Raw News -> Filter -> LLM -> Graph.

#### Story 4.4: Bản đồ Trực quan hóa Đồ thị Tri thức (Node Explorer / Bento Box)
**Là một** Quản trị viên hệ thống (Admin),
**Tôi muốn** xem Đồ thị Tri thức Neo4j được tích hợp gọn gàng trong các khối vuông (Bento Box),
**Để** kiểm tra trực quan chất lượng mạng lưới dữ liệu (zoom, click vào Node) ngay bên cạnh các bảng điều khiển khác mà không bị rối mắt.

**Tiêu chí nghiệm thu (Acceptance Criteria):**
- **Cho trước (Given)** Admin truy cập trang chủ Dashboard.
- **Khi (When)** Admin tìm kiếm một mã cổ phiếu.
- **Thì (Then)** hiển thị một canvas mạng lưới (Network Graph) trên nền surface `[data-surface="app"]` với các Node/Edge sắc nét.
- **Và (And)** khi click vào một Node, panel bên phải (Focus Sidebar) sẽ trượt ra hiển thị chi tiết thuộc tính (Sentiment Score, Nguồn bài báo) với font chữ và hairline chuẩn QuantyFin.

#### Story 4.5: Khung Điều hướng & Đăng nhập (App Shell, SideRail, Topbar & Login Screen)
**Là một** Quản trị viên hệ thống (Admin),  
**Tôi muốn** đăng nhập vào hệ thống và điều hướng linh hoạt giữa các màn hình bằng thanh SideRail và Topbar,  
**Để** tôi có thể truy cập và quản lý các tính năng của "buồng lái" (Cockpit).

**Tiêu chí nghiệm thu (Acceptance Criteria):**
- **Cho trước (Given)** người dùng chưa đăng nhập (localStorage `qf_auth = null` hoặc `'0'`).
- **Khi (When)** truy cập vào ứng dụng.
- **Thì (Then)** màn hình Đăng nhập (Login Screen) hiển thị một form chứa email/username và mật khẩu với màu sắc chủ đạo của thương hiệu.
- **Và (And)** khi người dùng điền thông tin và nhấn "Đăng nhập", hệ thống cập nhật `qf_auth = '1'` trong localStorage và chuyển hướng sang Dashboard.
- **Và (And)** giao diện chính hiển thị thanh SideRail chứa các nút điều hướng (Dashboard, KG, Stock, News, Chat, Alerts, Jobs, Settings) kèm theo badge hiển thị số lượng cảnh báo chưa đọc từ `data.alerts.length`.
- **Và (And)** thanh Topbar hiển thị Logo, bộ chọn kịch bản (Scenario Switcher - 4 trạng thái), nút Tìm kiếm nhanh (chuyển sang Chat) và nút Đăng xuất (khi click sẽ chuyển `qf_auth = '0'`).

#### Story 4.6: Màn hình Dashboard & Chi tiết Cổ phiếu (Market Overview & Stock Detail Screen)
**Là một** Nhà đầu tư (Investor/User),  
**Tôi muốn** xem tổng quan thị trường trên Dashboard và chuyển sang phân tích chi tiết cho một mã cổ phiếu,  
**Để** tôi có thể nắm bắt nhanh tình hình thị trường và theo dõi các chỉ số tài chính của mã cổ phiếu đó.

**Tiêu chí nghiệm thu (Acceptance Criteria):**
- **Cho trước (Given)** người dùng đã đăng nhập và đang ở màn hình Dashboard.
- **Khi (When)** trang Dashboard được tải.
- **Thì (Then)** hệ thống hiển thị Market Summary (chỉ số VN-Index, HNX, UPCoM đổi màu theo kịch bản thị trường), Top Movers (cổ phiếu tăng/giảm mạnh nhất), Portfolio Snapshot và Recent Alerts & News Teaser.
- **Và (And)** khi click vào một mã cổ phiếu bất kỳ, hệ thống chuyển hướng người dùng sang màn hình Chi tiết Cổ phiếu (Stock Detail Screen) của mã đó.
- **Và (And)** màn hình Chi tiết Cổ phiếu hiển thị giá hiện tại, % thay đổi, khối lượng giao dịch, AI Confidence Indicator, biểu đồ giá lịch sử, các chỉ số tài chính (P/E, EPS, Vốn hóa, Tỷ suất cổ tức) và nhận định phân tích của AI.
- **Và (And)** chỉ báo độ tin cậy AI (Confidence Indicator) sẽ tự động ẩn đi nếu tùy chỉnh cấu hình tắt chỉ báo được bật (`body.qf-no-conf` được kích hoạt).

#### Story 4.7: Màn hình Tin tức & Trợ lý Chat AI (News Feed & Chat Assistant)
**Là một** Nhà đầu tư (Investor/User),  
**Tôi muốn** đọc tin tức có gán nhãn cảm xúc bởi AI và chat trực tiếp với trợ lý ảo về phân tích chứng khoán,  
**Để** tôi nhanh chóng nắm bắt các tin tức vĩ mô/doanh nghiệp quan trọng và nhận câu trả lời phân tích tức thì.

**Tiêu chí nghiệm thu (Acceptance Criteria):**
- **Cho trước (Given)** người dùng điều hướng sang màn hình Tin tức (News Screen).
- **Khi (When)** trang Tin tức được tải.
- **Thì (Then)** hệ thống hiển thị danh sách tin tức tài chính được gắn nhãn Sentiment (Tích cực, Tiêu cực, Trung tính) kèm theo các bộ lọc theo ngành, mã cổ phiếu và loại tin tức.
- **Và (And)** khi người dùng điều hướng sang màn hình Chat.
- **Thì (Then)** hệ thống hiển thị giao diện bong bóng chat (bubble chat UI) kèm theo các câu lệnh gợi ý nhanh (Quick Prompts).
- **Và (And)** khi người dùng gửi câu hỏi, AI Agent phản hồi chi tiết về cổ phiếu hoặc ngành dựa trên dữ liệu thị trường và kịch bản hiện tại.
- **Và (And)** các mã cổ phiếu xuất hiện trong câu trả lời của AI tự động được bôi đậm và chuyển thành link liên kết click để mở nhanh màn hình Stock Detail.

#### Story 4.8: Màn hình Quản lý Cảnh báo & Cấu hình Hệ thống (Alerts & Settings Screen)
**Là một** Quản trị viên hệ thống (Admin),  
**Tôi muốn** cấu hình LLM Gateway và quản lý các quy tắc cảnh báo rủi ro,  
**Để** tôi có thể tùy chỉnh các tham số AI của hệ thống và thiết lập các điểm kích hoạt thông báo tự động.

**Tiêu chí nghiệm thu (Acceptance Criteria):**
- **Cho trước (Given)** người dùng điều hướng sang màn hình Alerts.
- **Khi (When)** trang Alerts được tải.
- **Thì (Then)** hệ thống hiển thị danh sách cảnh báo đang được kích hoạt (Critical, Warning, Info) cùng form cho phép tạo mới quy tắc cảnh báo (theo mục tiêu giá, khối lượng hoặc từ khóa tin tức).
- **Và (And)** khi người dùng điều hướng sang màn hình Cấu hình (Settings Screen).
- **Thì (Then)** hệ thống hiển thị form cấu hình chia theo nhóm (AI & Dữ liệu, Giao diện, Thông báo, Tài khoản, Nâng cao).
- **Và (And)** người dùng có thể chỉnh sửa các tham số của LLM Gateway (API Endpoint, API Key, Model, Temperature) và nhấn nút kiểm tra kết nối để đo độ trễ (latency).

#### Story 4.9: Màn hình Tác vụ Chạy nền (Background Jobs Screen)
**Là một** Quản trị viên hệ thống (Admin),  
**Tôi muốn** theo dõi trạng thái hoạt động của các tác vụ chạy nền (Background Jobs) do AI Agent thực hiện,  
**Để** tôi biết tiến trình phân tích dữ liệu, sentiment hoặc tổng hợp báo cáo và xem kết quả của các tác vụ đã hoàn thành.

**Tiêu chí nghiệm thu (Acceptance Criteria):**
- **Cho trước (Given)** người dùng điều hướng sang màn hình Jobs.
- **Khi (When)** trang Jobs được tải.
- **Thì (Then)** hệ thống hiển thị danh sách các tác vụ chạy nền đang hoạt động hoặc đã lên lịch (phân tích portfolio, quét sentiment, tổng hợp báo cáo).
- **Và (And)** hiển thị thanh tiến trình (progress bar) cùng nhãn trạng thái trực quan (`Running`, `Completed`, `Failed`) sử dụng font `JetBrains Mono` chuẩn thiết kế.
- **Và (And)** khi click vào một tác vụ bất kỳ, hệ thống hiển thị panel chi tiết chứa thông tin kết quả phân tích hoặc log lỗi tương ứng.

