# Tài liệu Kiến trúc Hệ thống (System Architecture)

QuantyFin là hệ thống trợ lý ảo thông minh hỗ trợ đầu tư tài chính, kết hợp phân tích cảm nhận tin tức bằng AI và mô hình hóa Đồ thị Tri thức (Knowledge Graph). Hệ thống gồm Backend API (FastAPI + PostgreSQL + Neo4j) và Frontend SPA (React 19 + TypeScript).

---

## 1. Tổng quan Kiến trúc (Executive Summary)

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React 19 SPA)                   │
│              Vite + TypeScript (strict mode)                 │
│              Port: 3000 (Docker) / 5173 (dev)               │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP/REST (JSON)
                           │ CORS: specific origins only
                           │ Security headers on all responses
┌──────────────────────────▼──────────────────────────────────┐
│                  Backend (FastAPI)                            │
│              Rate limiting (slowapi)                          │
│              Secret validation at startup                     │
│              Port: 8000                                      │
├─────────────────┬───────────────────────────────────────────┤
│  PostgreSQL 15  │  Neo4j 5 Community                        │
│  (port 5432)    │  (ports 7474, 7687)                       │
└─────────────────┴───────────────────────────────────────────┘
```

* **Kiến trúc:** Client-Server với REST API
* **Frontend:** Single Page Application (SPA) — Component-based, unidirectional data flow
* **Backend:** FastAPI (async Python) với structured exception handling và security middleware
* **Databases:** PostgreSQL (dữ liệu quan hệ) + Neo4j (Knowledge Graph)

---

## 2. Backend Architecture

### 2.1 Công nghệ

| Thành phần | Công nghệ | Phiên bản | Vai trò |
|:---|:---|:---:|:---|
| **Framework** | FastAPI | >=0.136.3 | REST API server (async) |
| **ORM** | SQLModel | >=0.0.38 | PostgreSQL interaction |
| **Graph DB Driver** | neo4j | >=6.2.0 | Neo4j Bolt connection |
| **Validation** | pydantic-settings | >=2.14.1 | Environment config validation |
| **Rate Limiting** | slowapi | >=0.1.9 | Request rate limiting |
| **Server** | uvicorn | >=0.49.0 | ASGI server |

### 2.2 Cấu trúc thư mục Backend

```
backend/
├── app/
│   ├── main.py              # App entry, middleware, routes
│   ├── core/
│   │   ├── config.py        # Settings + secret validation
│   │   ├── db.py            # PostgreSQL session
│   │   ├── neo4j.py         # Neo4j driver manager
│   │   ├── exceptions.py    # Exception hierarchy
│   │   └── logging.py       # Structured logging + trace IDs
│   └── api/v1/              # API route modules
├── tests/
│   ├── test_main.py         # Endpoint tests
│   └── test_security.py     # Security configuration tests
└── pyproject.toml           # Dependencies (uv)
```

### 2.3 Security Architecture

**Startup Validation** (`config.py`):
- `model_validator` kiểm tra `POSTGRES_PASSWORD`, `NEO4J_PASSWORD`, `SECRET_KEY`
- Raise `ValueError` nếu bất kỳ biến nào trống → app từ chối khởi động

**Middleware Stack** (thứ tự thực thi):
1. **Security Headers** — Inject 6 headers bảo mật vào mọi response
2. **Trace ID** — Gán `X-Trace-Id` cho request tracking/logging
3. **CORS** — Chỉ định origin cụ thể (không wildcard)

**Exception Handling**:
- `BaseAppException` → Structured error response (code, message, details)
- Generic `Exception` → Generic message, **không để lộ** internal details
- Tất cả exceptions kèm `trace_id` trong response metadata

**Rate Limiting** (slowapi):
- Key: `get_remote_address` (IP-based)
- `GET /`: 60/minute
- `GET /health`: 30/minute

### 2.4 API Endpoints

| Method | Path | Rate Limit | Mô tả |
|:---:|:---|:---|:---|
| GET | `/` | 60/min | Welcome message + version |
| GET | `/health` | 30/min | Health check (PostgreSQL + Neo4j connectivity) |
| GET | `/api/v1/docs` | — | Swagger UI |
| GET | `/api/v1/redoc` | — | ReDoc |
| GET | `/api/v1/openapi.json` | — | OpenAPI schema |

---

## 3. Frontend Architecture

### 3.1 Công nghệ

| Thành phần | Công nghệ | Phiên bản | Vai trò |
|:---|:---|:---:|:---|
| **Ngôn ngữ** | TypeScript | ~6.0 | `strict: true` — an toàn kiểu tối đa |
| **Thư viện UI** | React | ^19.2.6 | Component-based, unidirectional data flow |
| **Build Tool** | Vite | ^8.0.12 | Dev server + bundler |
| **UI Components** | shadcn/ui | — | Component library (tại `src/components/ui/`) |
| **Linter** | ESLint | ^10.3.0 | Code quality |

### 3.2 Cấu trúc thư mục Frontend

```
frontend/
├── src/
│   ├── main.tsx              # Entry point
│   ├── App.tsx               # Root component + routing
│   ├── components/
│   │   └── ui/               # shadcn/ui components
│   ├── lib/
│   │   └── mockData.ts       # Data simulation engine
│   └── screens/              # Screen components
├── tsconfig.json             # TypeScript strict mode
└── package.json
```

### 3.3 UI Layout & Routing

```
+-------------------------------------------------------------+
| Topbar (Kịch bản switch, Search, Đăng xuất)                  |
+-------------------+-----------------------------------------+
|                   | App Main (Vùng nội dung thay đổi)        |
|                   |                                         |
| SideRail          | * Dashboard: Tổng quan thị trường       |
| (Thanh điều hướng | * KG: Đồ thị Tri thức                   |
|  trái)            | * Stock: Chi tiết mã cổ phiếu           |
|                   | * News: Tin tức tổng hợp                |
|                   | * Chat: Tương tác AI Agent              |
|                   | * Alerts: Cảnh báo bất thường            |
|                   | * Jobs: Quản lý crawler                 |
|                   | * Settings: Cài đặt                     |
+-------------------+-----------------------------------------+
```

* **Routing:** Client-side qua biến trạng thái `screen` trong `App.tsx` (không dùng react-router)
* **Data Engine:** `buildData(scenario)` sinh dữ liệu giả lập với 4 kịch bản: `up`, `down`, `volatile`, `crisis`

### 3.4 Knowledge Graph

* **Node types:** `Event`, `Sector`, `Stock`, `Leader`, `Macro`, `Company`
* **Edge types:** `BELONGS_TO`, `IMPACTS_POS`, `IMPACTS_NEG`, `REDUCES`, `MANAGES`
* **Visualization:** Force-directed graph (KGViewer)

---

## 4. Infrastructure

### 4.1 Docker Compose

4 services trong network `quantyfin-net`:

| Service | Image | Health Check |
|:---|:---|:---|
| `db` | `postgres:15-alpine` | `pg_isready` (5s interval) |
| `neo4j` | `neo4j:5-community` | `cypher-shell RETURN 1` (10s interval) |
| `backend` | Custom (backend.Dockerfile) | Depends on db + neo4j healthy |
| `frontend` | Custom (frontend.Dockerfile) | Depends on backend |

### 4.2 Environment Configuration

Secrets quản lý qua `.env` file (không commit lên git):
- `POSTGRES_PASSWORD`, `NEO4J_PASSWORD`, `SECRET_KEY`: Bắt buộc, validated at startup
- `CORS_ORIGINS`: JSON array của allowed origins
- Xem đầy đủ tại [.env.example](../.env.example)

### 4.3 Testing

| Loại | Framework | Location |
|:---|:---|:---|
| Unit + Integration | pytest + httpx | `backend/tests/` |
| Security tests | pytest | `backend/tests/test_security.py` |
| TypeScript check | `tsc -b` | Frontend build step |
| Linting | ESLint | Frontend `npm run lint` |
