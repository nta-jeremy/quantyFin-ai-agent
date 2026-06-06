# Hướng dẫn Phát triển và Vận hành (Development & Operations Guide)

Tài liệu này cung cấp các hướng dẫn chi tiết để thiết lập môi trường phát triển cục bộ (local development), biên dịch và kiểm tra chất lượng mã nguồn cho dự án QuantyFin.

---

## 1. Backend (FastAPI)

### 1.1 Yêu cầu hệ thống

* **Python:** >= 3.11
* **Trình quản lý gói:** [uv](https://github.com/astral-sh/uv) (khuyến nghị) hoặc pip
* **Docker & Docker Compose:** Để chạy PostgreSQL và Neo4j

### 1.2 Thiết lập môi trường

```bash
# 1. Sao chép tệp cấu hình môi trường
cp .env.example .env

# 2. Chỉnh sửa .env — BẮT BUỘC đặt giá trị thực cho 3 biến secrets
#    POSTGRES_PASSWORD, NEO4J_PASSWORD, SECRET_KEY
#    Ứng dụng sẽ KHÔNG khởi động nếu bất kỳ biến nào ở trên bị bỏ trống.

# 3. Khởi chạy cơ sở dữ liệu
docker compose up -d db neo4j

# 4. Cài đặt dependencies và chạy backend
cd backend
uv sync
uv run uvicorn app.main:app --reload --port 8000
```

### 1.3 Biến môi trường bắt buộc

| Biến | Mô tả | Ví dụ |
|:---|:---|:---|
| `POSTGRES_PASSWORD` | Mật khẩu PostgreSQL | `my-secure-pg-password` |
| `NEO4J_PASSWORD` | Mật khẩu Neo4j | `my-secure-neo4j-password` |
| `SECRET_KEY` | Khóa bí mật ứng dụng (JWT, mã hóa) | `openssl rand -hex 32` |

> **Lưu ý:** Các biến này có giá trị mặc định `changeme` trong `.env.example` và `docker-compose.yml` chỉ để phát triển cục bộ. **Không bao giờ** sử dụng giá trị mặc định trong production.

Xem đầy đủ các biến tại [.env.example](../.env.example).

### 1.4 Các lệnh phát triển Backend

| Tác vụ | Câu lệnh | Mô tả |
|:---|:---|:---|
| Chạy dev server | `uv run uvicorn app.main:app --reload` | Khởi chạy tại `http://localhost:8000` với hot-reload |
| API docs (Swagger) | `http://localhost:8000/api/v1/docs` | Tài liệu API tương tác |
| API docs (ReDoc) | `http://localhost:8000/api/v1/redoc` | Tài liệu API dạng ReDoc |
| Chạy tests | `uv run pytest` | Chạy toàn bộ test suite |
| Chạy security tests | `uv run pytest tests/test_security.py` | Kiểm tra cấu hình bảo mật |

### 1.5 Bảo mật Backend

Các biện pháp bảo mật đã được triển khai:

**Secret Validation:** Ứng dụng kiểm tra lúc khởi động — nếu `POSTGRES_PASSWORD`, `NEO4J_PASSWORD`, hoặc `SECRET_KEY` trống, ứng dụng sẽ raise lỗi và từ chối khởi động.

**CORS:** Chỉ định origin cụ thể (`http://localhost:5173`), không sử dụng wildcard `*`. Cấu hình qua biến `CORS_ORIGINS`.

**Security Headers:** Tất cả responses đều bao gồm:
| Header | Giá trị |
|:---|:---|
| `X-Content-Type-Options` | `nosniff` |
| `X-Frame-Options` | `DENY` |
| `X-XSS-Protection` | `1; mode=block` |
| `Referrer-Policy` | `strict-origin-when-cross-origin` |
| `Content-Security-Policy` | `default-src 'self'` |
| `Cache-Control` | `no-store` |

**Rate Limiting** (qua `slowapi`):
| Endpoint | Giới hạn |
|:---|:---|
| `GET /` | 60 requests/phút |
| `GET /health` | 30 requests/phút |

**Exception Handling:** Ngoại lệ không được xử lý trả về message chung chung, không để lộ thông tin nội bộ (stack trace, chi tiết database, v.v.).

---

## 2. Frontend (React + TypeScript)

### 2.1 Yêu cầu hệ thống

* **Node.js:** Phiên bản LTS (v18 hoặc v20+)
* **Nền tảng quản lý gói:** `npm` (hoặc `pnpm`/`yarn`)

### 2.2 Thiết lập môi trường

```bash
# 1. Di chuyển vào thư mục frontend
cd frontend

# 2. Cài đặt các gói thư viện phụ thuộc
npm install

# 3. Khởi chạy dev server
npm run dev
```

### 2.3 Các lệnh phát triển Frontend

| Tác vụ | Câu lệnh | Công cụ | Mô tả |
| :--- | :--- | :---: | :--- |
| **Chạy Local Dev Server** | `npm run dev` | Vite | Khởi chạy tại `http://localhost:5173/` với HMR |
| **Kiểm tra mã nguồn** | `npm run lint` | ESLint | Kiểm tra coding conventions và phát hiện lỗi |
| **Biên dịch dự án** | `npm run build` | TSC + Vite | Kiểm tra kiểu dữ liệu (`tsc -b`) và đóng gói (`vite build`) |
| **Xem trước bản Build** | `npm run preview` | Vite | Chạy server xem trước tại `http://localhost:4173/` |

> **TypeScript:** Dự án sử dụng `strict: true` trong tsconfig để đảm bảo an toàn kiểu dữ liệu tối đa.

### 2.4 Cấu hình môi trường Frontend

Khi kết nối với API Backend, tạo tệp `.env` tại thư mục `frontend/`:
```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```
