---
stepsCompleted: [1, 2, 3, 4, 5, 6, 7, 8]
inputDocuments: ["_bmad-output/planning-artifacts/prds/prd-quantyFin-ai-2026-06-03/prd.md"]
workflowType: 'architecture'
project_name: 'quantyFin-ai'
user_name: 'Jeremy Nguyen'
date: '2026-06-04'
lastStep: 8
status: 'complete'
completedAt: '2026-06-05T08:48:00+07:00'
---

# Architecture Decision Document

_This document builds collaboratively through step-by-step discovery. Sections are appended as we work through each architectural decision together._

## Project Context Analysis

### Requirements Overview

**Functional Requirements:**
- **Data Ingestion & Processing:** Hệ thống crawler và API fetcher ổn định, chạy theo lịch (daily batch processing).
- **Cổng lọc tối ưu chi phí (Cost-Control Pre-filter):** Data Pipeline bắt buộc phải có một tầng xử lý logic thuần túy (thuật toán cổ điển, keyword matching) đóng vai trò làm màng lọc "Zero-Cost". Tầng này sẽ loại bỏ các tin rác trước khi dữ liệu được chuyển đến LLM Engine, giúp bảo vệ ngân sách API một cách chủ động.
- **AI/NLP Engine:** Pipeline xử lý ngôn ngữ tự nhiên nhiều bước: Trích xuất thực thể -> Tạo mối quan hệ -> Đánh giá cảm xúc. Đòi hỏi cơ chế gọi LLM linh hoạt.
- **Storage:** Hệ thống lưu trữ đa mô hình: GraphDB để lưu cấu trúc tri thức và VectorDB cho semantic search (RAG).
- **Delivery:** Hệ thống cảnh báo (push notifications) qua Telegram và Dashboard web để trực quan hóa dữ liệu.

**Non-Functional Requirements:**
- Tối ưu chi phí là yếu tố then chốt định hình kiến trúc (phân luồng xử lý LLM theo chi phí).
- Kiến trúc module hóa (dễ thêm/sửa đổi nguồn tin tức mới độc lập).
- Bảo mật mức nội bộ (cơ chế xác thực cơ bản cho Web Dashboard và Telegram bot hạn chế người dùng).

**Scale & Complexity:**
Dự án có quy mô nội bộ, lưu lượng truy cập thấp nhưng độ phức tạp kỹ thuật ở mức trung bình do kết hợp nhiều luồng xử lý dữ liệu phức tạp (Scraping + GraphDB + LLM).

- Primary domain: Data Engineering, AI Backend, Web/Bot MVP
- Complexity level: Medium
- Estimated architectural components: 4 (Data Ingestion, AI Engine, Graph/Vector Storage, UI/Bot Gateway)

### Technical Constraints & Dependencies

- **Hợp nhất Lưu trữ (Storage Consolidation):** Để bảo vệ tài nguyên của máy chủ (RAM/CPU), kiến trúc bắt buộc phải tìm giải pháp hợp nhất Graph Database và Vector Database vào chung một engine duy nhất (ví dụ: PostgreSQL hoặc Neo4j), nghiêm cấm việc triển khai rời rạc nhiều DB engine khác nhau.
- **Ràng buộc Hệ sinh thái:** Do tính chất xử lý dữ liệu và AI, lõi hệ thống bắt buộc phải sử dụng hệ sinh thái Python. Tuy nhiên, việc tách biệt khối xử lý dữ liệu (AI Engine) và khối giao diện (Web/Bot) là cần thiết để đảm bảo sự cố crawler không làm gián đoạn trải nghiệm người dùng.
- **Ràng buộc Triển khai (Deployment):** Hệ thống phải được thiết kế để có thể chạy trọn vẹn trên một máy chủ duy nhất (Single-node) thông qua containerization (Docker Compose) nhằm tối ưu chi phí hạ tầng (VPS giá rẻ), thay vì các kiến trúc phân tán đám mây đắt đỏ.
- Phụ thuộc vào tính ổn định của các nguồn báo chí (rủi ro thay đổi DOM/chống bot) và API bên thứ 3 (vn-stock).
- Ràng buộc chi phí API của LLM (cần cơ chế caching, batching, rate-limiting để kiểm soát token).

### Cross-Cutting Concerns Identified

- **Cost Management:** Tối ưu hóa số lượng token gọi LLM và chi phí hạ tầng.
- **Sự cố cô lập (Fault Isolation):** Sự thất bại của các tác vụ chạy ngầm (batch jobs cào tin tức, gọi API LLM) không được phép ảnh hưởng đến thời gian phản hồi (uptime) của Telegram Bot và Web Dashboard.
- **Data Quality & Resilience:** Cơ chế xử lý lỗi và retry khi crawler thất bại hoặc format website thay đổi.
- **Task Scheduling:** Quản lý lịch chạy daily batch đảm bảo tính toàn vẹn dữ liệu.

## Starter Template Evaluation

### Primary Technology Domain

Full-stack Web Application (React Frontend + FastAPI Backend) kết hợp AI/Data Pipeline.

### Starter Options Considered

- **Full Stack FastAPI Template (tiangolo/full-stack-fastapi-template)**: Là template chuẩn mực của ngành do chính tác giả FastAPI tạo ra, tích hợp sẵn FastAPI, PostgreSQL (SQLModel) và Docker Compose.
- **Custom Vite + React + shadcn/ui**: Theo chuẩn năm 2026, thay vì dùng các boilerplate Frontend khổng lồ dễ gây "phình to" code (bloatware), cộng đồng ưu tiên tự tạo mới bằng Vite kết hợp Tailwind v4 và `shadcn/ui` CLI để hoàn toàn làm chủ các component giao diện.

### Selected Starter: Custom Full-Stack Integration (FastAPI Backend + Vite/React Frontend)

**Rationale for Selection:**
Chúng ta sẽ áp dụng cách tiếp cận "Hybrid" (Kết hợp) để tối ưu hóa sự linh hoạt:
- **Backend:** Lấy cảm hứng cấu trúc từ `tiangolo/full-stack-fastapi-template` để có nền tảng vững chắc cho FastAPI, kết nối PostgreSQL (dữ liệu quan hệ) và Neo4j (Graph & Vector data). Sử dụng `uv` (trình quản lý gói Python hiện đại và siêu nhanh) thay thế cho pip/poetry.
- **Frontend:** Khởi tạo dự án Vite sạch sẽ với React TypeScript, cài đặt Tailwind CSS v4 mới nhất và cấu hình `shadcn/ui` để xây dựng giao diện Dashboard chuyên nghiệp mà không bị thừa code.

**Initialization Command:**

*Backend (Python/FastAPI):*
```bash
mkdir backend && cd backend
uv init
uv add fastapi uvicorn sqlmodel psycopg2-binary neo4j pydantic-settings
```

*Frontend (React/Vite):*
```bash
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install tailwindcss @tailwindcss/vite
npx shadcn@latest init
```

**Architectural Decisions Provided by Starter:**

**Language & Runtime:**
- Backend: Python (quản lý môi trường siêu tốc bằng công cụ `uv`).
- Frontend: TypeScript chạy trên Node.js.

**Styling Solution:**
Tailwind CSS v4 (cấu hình qua Vite plugin cực gọn) kết hợp hệ thống component của shadcn/ui (dựa trên Radix UI).

**Build Tooling:**
- Frontend: Vite (Build cực nhanh, Hot Module Replacement tức thì).
- Backend: `uvicorn` làm ASGI server.

**Code Organization & Infrastructure:**
- Tách biệt hoàn toàn thư mục `frontend` và `backend`. 
- **Yêu cầu bắt buộc:** Phải tự cấu hình `docker-compose.yml` từ đầu để liên kết mạng nội bộ cho Frontend, Backend, Postgres, và Neo4j.

**Security & Authentication (Tối giản):**
Để duy trì tốc độ phát triển cực nhanh cho dự án MVP nội bộ này, chúng ta sẽ không xây dựng hệ thống quản lý user cồng kềnh. Thay vào đó, áp dụng cơ chế xác thực tối giản dùng `OAuth2PasswordBearer` có sẵn của FastAPI.

**Testing Strategy:**
Việc chọn Custom Starter đồng nghĩa với việc không có sẵn test tự động. **Yêu cầu bắt buộc:** Ticket triển khai đầu tiên (Implementation Story số 1) phải bao gồm thiết lập môi trường Pytest (Backend) và Playwright (Frontend E2E).

**Note:** Việc chạy các lệnh khởi tạo này và cấu hình cơ sở hạ tầng nền tảng sẽ là công việc đầu tiên khi bước vào giai đoạn thực thi.

## Core Architectural Decisions

### Decision Priority Analysis

**Critical Decisions (Block Implementation):**
- **Data Architecture:** Sử dụng SQLModel + Alembic
- **AI Orchestration:** Sử dụng CrewAI kết hợp LiteLLM làm Gateway

**Important Decisions (Shape Architecture):**
- **Frontend State & Routing:** TanStack Router + TanStack Query + Zustand

**Deferred Decisions (Post-MVP):**
- Hệ thống phân quyền chi tiết Role-based Access Control (Tạm thời dùng `OAuth2PasswordBearer` cơ bản).

### Data Architecture

- **Category:** Database ORM & Migrations
- **Decision:** SQLModel + Alembic
- **Version:** SQLModel `v0.0.38` (2026)
- **Rationale:** Kết hợp Pydantic và SQLAlchemy thành 1 lớp model duy nhất, giảm 50% thời gian code cho FastAPI.
- **Affects:** Data Ingestion, AI Engine, Backend API

### Authentication & Security

- **Category:** Authentication Method
- **Decision:** Tối giản với `OAuth2PasswordBearer` (Tích hợp sẵn của FastAPI)
- **Rationale:** Giữ vững tốc độ phát triển cho MVP nội bộ, tránh lãng phí thời gian vào các bộ boilerplate Auth quá cồng kềnh.
- **Affects:** Frontend Dashboard, Backend API

### API & Communication Patterns

- **Category:** Multi-Agent Orchestration & LLM Gateway
- **Decision:** CrewAI + LiteLLM
- **Version:** CrewAI `v1.14.6`, LiteLLM `v1.87.0`
- **Rationale:** 
  - **CrewAI** chia vai trò Agent (Scraper, Analyst, Reviewer...) rất tự nhiên và dễ xây dựng luồng nghiệp vụ tin tức.
  - **LiteLLM** đứng sau lưng làm nhiệm vụ kiểm soát Rate Limit, tính toán số tiền token đã đốt và chuẩn hóa API (có thể dễ dàng đổi từ GPT-4 sang Claude 3.5 hay Gemini).
- **Affects:** AI/NLP Engine

### Frontend Architecture

- **Category:** Routing, Data Fetching & State
- **Decision:** TanStack Router + TanStack Query + Zustand
- **Version:** TanStack hệ `v1.170` (2026)
- **Rationale:** TanStack Router mang lại Type-safety 100% từ URL xuống Component. Kết hợp TanStack Query để gọi API và cache mượt mà. Phù hợp chuẩn 2026.
- **Affects:** React Web Dashboard

### Infrastructure & Deployment

- **Category:** Hosting Strategy
- **Decision:** Docker Compose (Single-node VPS)
- **Rationale:** Chi phí rẻ nhất cho MVP nội bộ. Gom nhóm toàn bộ (FastAPI, React, Postgres, Neo4j, CrewAI script) vào chung một mạng nội bộ ảo trên cùng 1 server.

### Decision Impact Analysis

**Implementation Sequence:**
1. Khởi tạo Docker Compose base (Network nội bộ, Postgres, Neo4j).
2. Setup FastAPI + SQLModel + Alembic.
3. Setup Vite React + Tailwind v4 + shadcn/ui.
4. Tích hợp TanStack Router & Query vào Frontend.
5. Cài đặt CrewAI + LiteLLM thiết lập AI Engine.

**Cross-Component Dependencies:**
- Frontend phụ thuộc chặt chẽ vào OpenAPI schema (JSON) sinh ra từ FastAPI để đảm bảo Type-safe cho các lời gọi hàm.
- CrewAI agents need kết nối đồng thời với Neo4j (để đọc Knowledge Graph) và LiteLLM (để suy luận).

## Implementation Patterns & Consistency Rules

### Pattern Categories Defined

**Critical Conflict Points Identified:**
Có 5 khu vực xung đột chính mà các AI agent có thể tự đưa ra các quyết định khác nhau nếu không được quy định đồng nhất:
1. Quy tắc đặt tên (Postgres vs Neo4j vs Codebase)
2. Cấu trúc Schema Response của API
3. Cơ chế xử lý lỗi toàn cục và truy vết sự cố (Tracing)
4. Luồng cập nhật State trong React
5. Tổ chức thư mục và định vị File kiểm thử

### Naming Patterns

**Database Naming Conventions:**
*   **PostgreSQL (Relational):**
    *   Tên bảng: Số nhiều, viết thường dạng snake_case (ví dụ: `news_articles`, `stock_prices`).
    *   Tên cột: snake_case (ví dụ: `article_id`, `sentiment_score`).
    *   Khóa ngoại (Foreign Key): Định dạng `singular_table_name_id` (ví dụ: `news_article_id`).
    *   Tên Index: `idx_<table_name>_<column_name>` (ví dụ: `idx_news_articles_published_at`).
*   **Neo4j (Graph Database):**
    *   Nhãn Node (Node Labels): Viết hoa chữ cái đầu PascalCase (ví dụ: `(:Stock)`, `(:NewsArticle)`, `(:Entity)`).
    *   Kiểu Quan hệ (Relationship Types): Viết hoa toàn bộ phân cách bằng dấu gạch dưới UPPER_SNAKE_CASE (ví dụ: `[:MENTIONS]`, `[:RELATED_TO]`, `[:SENTIMENT_OF]`).
    *   Thuộc tính (Properties): Viết thường chữ đầu camelCase (ví dụ: `tickerSymbol`, `sentimentScore`, `processedAt`).

**API Naming Conventions:**
*   REST Endpoints: Dùng danh từ số nhiều, viết thường snake-case/kebab-case phân cách (ví dụ: `/api/v1/news-articles`, `/api/v1/stocks`).
*   Định dạng Route Parameter: Kiểu FastAPI dùng dấu ngoặc nhọn `{id}` (ví dụ: `/api/v1/stocks/{ticker}`).
*   Định dạng Query Parameter: camelCase (ví dụ: `/api/v1/news-articles?publishedAfter=...`).
*   Header tự định nghĩa: kebab-case tiêu chuẩn (ví dụ: `X-Trace-Id`).

**Code Naming Conventions:**
*   **React/TypeScript (Frontend):**
    *   Component: PascalCase (ví dụ: `StockChart.tsx`, `SentimentBadge.tsx`).
    *   Tên file: PascalCase đối với các component React. camelCase đối với các file chức năng, helper, route (ví dụ: `apiClient.ts`, `formatters.ts`).
    *   Function: camelCase (ví dụ: `fetchStockData`).
    *   Variable: camelCase (ví dụ: `isLoading`, `stockData`).
*   **Python/FastAPI (Backend):**
    *   Modules & Packages: snake_case (ví dụ: `core/`, `api/v1/`).
    *   Class: PascalCase (ví dụ: `NewsArticleService`).
    *   Function & Variable: snake_case (ví dụ: `get_news_by_id`, `sentiment_score`).

### Structure Patterns

**Project Organization:**
*   Toàn bộ test phải nằm trong các thư mục kiểm thử tập trung độc lập: `backend/tests/` đối với Python, và `frontend/tests/` đối với React/Playwright E2E. Nghiêm cấm đặt file test co-locate chung với mã nguồn để giữ codebase gọn gàng nhất.
*   Mã nguồn dùng chung (Shared Utilities) được phân tách rõ ràng tại `backend/app/core/` và `frontend/src/lib/utils/`.

**File Structure Patterns:**
*   Biến môi trường và cấu hình cấu trúc dự án bắt buộc phải được đọc và kiểm thử từ các file tập trung: `backend/app/core/config.py` (sử dụng `Pydantic-Settings` để map từ `.env`) và `frontend/src/config/` (đọc từ Vite env `import.meta.env`).

### Format Patterns

**API Response Formats:**
*   Tất cả các API endpoint trả về dữ liệu đều phải được bọc trong một Schema thống nhất.
*   Định nghĩa TypeScript của Wrapper (`ApiResponse<T>`):
    ```typescript
    interface ApiResponse<T> {
      data: T | null;
      error: {
        code: string;
        message: string;
        details?: any;
      } | null;
      meta?: {
        trace_id: string;
        [key: string]: any;
      };
    }
    ```
*   **Success Response:** Dữ liệu ở trường `data`, trường `error` nhận giá trị `null`.
*   **Error Response:** Trường `data` nhận giá trị `null`, thông tin lỗi chi tiết hiển thị ở `error` kèm `code` phân loại, `message` hiển thị cho người dùng, và `details` cho lỗi kiểm thử.

**Data Exchange Formats:**
*   Định dạng JSON: API truyền nhận dữ liệu theo dạng `camelCase` ở cả chiều Request và Response. FastAPI backend sẽ tự động serialize/deserialize (từ model snake_case nội bộ của Python sang camelCase ở biên kết nối).
*   Định dạng Date/Time: Sử dụng chuỗi ISO 8601 kèm múi giờ (ví dụ: `2026-06-04T12:00:00+07:00`).

### Communication Patterns

**Event Systems & Agent Coordination:**
*   Giao tiếp giữa các Agent trong CrewAI: Tuân thủ cấu hình strictly typed Pydantic models. Tránh gửi chuỗi hoặc dictionary thô không định dạng để tránh sai lệch thông tin xử lý.
*   Định dạng Log: Cả Backend và Frontend sử dụng cấu trúc JSON log ghi ra stdout, bắt buộc chứa các trường thông tin: `trace_id`, `timestamp`, `log_level`, `module`, và `message`.

**State Management Patterns:**
*   React State: Quản lý qua Zustand thông qua các thay đổi bất biến (immutable state updates). Tên Action cập nhật trạng thái phải bắt đầu bằng tiền tố `set<StateName>` hoặc biểu diễn rõ ràng hành động chuyển đổi trạng thái (ví dụ: `toggleSidebar`).

### Process Patterns

**Error Handling & Tracing:**
*   Bộ xử lý lỗi FastAPI toàn cục (Global Exception Handler): Đảm bảo bắt mọi ngoại lệ chưa được xử lý và trả về cấu trúc `ApiResponse<null>` với HTTP Status `500 Internal Server Error`.
*   **Bắt buộc có Trace ID:** Phản hồi JSON từ Exception Handler phải chứa `trace_id` trong trường `meta` để hỗ trợ debugging nhanh:
    ```json
    {
      "data": null,
      "error": {
        "code": "INTERNAL_SERVER_ERROR",
        "message": "Đã xảy ra lỗi hệ thống. Vui lòng liên hệ quản trị viên."
      },
      "meta": {
        "trace_id": "err_5f3b7c8a..."
      }
    }
    ```
*   Mỗi request gửi tới API sẽ được gán một `trace_id` ngẫu nhiên (UUIDv4) qua middleware. ID này được đưa vào ngữ cảnh logging và đính kèm trong header phản hồi cũng như payload lỗi.

**Loading States:**
*   Sử dụng cờ `isLoading`/`isFetching` từ TanStack Query ở cấp độ component cục bộ để điều phối trạng thái tải dữ liệu, kết hợp với các component Skeleton từ `shadcn/ui`. Tránh dùng cơ chế Loading Spinner toàn màn hình khóa UI trừ khi hệ thống đang khởi tạo ứng dụng.

### Enforcement Guidelines

**Tất cả AI Agent bắt buộc phải tuân thủ:**
1. Kiểm tra các class SQLModel sẵn có trước khi định nghĩa model mới để tránh bị trùng lặp khai báo bảng dữ liệu.
2. Mọi API endpoint mới phải khai báo đúng tiền tố `/api/v1` và bắt buộc bọc qua middleware xử lý trace_id.
3. Đặt đúng chuẩn hoa/thường cho cơ sở dữ liệu Neo4j: Nhãn Node (PascalCase), Quan hệ (UPPER_SNAKE_CASE).

### Pattern Examples

**Ví dụ đúng:**
*Cypher query chuẩn trong Neo4j:*
```cypher
MATCH (s:Stock {tickerSymbol: "VNM"})-[r:MENTIONS]-(a:NewsArticle) RETURN s, r, a
```

*Phản hồi API báo lỗi đúng quy chuẩn:*
```json
{
  "data": null,
  "error": {
    "code": "STOCK_NOT_FOUND",
    "message": "Không tìm thấy thông tin cổ phiếu có mã VIC."
  },
  "meta": {
    "trace_id": "9a1b2c3d-4e5f-6a7b-8c9d-0e1f2a3b4c5d"
  }
}
```

**Anti-Patterns (Mẫu phản thiết kế cần tránh):**
*   Trả về trực tiếp SQLModel thô hoặc Dictionary tự định nghĩa từ router mà không qua `ApiResponse` wrapper.
*   Đặt tên quan hệ trong Neo4j dạng camelCase hoặc viết thường (ví dụ: `[:mentions]` hoặc `[:mentionsStock]`).
*   Bỏ qua việc thêm `trace_id` trong header/meta phản hồi lỗi hoặc tự định nghĩa log format tùy tiện.

## Project Structure & Boundaries

### Complete Project Directory Structure

```text
quantyFin-ai/
├── README.md
├── docker-compose.yml
├── .env.example
├── .gitignore
├── .github/
│   └── workflows/
│       └── ci.yml
├── docker/
│   ├── backend.Dockerfile
│   └── frontend.Dockerfile
├── backend/
│   ├── pyproject.toml
│   ├── uv.lock
│   ├── alembic.ini
│   ├── app/
│   │   ├── main.py
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py
│   │   │   ├── db.py          # Postgres SQLModel engine & session
│   │   │   ├── neo4j.py       # Neo4j connection helper
│   │   │   ├── security.py    # Basic auth / JWT
│   │   │   ├── logging.py     # Custom JSON logger
│   │   │   └── exceptions.py  # Hệ thống lỗi tùy chỉnh (CrawlerException, SystemException...)
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── deps.py        # API dependencies (current_user, db_session)
│   │   │   └── v1/
│   │   │       ├── __init__.py
│   │   │       ├── auth.py    # Login / token routes
│   │   │       ├── news.py    # News queries & manual trigger
│   │   │       └── stocks.py  # Stock analysis endpoints
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── news.py        # News articles & sentiment tables
│   │   │   ├── stock.py       # Stock tickers & prices tables
│   │   │   └── user.py        # Admin users tables
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── crawler.py     # Orchestrator chính điều phối scraping
│   │   │   ├── scrapers/      # Phân chia parser riêng biệt cho từng nguồn báo để cô lập lỗi
│   │   │   │   ├── __init__.py
│   │   │   │   ├── base.py    # Lớp Base Scraper (mặc định timeout = 300s, log HTML lỗi)
│   │   │   │   ├── vnexpress.py
│   │   │   │   ├── cafef.py
│   │   │   │   ├── vneconomy.py
│   │   │   │   ├── vietstock.py
│   │   │   │   ├── tuoitre.py
│   │   │   │   ├── thanhnien.py
│   │   │   │   └── vnbusiness.py
│   │   │   ├── stock_data.py  # vn-stock API wrapper
│   │   │   ├── jobs.py        # Quản lý trạng thái phân tích ngầm (Background Tasks)
│   │   │   └── neo4j_sync.py  # Sync rels & nodes từ Postgres sang Neo4j
│   │   └── agents/
│   │       ├── __init__.py
│   │       ├── gateway.py     # LiteLLM router config
│   │       ├── crew.py        # CrewAI orchestration definition
│   │       ├── agents.py      # Spec for Scraper, Analyst, Reviewer
│   │       └── tasks.py       # Definition of tasks for agents
│   ├── alembic/
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   └── versions/
│   ├── data/
│   │   └── failed_scrapes/    # Lưu trữ HTML lỗi khi cào tin để debug (được ignore khỏi git)
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py
│       ├── api/
│       ├── services/
│       └── agents/
└── frontend/
    ├── package.json
    ├── package-lock.json
    ├── tsconfig.json
    ├── vite.config.ts
    ├── postcss.config.js
    ├── tailwind.config.js
    ├── index.html
    ├── scripts/
    │   └── generate-client.ts # Script auto-gen Types từ OpenAPI JSON của Backend
    ├── src/
    │   ├── main.tsx
    │   ├── index.css
    │   ├── config/
    │   │   └── index.ts
    │   ├── routes/
    │   │   ├── __root.tsx
    │   │   ├── index.tsx      # Welcome / Login page
    │   │   └── dashboard/
    │   │       ├── index.tsx  # Dashboard layout
    │   │       ├── news.tsx   # News feed / Graph visualization
    │   │       └── stocks.tsx # Stock overview & details
    │   ├── components/
    │   │   ├── ui/            # shadcn/ui base components
    │   │   │   ├── button.tsx
    │   │   │   ├── card.tsx
    │   │   │   ├── dialog.tsx
    │   │   │   └── skeleton.tsx
    │   │   ├── dashboard/
    │   │   │   ├── stock-chart.tsx
    │   │   │   ├── news-card.tsx
    │   │   │   └── kg-graph.tsx  # Neo4j visualization (D3/Vis.js)
    │   │   └── shared/
    │   │       ├── layout.tsx
    │   │       └── error-boundary.tsx # Bọc các component UI để tránh sập toàn trang
    │   ├── lib/
    │   │   ├── apiClient.ts   # Axios/Fetch setup với trace_id middleware
    │   │   └── utils.ts       # tailwind-merge helper
    │   ├── hooks/
    │   │   ├── useAuth.ts
    │   │   ├── useNews.ts     # TanStack Query logic
    │   │   └── useStocks.ts
    │   ├── store/
    │   │   └── useAuthStore.ts # Zustand global auth state
    │   └── types/
    │       └── api.ts         # File tự động sinh (Không sửa thủ công)
    └── tests/
        └── dashboard.spec.ts   # Playwright E2E tests
```

### Architectural Boundaries

**API Boundaries:**
*   **External API Interface:** Giao tiếp Client-Server thông qua RESTful API định nghĩa ở `backend/app/api/v1/`. Mọi dữ liệu đi qua biên giới này bắt buộc tuân theo định dạng JSON camelCase và bọc bởi `ApiResponse<T>`.
*   **Telegram Bot Boundary:** Telegram Bot hoạt động như một Delivery client độc lập, chỉ gọi API nội bộ thông qua client HTTP bảo mật để push thông tin cảnh báo, không truy cập trực tiếp vào databases.

**Component Boundaries:**
*   **Frontend State vs. UI Components:** UI components (`frontend/src/components/`) là các thành phần hiển thị (presentational). Trạng thái nghiệp vụ và giao tiếp mạng được cô lập trong `frontend/src/hooks/` (dữ liệu từ API) và `frontend/src/store/` (trạng thái UI, phiên làm việc).
*   **Routing Boundary:** Định nghĩa các Route bằng TanStack Router (`frontend/src/routes/`), tích hợp sẵn các Loader để tải trước dữ liệu, đảm bảo việc chuyển trang không bị gián đoạn hoặc lỗi trạng thái Type-safe.

**Service Boundaries:**
*   **Zero-Cost Filter Boundary:** Dữ liệu tin tức thô sau khi cào bằng `crawler.py` bắt buộc phải đi qua hàm tiền lọc logic thuần túy (Classic NLP, regex, key matching) trước khi đẩy vào luồng AI. Tầng AI Agent nằm sau ranh giới này để cô lập chi phí.
*   **AI & Job Execution Boundary:** API endpoints nhận yêu cầu crawler/phân tích sẽ lập tức trả về HTTP Status `202 Accepted` kèm `job_id` thông qua `services/jobs.py` (quản lý trạng thái thông qua DB), sau đó đẩy luồng chạy của CrewAI/Neo4j Sync vào `BackgroundTasks` tích hợp sẵn của FastAPI. Frontend sử dụng TanStack Query thực hiện kỹ thuật polling trạng thái để hiển thị tiến trình mượt mà, tránh việc kết nối API bị treo hoặc timeout.
*   **Type-safety Boundary:** Frontend tích hợp script `generate-client.ts` tự động đọc schema từ Backend và ghi đè vào `src/types/api.ts` mỗi khi chạy môi trường dev, đảm bảo 100% type-safety từ API Router đến Frontend Client.
*   **AI Engine Boundary:** `agents/` là module độc lập với API, giao tiếp qua LiteLLM gateway. API Endpoint chỉ trigger luồng chạy của CrewAI và nhận kết quả trả về, không can tiệp vào cách thức hoạt động nội bộ của Crew.

**Data Boundaries:**
*   **PostgreSQL Boundary:** SQLModel đại diện cho dữ liệu quan hệ (Người dùng, Cấu hình, Tin tức, Giá cổ phiếu lịch sử). Mọi truy vấn phải đi qua SQLAlchemy session.
*   **Neo4j Boundary:** Chứa dữ liệu thực thể phi quan hệ (Knowledge Graph) và Vector Embeddings cho RAG. Việc đồng bộ dữ liệu từ Postgres sang Neo4j được xử lý thông qua `services/neo4j_sync.py` theo mô hình Event hoặc Batch, không ghi trực tiếp Neo4j từ API Router chính.

### Requirements to Structure Mapping

**Feature/Epic Mapping:**
*   **Crawler & Data Ingestion (Zero-Cost filter):**
    *   Mã nguồn logic: `backend/app/services/crawler.py` & `backend/app/services/stock_data.py`.
    *   Kiểm thử: `backend/tests/services/test_crawler.py`.
*   **AI Engine & Sentiment Extraction (CrewAI + LiteLLM):**
    *   Mã nguồn logic: `backend/app/agents/`.
    *   Kiểm thử: `backend/tests/agents/test_crew.py`.
*   **Knowledge Graph & Vector Sync:**
    *   Mã nguồn logic: `backend/app/services/neo4j_sync.py` & `backend/app/core/neo4j.py`.
*   **Web Dashboard UI:**
    *   Mã nguồn logic: `frontend/src/routes/dashboard/` & `frontend/src/components/dashboard/`.
    *   Kiểm thử: `frontend/tests/dashboard.spec.ts`.

**Cross-Cutting Concerns:**
*   **Authentication:**
    *   Backend: `backend/app/core/security.py` & `backend/app/api/deps.py`.
    *   Frontend: `frontend/src/store/useAuthStore.ts` & `frontend/src/routes/index.tsx`.
*   **Global Exception & Tracing (`trace_id`):**
    *   Backend Exception Handler & Logging: `backend/app/core/logging.py` & `backend/app/main.py`.
    *   Frontend API client integration: `frontend/src/lib/apiClient.ts`.

### Integration Points

**Internal Communication:**
*   FastAPI backend kết nối PostgreSQL thông qua SQLModel engine (`backend/app/core/db.py`) và Neo4j thông qua Bolt driver (`backend/app/core/neo4j.py`).
*   Frontend gọi API Backend thông qua Axios Client định nghĩa tại `frontend/src/lib/apiClient.ts`. Mọi request tự động chèn JWT token từ Zustand store vào Header `Authorization`.

**External Integrations:**
*   **LiteLLM Gateway:** Đóng vai trò proxy cho mọi LLM calls từ CrewAI agents, quản lý rate limit và token usage.
*   **Stock API (vn-stock):** Lấy dữ liệu giá trị giao dịch, ticker thực tế từ sàn chứng khoán Việt Nam qua thư viện python.
*   **Telegram Bot API:** Push tin nhắn cảnh báo phân tích từ Backend tới kênh Telegram được định sẵn.

### File Organization Patterns

*   **Configuration Files:** Đặt ở thư mục gốc của từng phần dự án (`backend/` và `frontend/`). File `.env` lưu trữ cục bộ trên VPS và không được commit lên Git (dùng `.env.example` để mô tả cấu trúc biến).
*   **Test Organization:** Kiểm thử Backend dùng `pytest` được viết trong `backend/tests/`, có cấu hình fixture dùng chung tại `conftest.py`. Kiểm thử Frontend dùng `Playwright` đặt trong `frontend/tests/`.
*   **Asset Organization:** Ảnh tĩnh, logo đặt tại `frontend/public/assets/`. Các component đồ họa động dùng d3/vis.js để dựng tại runtime không lưu trữ tài nguyên tĩnh lớn.

## Architecture Validation Results

### Coherence Validation ✅

**Decision Compatibility:**
Tất cả các lựa chọn công nghệ (FastAPI, SQLModel, Alembic, CrewAI, LiteLLM ở Backend và React, Vite, TanStack Query/Router, Zustand ở Frontend) tương thích hoàn toàn. Phiên bản được kiểm chứng đảm bảo không xảy ra xung đột dependency. Việc tích hợp Docker Compose ở mức Root giúp liên kết toàn bộ tài nguyên cục bộ một cách tối giản nhất.

**Pattern Consistency:**
Các mẫu thiết kế (như quy tắc đặt tên Neo4j PascalCase/UPPER_SNAKE_CASE, kiểu dữ liệu trả về `ApiResponse<T>`, và middleware tự sinh Client Types) hỗ trợ chặt chẽ cho sự nhất quán mã nguồn giữa nhiều AI Agent phát triển song song.

**Structure Alignment:**
Cấu trúc thư mục được phân rã thành các dịch vụ độc lập (`backend/` và `frontend/`). Ranh giới giữa luồng xử lý đồng bộ (API Endpoints) và luồng bất đồng bộ tốn tài nguyên (Crawler, AI Agent) được phân định rõ thông qua `BackgroundTasks` và dịch vụ `jobs.py`.

### Requirements Coverage Validation ✅

**Epic/Feature Coverage:**
Hệ thống cào và tiền lọc (Zero-Cost Filter), trích xuất thông tin bằng AI (CrewAI + LiteLLM), lưu trữ Knowledge Graph (Neo4j) và cập nhật đồ thị trực quan đều có các file/module tương ứng chịu trách nhiệm thiết kế.

**Functional Requirements Coverage:**
*   **Zero-Cost Filter:** Xử lý qua lớp cào cơ bản `backend/app/services/scrapers/`.
*   **AI Engine:** Xử lý qua `backend/app/agents/` gọi qua LiteLLM Gateway.
*   **Graph/Vector Storage:** Xử lý qua `backend/app/core/neo4j.py` và Postgres (SQLModel).
*   **Telegram & Dashboard:** Xử lý qua Endpoint của FastAPI và Web App.

**Non-Functional Requirements Coverage:**
*   **Tối ưu hóa chi phí:** LiteLLM kiểm soát ngân sách token, Zero-Cost filter giảm số lượng tin tức cần gửi cho AI. Triển khai Single VPS qua Docker Compose giảm chi phí vận hành.
*   **Cô lập lỗi (Fault Isolation):** Lỗi của crawler hoặc Neo4j không ảnh hưởng đến API chính hoặc giao diện người dùng nhờ lưu trạng thái job ngầm và giao dịch độc lập.

### Implementation Readiness Validation ✅

**Decision Completeness:**
Mọi quyết định quan trọng (ORM, Auth, State Management, LLM Gateway, Triển khai) đã được định hình và thống nhất cụ thể kèm theo phiên bản.

**Structure Completeness:**
Cây thư mục chi tiết đến cấp độ file nghiệp vụ chính (`main.py`, `generate-client.ts`, `exceptions.py`, `error-boundary.tsx`, v.v.) giúp Agent biết chính xác nơi cần đặt code mới.

**Pattern Completeness:**
Các quy tắc đặt tên Database, API, định dạng JSON, Trace ID toàn cục, cơ chế Retry và xử lý Timeout mặc định cho Crawler (300s) đã được hoàn thiện đầy đủ.

### Gap Analysis Results

*   **Critical Gaps (Rủi ro chặn triển khai):** *Không có.*
*   **Important Gaps (Cần hoàn thiện khi triển khai):** Cấu hình ban đầu của Telegram Bot token và LLM API Keys (sẽ được định nghĩa thông qua file `.env.example` và tải từ biến môi trường của hệ thống VPS).
*   **Nice-to-Have Gaps (Cải tiến tùy chọn):** Cài đặt pre-commit hooks (Ruff và ESLint) để tự động kiểm duyệt định dạng code trước khi đẩy Git.

### Validation Issues Addressed
*   **Xử lý nghẽn API:** Đã giải quyết nguy cơ nghẽn API khi chạy CrewAI kéo dài bằng cơ chế Job polling phi đồng bộ (FastAPI BackgroundTasks).
*   **Bảo vệ hiệu năng DB khi Polling:** Bổ sung Index cho cột `status` và `job_id` của bảng `jobs` trong Postgres để tối ưu hóa truy vấn đọc lặp lại từ Frontend.
*   **Cơ chế phục hồi Neo4j:** Đã giải quyết rủi ro sập dây chuyền Neo4j bằng cơ chế trạng thái `SYNC_FAILED` và cơ chế Re-sync tự động/thủ công.
*   **Kiểm soát chi phí kiểm thử:** Bắt buộc thiết lập mock LiteLLM / LLM API trong các test suite (`backend/tests/conftest.py`) để ngăn chặn việc hao phí Token của nhà phát triển khi chạy CI/CD.
*   **Kiểm thử tải trọng Polling:** Lên kế hoạch viết script load-testing đơn giản bằng `k6` cho endpoint kiểm tra Job nhằm đảm bảo Single-node VPS chịu được tải khi nhiều admin truy cập đồng thời.
*   Đã thống nhất thời gian Job Timeout mặc định cho Crawler là 300 giây.

### Architecture Completeness Checklist

**Requirements Analysis**
- [x] Project context thoroughly analyzed
- [x] Scale and complexity assessed
- [x] Technical constraints identified
- [x] Cross-cutting concerns mapped

**Architectural Decisions**
- [x] Critical decisions documented with versions
- [x] Technology stack fully specified
- [x] Integration patterns defined
- [x] Performance considerations addressed

**Implementation Patterns**
- [x] Naming conventions established
- [x] Structure patterns defined
- [x] Communication patterns specified
- [x] Process patterns documented

**Project Structure**
- [x] Complete directory structure defined
- [x] Component boundaries established
- [x] Integration points mapped
- [x] Requirements to structure mapping complete

### Architecture Readiness Assessment

*   **Overall Status:** `READY FOR IMPLEMENTATION` (Tất cả 16 điều kiện kiểm tra đã đạt và không còn rủi ro chặn triển khai).
*   **Confidence Level:** `high` (Độ tự tin cao do ranh giới lỗi và cấu trúc Type-safety đã được xác định rất chi tiết).
*   **Key Strengths (Điểm mạnh cốt lõi):**
    1. Cơ chế lọc tin Zero-Cost giúp tiết kiệm ngân sách LLM tối đa.
    2. Kiến trúc xử lý bất đồng bộ gọn nhẹ không cần hàng đợi nặng nề.
    3. Type-safe chặt chẽ từ API xuống Frontend UI.
*   **Areas for Future Enhancement (Định hướng tương lai):** Tích hợp Redis và hàng đợi tin nhắn thực tế (như Celery hoặc RabbitMQ) nếu quy mô người dùng tăng mạnh vượt quá ngưỡng tải của Single-node VPS.

### Implementation Handoff

**AI Agent Guidelines:**
1. Tuyệt đối tuân thủ cây cấu trúc thư mục đã định dạng, không tự ý sinh file thô ngoài ranh giới quy định.
2. Mọi API router mới bắt buộc trả về kiểu dữ liệu thống nhất `ApiResponse<T>` và ghi log kèm `trace_id`.
3. Kiểm tra tính độc lập của các parser trong `services/scrapers/` để đảm bảo lỗi cào tin của một tờ báo không gây ảnh hưởng đến toàn bộ hệ thống.

**First Implementation Priority:**
Triển khai khởi tạo Docker Compose base chứa PostgreSQL (SQLModel + Alembic) và Neo4j cùng với Backend cấu hình middleware xử lý `trace_id`.


