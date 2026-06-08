# Hướng dẫn Triển khai (Deployment Guide)

Tài liệu này hướng dẫn đóng gói và triển khai ứng dụng QuantyFin (Backend + Frontend + Databases) lên môi trường production.

---

## 1. Triển khai Full-stack với Docker Compose

### 1.1 Cấu hình môi trường (BẮT BUỘC)

Trước khi deploy, tạo file `.env` từ template và **đặt giá trị thực** cho các biến secrets:

```bash
cp .env.example .env
```

| Biến | Bắt buộc | Mô tả | Cách tạo giá trị |
|:---|:---:|:---|:---|
| `POSTGRES_PASSWORD` | ✅ | Mật khẩu PostgreSQL | `openssl rand -base64 32` |
| `NEO4J_PASSWORD` | ✅ | Mật khẩu Neo4j | `openssl rand -base64 32` |
| `SECRET_KEY` | ✅ | Khóa bí mật ứng dụng | `openssl rand -hex 32` |
| `CORS_ORIGINS` | Production | Danh sách origin được phép (JSON array) | `["https://yourdomain.com"]` |

> **Cảnh báo:** `docker-compose.yml` sử dụng giá trị mặc định `changeme` cho passwords chỉ để phát triển cục bộ. Trong production, **bắt buộc** override qua `.env` hoặc environment variables.

### 1.2 Khởi chạy

```bash
# Build và start toàn bộ services
docker compose up -d

# Kiểm tra trạng thái
docker compose ps

# Xem logs
docker compose logs -f backend
```

### 1.3 Ports

| Service | Port | Mô tả |
|:---|:---|:---|
| Frontend | `3000` | Giao diện người dùng |
| Backend API | `8000` | API server (FastAPI) |
| PostgreSQL | `5432` | Database (chỉ expose trong dev) |
| Neo4j HTTP | `7474` | Neo4j Browser |
| Neo4j Bolt | `7687` | Neo4j connection |

---

## 2. Cấu hình Bảo mật (Security Configuration)

### 2.1 Secret Validation

Backend **từ chối khởi động** nếu bất kỳ biến nào sau đây trống:
- `POSTGRES_PASSWORD`
- `NEO4J_PASSWORD`
- `SECRET_KEY`

Kiểm tra tại: `backend/app/core/config.py` — `validate_secrets()` model validator.

### 2.2 Security Headers

Tất cả HTTP responses bao gồm các headers bảo mật:

| Header | Giá trị | Mục đích |
|:---|:---|:---|
| `X-Content-Type-Options` | `nosniff` | Ngăn browser MIME-sniffing |
| `X-Frame-Options` | `DENY` | Ngăn clickjacking |
| `X-XSS-Protection` | `1; mode=block` | Kích hoạt XSS filter |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Kiểm soát referrer leakage |
| `Content-Security-Policy` | `default-src 'self'` | Ngăn tải tài nguyên ngoài |
| `Cache-Control` | `no-store` | Ngăn cache responses nhạy cảm |

### 2.3 CORS

CORS được cấu hình chỉ định origin cụ thể (không dùng wildcard `*`):
- **Mặc định:** `["http://localhost:5173"]` (dev only)
- **Production:** Đặt qua biến `CORS_ORIGINS` trong `.env`

### 2.4 Rate Limiting

Sử dụng `slowapi` để giới hạn request rate:

| Endpoint | Limit |
|:---|:---|
| `GET /` | 60 requests/phút |
| `GET /health` | 30 requests/phút |

Khi vượt giới hạn, API trả về `429 Too Many Requests`.

### 2.5 Exception Handling

- **Application exceptions** (`BaseAppException`): Trả về message + error code có cấu trúc
- **Unhandled exceptions**: Trả về message chung chung, **không để lộ** stack trace hoặc thông tin nội bộ

---

## 3. Triển khai Frontend riêng lẻ

Vì Frontend là SPA (Single Page Application) xây dựng bằng Vite, có thể triển khai tĩnh riêng:

### 3.1 Build

```bash
cd frontend
npm install
npm run build
```

Output: `frontend/dist/`

### 3.2 Triển khai lên Vercel (Khuyến nghị)

1. Tạo dự án trên [Vercel Dashboard](https://vercel.com)
2. Cấu hình:
   - **Framework Preset:** `Vite`
   - **Root Directory:** `frontend`
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`

### 3.3 Triển khai lên Netlify

1. Tạo site mới trên [Netlify](https://netlify.com)
2. Cấu hình:
   - **Base directory:** `frontend`
   - **Build command:** `npm run build`
   - **Publish directory:** `frontend/dist`

### 3.4 Docker Container riêng

```dockerfile
FROM node:20-alpine AS build-stage
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:stable-alpine
COPY --from=build-stage /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

---

## 4. SSL/TLS & DNS

1. Trỏ bản ghi DNS (CNAME/A) tới server
2. Kích hoạt SSL/TLS (Let's Encrypt tự động qua Vercel/Netlify, hoặc Certbot cho VPS)
3. Trong production, đặt `CORS_ORIGINS` với `https://` origins
