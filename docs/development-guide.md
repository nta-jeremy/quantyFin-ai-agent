# Hướng dẫn Phát triển và Vận hành (Development & Operations Guide)

Tài liệu này cung cấp các hướng dẫn chi tiết để thiết lập môi trường phát triển cục bộ (local development), biên dịch và kiểm tra chất lượng mã nguồn cho dự án QuantyFin Frontend.

## 1. Yêu cầu Hệ thống (Prerequisites)

* **Node.js:** Phiên bản LTS mới nhất (khuyến nghị v18 hoặc v20+).
* **Nền tảng quản lý gói:** `npm` (đi kèm Node.js) hoặc `pnpm`/`yarn`.
* **Trình duyệt Web:** Chrome, Edge, Safari hoặc Firefox phiên bản hiện đại hỗ trợ SVG Sprites và hiệu ứng CSS nâng cao.

## 2. Thiết lập Môi trường cục bộ (Setup Instructions)

Thực hiện các bước sau tại thư mục [docs/sample_src/frontend](file:///Users/tunganh252/Desktop/Projects/Finance/quantyFin-ai-agent/docs/sample_src/frontend):

```bash
# 1. Di chuyển vào thư mục mã nguồn frontend
cd docs/sample_src/frontend

# 2. Cài đặt các gói thư viện phụ thuộc
npm install
```

## 3. Các lệnh phát triển chính (Development Commands)

| Tác vụ | Câu lệnh | Công cụ | Mô tả |
| :--- | :--- | :---: | :--- |
| **Chạy Local Dev Server** | `npm run dev` | Vite 8 | Khởi chạy máy chủ phát triển tại `http://localhost:5173/` với HMR (Hot Module Replacement) |
| **Kiểm tra mã nguồn (Linter)** | `npm run lint` | ESLint 10 | Kiểm tra các quy chuẩn viết mã (coding conventions) và phát hiện lỗi cú pháp tĩnh |
| **Biên dịch dự án (Build)** | `npm run build` | TSC + Vite | Kiểm tra kiểu dữ liệu TypeScript tĩnh (`tsc -b`) và đóng gói mã nguồn cho Production (`vite build`) |
| **Xem trước bản Build** | `npm run preview` | Vite 8 | Chạy máy chủ cục bộ để xem trước bản build đã tối ưu hóa tại cổng `http://localhost:4173/` |

## 4. Cấu hình Môi trường (Environment Configuration)

Dự án hiện tại hoạt động độc lập ở phía Client với dữ liệu giả lập động và không yêu cầu tệp cấu hình `.env` cho môi trường cục bộ. 

Khi kết nối với API Backend trong tương lai, cần bổ sung tệp `.env` tại thư mục gốc của frontend với biến cấu hình:
```env
VITE_API_BASE_URL=http://localhost:8080/api/v1
```

## 5. Quy trình Đóng gói & Vận hành (CI/CD & Deployment)

Hiện tại dự án chưa cấu hình các đường ống tích hợp và triển khai tự động (CI/CD pipelines) như GitHub Workflows hay GitLab CI trong thư mục cục bộ này. Bản build đầu ra nằm tại thư mục `dist/` có thể được triển khai tĩnh lên các nền tảng Hostings tĩnh như Vercel, Netlify hoặc Cloudflare Pages bằng cách trỏ đường dẫn tới thư mục `docs/sample_src/frontend/dist`.
