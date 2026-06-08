# QuantyFin Backend

FastAPI backend cho QuantyFin AI Agent — hệ thống trợ lý đầu tư tài chính với phân tích cảm nhận AI và Knowledge Graph.

## Yêu cầu

- Python >= 3.11
- [uv](https://github.com/astral-sh/uv) (khuyến nghị) hoặc pip
- PostgreSQL 15 + Neo4j 5 (chạy qua Docker Compose)

## Quick Start

```bash
# 1. Cấu hình environment
cp .env.example .env
# Chỉnh .env: đặt POSTGRES_PASSWORD, NEO4J_PASSWORD, SECRET_KEY

# 2. Khởi chạy databases
docker compose up -d db neo4j

# 3. Install dependencies + chạy server
cd backend
uv sync
uv run uvicorn app.main:app --reload --port 8000
```

## Biến môi trường bắt buộc

| Biến | Mô tả |
|:---|:---|
| `POSTGRES_PASSWORD` | Mật khẩu PostgreSQL — app từ chối khởi động nếu trống |
| `NEO4J_PASSWORD` | Mật khẩu Neo4j — app từ chối khởi động nếu trống |
| `SECRET_KEY` | Khóa bí mật ứng dụng — app từ chối khởi động nếu trống |
| `CORS_ORIGINS` | Allowed origins (mặc định: `["http://localhost:5173"]`) |

## API Endpoints

| Method | Path | Mô tả |
|:---:|:---|:---|
| GET | `/` | Welcome (rate limit: 60/min) |
| GET | `/health` | Health check PostgreSQL + Neo4j (rate limit: 30/min) |
| GET | `/api/v1/docs` | Swagger UI |
| GET | `/api/v1/redoc` | ReDoc |

## Bảo mật

- **Secret validation:** Kiểm tra lúc khởi động, raise error nếu secrets trống
- **Security headers:** `X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection`, `Referrer-Policy`, `Content-Security-Policy`, `Cache-Control`
- **CORS:** Specific origins only (no wildcard)
- **Rate limiting:** Via `slowapi` — 60/min (root), 30/min (health)
- **Exception handling:** Không để lộ internal details trong error responses

## Testing

```bash
# Chạy toàn bộ tests
uv run pytest

# Chỉ security tests
uv run pytest tests/test_security.py

# Verbose output
uv run pytest -v
```

## Dependencies

| Package | Version | Mục đích |
|:---|:---|:---|
| fastapi | >=0.136.3 | REST API framework |
| sqlmodel | >=0.0.38 | PostgreSQL ORM |
| neo4j | >=6.2.0 | Graph DB driver |
| pydantic-settings | >=2.14.1 | Config validation |
| slowapi | >=0.1.9 | Rate limiting |
| uvicorn | >=0.49.0 | ASGI server |
| psycopg2-binary | >=2.9.12 | PostgreSQL adapter |
