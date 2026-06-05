---
stepsCompleted: [1]
inputDocuments: ["_bmad-output/planning-artifacts/prds/prd-quantyFin-ai-2026-06-03/prd.md", "_bmad-output/planning-artifacts/architecture.md", "_bmad-output/planning-artifacts/ux-designs/ux-quantyFin-ai-2026-06-05/DESIGN.md"]
---

# quantyFin-ai - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for quantyFin-ai, decomposing the requirements from the PRD, UX Design if it exists, and Architecture requirements into implementable stories.

## Requirements Inventory

### Functional Requirements

FR1: Thu thập Dữ liệu Giá & Chỉ số: Tự động lấy dữ liệu giao dịch hàng ngày (OHLCV), chỉ báo kỹ thuật cơ bản từ thư viện vn-stock và các API miễn phí khác.
FR2: Thu thập Tin tức (News Scraping): Tự động "cào" và làm sạch tin tức từ các báo tài chính qua trực tiếp hoặc RSS.
FR3: Lập lịch chạy tự động (Scheduling): Pipeline thu thập tự động kích hoạt dạng batch.
FR4: Trích xuất thực thể (Entity Extraction): Đọc tin tức và bóc tách Ticker, Công ty, Lãnh đạo, Ngành nghề, Sự kiện.
FR5: Xây dựng mối quan hệ (Relationship Mapping): Gắn kết các thông tin thành đồ thị.
FR6: Lưu trữ dữ liệu: Lưu trữ cấu trúc Graph để phục vụ truy vấn và RAG.
FR7: Đánh giá tâm lý thị trường (Sentiment Analysis): Chấm điểm cảm xúc (tích cực/tiêu cực/trung tính) của tin tức tác động lên mã cổ phiếu.
FR8: Tổng hợp & Cảnh báo Rủi ro: Phát hiện các chuỗi sự kiện rủi ro/bất thường và gửi cảnh báo qua Telegram.
FR9: Trợ lý Truy vấn (Q&A Bot): Giao diện chat cho phép người dùng hỏi trực tiếp và AI sẽ dùng Knowledge Graph để trả lời.
FR10: Giao diện cơ bản (MVP Web UI): Cung cấp một Web Dashboard trực quan hóa Knowledge Graph, biểu đồ kỹ thuật và tin tức tổng hợp.

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

UX-DR1: Bảng màu thương hiệu & Trạng thái: Áp dụng các Token màu nền tối (`#0B0E11`), thẻ card (`#1E2329`), màu nhấn chính Binance Yellow (`#FCD535`), màu trạng thái `trading-up` (`#0ECB81`) và `trading-down` (`#F6465D`).
UX-DR2: Typography hiển thị: Áp dụng font Inter cho văn bản thông thường và JetBrains Mono/IBM Plex Mono cho dữ liệu số, Ticker, log lỗi.
UX-DR3: Giao diện thẻ & Border: Triển khai hệ thống CSS/Tailwind theo Layout Grid 12 cột, dùng viền hairline 1px (`#2B3139`) phân tách thay cho đổ bóng mờ kính.
UX-DR4: Các UI Component cơ bản: Xây dựng các component tái sử dụng (button-primary, button-secondary, dashboard-card, input-field) dựa trên thiết kế tokens.
UX-DR5: Status Badge Component: Xây dựng component Badge với 2 trạng thái thành công/lỗi rõ ràng để thông báo hoạt động crawler và pipeline.

### FR Coverage Map

{{requirements_coverage_map}}

## Epic List

{{epics_list}}
