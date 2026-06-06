---
phase: 1
title: "Security Fixes"
status: done
effort: "4h"
---

# Phase 1: Security Fixes

## Overview
Tập trung sửa 6 lỗi bảo mật nghiêm trọng (Critical) bao gồm: Hardcoded secrets ở cấu hình backend, lỗ hổng Wildcard CORS kết hợp allow_credentials, lộ chi tiết lỗi hệ thống cho client, cấu hình sai alias của shadcn/ui, thiếu strict mode trong TypeScript và nguy cơ rò rỉ `.env` lên git.

## Implementation Steps

### Step 1: Loại bỏ hardcoded secrets trong config.py
- **File**: [/backend/app/core/config.py](file:///Users/tunganh252/Desktop/Projects/Finance/quantyFin-ai-agent/backend/app/core/config.py)
- **Thay đổi**: Thay thế các chuỗi mặc định của `POSTGRES_PASSWORD`, `NEO4J_PASSWORD`, và `SECRET_KEY` bằng chuỗi rỗng `""`.
- Thêm validator sử dụng Pydantic `@model_validator(mode='after')` để bắt lỗi nếu các giá trị này trống khi chạy ứng dụng (đặc biệt khi DEBUG là False).

### Step 2: Sửa cấu hình CORS (CORS Wildcard + Credentials)
- **File**: [/backend/app/core/config.py](file:///Users/tunganh252/Desktop/Projects/Finance/quantyFin-ai-agent/backend/app/core/config.py)
- **Thay đổi**: Khai báo danh sách domain cụ thể `CORS_ORIGINS: list[str] = ["http://localhost:5173"]` (hoặc lấy từ môi trường).
- **File**: [/backend/app/main.py](file:///Users/tunganh252/Desktop/Projects/Finance/quantyFin-ai-agent/backend/app/main.py)
- **Thay đổi**: Đổi `allow_origins=["*"]` thành `allow_origins=settings.CORS_ORIGINS`.

### Step 3: Ngăn chặn rò rỉ chi tiết lỗi hệ thống (Exception Leak)
- **File**: [/backend/app/main.py](file:///Users/tunganh252/Desktop/Projects/Finance/quantyFin-ai-agent/backend/app/main.py)
- **Thay đổi**: Trong `generic_exception_handler`, thay vì trả về `"details": str(exc)` hãy đổi thành `"details": "Internal server error"` hoặc `None` để bảo mật thông tin nội bộ. Vẫn ghi log chi tiết trên server.

### Step 4: Sửa alias đường dẫn shadcn/ui
- **Thay đổi**: Di chuyển thư mục `frontend/@/components/` sang `frontend/src/components/` và `frontend/@/lib/` sang `frontend/src/lib/`. Xoá thư mục `frontend/@/`.
- **File**: [/frontend/components.json](file:///Users/tunganh252/Desktop/Projects/Finance/quantyFin-ai-agent/frontend/components.json)
- **Thay đổi**: Cập nhật các alias tương ứng để khớp với `frontend/tsconfig.json` và cấu hình Vite.

### Step 5: Bật TypeScript Strict Mode
- **File**: [/frontend/tsconfig.app.json](file:///Users/tunganh252/Desktop/Projects/Finance/quantyFin-ai-agent/frontend/tsconfig.app.json)
- **Thay đổi**: Thêm `"strict": true` vào `compilerOptions`. Kiểm tra và sửa các lỗi type-checking phát sinh.

### Step 6: Xác minh và cấu hình .env an toàn
- **File**: [/.gitignore](file:///Users/tunganh252/Desktop/Projects/Finance/quantyFin-ai-agent/.gitignore)
- **Thay đổi**: Đảm bảo `.env` được khai báo. Chạy lệnh `git rm --cached .env` nếu phát hiện tệp đã bị tracking.
- **File**: [/.env.example](file:///Users/tunganh252/Desktop/Projects/Finance/quantyFin-ai-agent/.env.example)
- **Thay đổi**: Đảm bảo chỉ chứa các placeholder an toàn (ví dụ: `changeme`), không chứa mật khẩu thật.

## Success Criteria
- [x] Không còn hardcoded mật khẩu/khóa bí mật trong `config.py`.
- [x] CORS được cấu hình giới hạn domain cụ thể thay vì dấu wildcard `*`.
- [x] Client không nhận được nội dung exception thô của hệ thống.
- [x] Thư mục `frontend/@/` bị xóa hoàn toàn, shadcn/ui hoạt động chính xác với đường dẫn `src/`.
- [x] Dự án frontend compile thành công với TypeScript strict mode bật.
- [x] Tệp `.env` không bị đẩy lên git repository.
- [x] Security headers (X-Content-Type-Options, X-Frame-Options, CSP, etc.) được thêm.
- [x] Rate limiting được cấu hình cho API endpoints.
