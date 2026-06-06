# Chỉ mục Tài liệu Dự án (Project Documentation Index)

Chào mừng bạn đến với tài liệu kỹ thuật dành cho nhà phát triển và các tác nhân AI của dự án **QuantyFin**. Đây là điểm tra cứu trung tâm để hiểu toàn bộ kiến trúc, mô hình dữ liệu và quy trình phát triển của ứng dụng.

## 1. Tổng quan Dự án

* **Tên dự án:** QuantyFin AI Agent
* **Loại dự án:** Monolith Web Application
* **Ngôn ngữ lập trình chính:** TypeScript (React 19)
* **Kiểu kiến trúc:** Component-based SPA (Single Page Application)
* **Thư mục mã nguồn:** [docs/sample_src/frontend](file:///Users/tunganh252/Desktop/Projects/Finance/quantyFin-ai-agent/docs/sample_src/frontend)

## 2. Tra cứu Nhanh (Quick Reference)

* **Công nghệ cốt lõi:** React 19, Vite 8, TypeScript 6, Vanilla CSS.
* **Điểm khởi chạy (Entry Point):** [main.tsx](file:///Users/tunganh252/Desktop/Projects/Finance/quantyFin-ai-agent/docs/sample_src/frontend/src/main.tsx).
* **Quản lý dữ liệu giả lập:** [mockData.ts](file:///Users/tunganh252/Desktop/Projects/Finance/quantyFin-ai-agent/docs/sample_src/frontend/src/lib/mockData.ts).

## 3. Danh mục Tài liệu Kỹ thuật đã sinh (Generated Documentation)

Tất cả các tài liệu dưới đây đã được cập nhật và sẵn sàng tra cứu:

* 📚 [Tổng quan Dự án (Project Overview)](./project-overview.md) — Giới thiệu tổng quan về mục tiêu, giải pháp và cấu trúc tài liệu.
* 🏗️ [Tài liệu Kiến trúc hệ thống (System Architecture)](./architecture.md) — Đặc tả kiến trúc luồng dữ liệu, vỏ ứng dụng, bộ sinh dữ liệu và mô hình đồ thị tri thức.
* 📁 [Phân tích cấu trúc thư mục (Source Tree Analysis)](./source-tree-analysis.md) — Sơ đồ tổ chức các tệp tin và các điểm khởi chạy mấu chốt của ứng dụng.
* 📦 [Danh mục Thành phần giao diện (Component Inventory)](./component-inventory.md) — Danh sách các UI Components như Sidebar, Topbar, Screens, KGViewer, TweaksPanel.
* ⚙️ [Mô hình dữ liệu (Data Models)](./data-models-frontend.md) — Đặc tả chi tiết cấu trúc dữ liệu cho Stock, News, Alert, Job, KGNode.
* 🔌 [Giao thức API & Mô phỏng (API Contracts)](./api-contracts-frontend.md) — Đặc tả cơ chế mô phỏng dữ liệu và lộ trình ánh xạ sang các endpoints thực tế.
* 🛠️ [Hướng dẫn phát triển cục bộ (Development Guide)](./development-guide.md) — Hướng dẫn cài đặt, chạy máy chủ dev cục bộ và các câu lệnh phát triển.
* 🚀 [Hướng dẫn triển khai sản phẩm (Deployment Guide)](./deployment-guide.md) — Các bước đóng gói, cấu hình docker container, Nginx và triển khai lên đám mây.
* 🕸️ [Đặc tả KGViewer & Cài đặt Crawler](./kgviewer-crawler-guide.md) — Tài liệu chi tiết thiết kế thành phần KGViewer và hướng dẫn thiết lập hệ thống thu thập tin tức vĩ mô qua RSS, API và Playwright.

## 4. Tài liệu Thiết kế & Hướng dẫn Tích hợp (Design & Integration Docs)

Đây là các tài liệu thiết kế giao diện UX, kịch bản hành vi và hướng dẫn tích hợp công cụ AI:

* 🎨 [Tài liệu Thiết kế hệ thống (Design System README)](./design_ui_ux/DesignSystem/README.md) — Tổng quan về hệ thống thiết kế giao diện.
* 📏 [Đặc tả Thiết kế Giao diện (Design Specs)](./design_ui_ux/DesignSystem/DESIGN.md) — Quy chuẩn màu sắc, phông chữ và bố cục.
* 📋 [QuantyFin PRD (Product Requirement Document)](./design_ui_ux/PRD-QuantyFin-standalone.md) — Tài liệu yêu cầu sản phẩm chi tiết cho QuantyFin.

## 5. Khởi chạy nhanh Dự án (Getting Started)

Để chạy thử giao diện QuantyFin Frontend trên máy tính của bạn:

```bash
# Di chuyển đến thư mục mã nguồn
cd docs/sample_src/frontend

# Cài đặt thư viện phụ thuộc
npm install

# Khởi chạy chế độ phát triển
npm run dev
```

Sau khi chạy lệnh trên, truy cập `http://localhost:5173` trên trình duyệt để trải nghiệm giao diện QuantyFin.
