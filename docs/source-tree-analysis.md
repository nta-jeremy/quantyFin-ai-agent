# Phân tích Cấu trúc Thư mục Nguồn (Source Tree Analysis)

Cấu trúc thư mục của dự án QuantyFin Frontend được tổ chức theo cấu trúc tiêu chuẩn của một ứng dụng Single Page Application (SPA) xây dựng trên nền tảng React + Vite + TypeScript.

## 1. Bản đồ Thư mục Dự án

Dưới đây là sơ đồ chi tiết các thư mục và tệp tin mã nguồn trong thư mục [frontend](file:///Users/tunganh252/Desktop/Projects/Finance/quantyFin-ai-agent/docs/sample_src/frontend):

```
docs/sample_src/frontend/
├── dist/                          # Thư mục chứa mã nguồn đã build (production bundle)
├── public/                        # Chứa các tài nguyên tĩnh không qua xử lý của Vite
│   ├── favicon.svg                # Icon ứng dụng hiển thị trên trình duyệt
│   └── icons.svg                  # Danh sách bộ icons SVG dùng chung (SVG sprites)
├── src/                           # Thư mục chứa mã nguồn chính của ứng dụng
│   ├── assets/                    # Chứa hình ảnh tĩnh phục vụ ứng dụng
│   │   ├── hero.png               # Banner trang chủ/login
│   │   ├── react.svg
│   │   └── vite.svg
│   ├── components/                # Chứa các React components phân rã
│   │   ├── KGViewer.tsx           # Trình xem đồ thị tri thức (Knowledge Graph) tương tác
│   │   ├── ScreenComponents.tsx   # Các màn hình chính (Dashboard, Login, Stock, News, Chat, Alerts, Jobs)
│   │   ├── Settings.tsx           # Màn hình cài đặt hệ thống
│   │   ├── SharedUI.tsx           # Thành phần UI dùng chung (Sidebar, Topbar, Header)
│   │   └── TweaksPanel.tsx        # Bảng điều khiển giả lập kịch bản thị trường (QuantyFin Tweaks)
│   ├── lib/                       # Chứa thư viện tiện ích và mô hình dữ liệu
│   │   └── mockData.ts            # Cấu trúc interfaces và thuật toán sinh dữ liệu thị trường giả lập
│   ├── styles/                    # Chứa hệ thống CSS modular hóa
│   │   ├── ai_kit.css             # Định kiểu các chip cảm nhận và thành phần giao tiếp AI
│   │   ├── app_kit.css            # Thư viện giao diện chính (bảng, khối thông tin, KPI)
│   │   ├── colors_and_type.css    # Biến CSS cho màu sắc và typography hệ thống
│   │   └── project_styles.css     # Định kiểu tùy biến bổ sung của dự án
│   ├── App.css                    # Định kiểu tổng quát cho vỏ ứng dụng (app shell)
│   ├── App.tsx                    # React Root Component điều phối định tuyến và kịch bản giả lập
│   ├── index.css                  # CSS cấp cao nhất (reset và biến global)
│   └── main.tsx                   # Điểm khởi chạy ứng dụng (Application Entry Point)
├── package.json                   # Định nghĩa dependencies và các câu lệnh npm scripts
├── tsconfig.json                  # Cấu hình TypeScript cho dự án
├── tsconfig.app.json              # Cấu hình TypeScript chi tiết cho mã nguồn ứng dụng
├── tsconfig.node.json             # Cấu hình TypeScript cho môi trường Node (Vite config)
├── eslint.config.js               # Cấu hình công cụ kiểm tra chất lượng mã nguồn (linter)
└── vite.config.ts                 # Cấu hình bộ công cụ bundler Vite
```

## 2. Các điểm mấu chốt của ứng dụng (Key Entrypoints)

* **Điểm khởi tạo (Application Entry Point):** [main.tsx](file:///Users/tunganh252/Desktop/Projects/Finance/quantyFin-ai-agent/docs/sample_src/frontend/src/main.tsx) nạp React 19 và render component `<App />` vào DOM tại phần tử `#root` của `index.html`.
* **Component gốc (Root App Component):** [App.tsx](file:///Users/tunganh252/Desktop/Projects/Finance/quantyFin-ai-agent/docs/sample_src/frontend/src/App.tsx) thực hiện:
  1. Quản lý trạng thái xác thực người dùng giả lập (`qf_auth` trong `localStorage`).
  2. Quản lý định tuyến màn hình nội bộ (`dashboard`, `kg`, `stock`, `news`, `chat`, `alerts`, `jobs`, `settings`).
  3. Cung cấp bộ cấu hình giả lập kịch bản (`QuantyFin Tweaks`) cho phép chuyển đổi nhanh giữa các môi trường thị trường (Tăng, Giảm, Biến động, Khủng hoảng) và bật/tắt hiển thị chỉ số tin cậy AI.
* **Bộ sinh dữ liệu (Data Engine):** [mockData.ts](file:///Users/tunganh252/Desktop/Projects/Finance/quantyFin-ai-agent/docs/sample_src/frontend/src/lib/mockData.ts) là nơi nắm giữ toàn bộ thuật toán tạo xu hướng biến động giá của 32 mã cổ phiếu và sinh tự động 32 tin tức tài chính dựa theo kịch bản thị trường được chọn.
