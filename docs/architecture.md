# Tài liệu Kiến trúc Hệ thống (System Architecture)

QuantyFin Frontend là giao diện ứng dụng web tương tác dành cho trợ lý đầu tư AI (QuantyFin AI Agent). Hệ thống cho phép nhà đầu tư theo dõi điểm cảm nhận thị trường vĩ mô (AI sentiment analysis), khám phá mối quan hệ liên đới giữa các sự kiện và mã cổ phiếu thông qua Đồ thị Tri thức (Knowledge Graph), giám sát tiến độ thu thập tin tức của các AI Agents (RSS, Playwright), và tương tác trực tiếp với Trợ lý ảo qua khung Chat.

## 1. Tổng quan Kiến trúc (Executive Summary)

* **Loại kiến trúc:** Single Page Application (SPA) phát triển trên nền tảng React 19.
* **Mô hình kiến trúc:** Component-based Architecture (Kiến trúc hướng thành phần) kết hợp mô hình luồng dữ liệu một chiều (Unidirectional Data Flow) của React.
* **Cơ chế trạng thái:** Trạng thái giao diện, định tuyến màn hình, và kịch bản dữ liệu được quản lý tập trung ở Root Component (`App.tsx`), truyền xuống các Component con qua `props` hoặc lưu trữ phiên ở `localStorage`.
* **Cơ chế mô phỏng dữ liệu (Data Engine):** Sử dụng công cụ mô phỏng toán học cục bộ để tạo biến động giá và tin tức theo 4 kịch bản thị trường chính (`up`, `down`, `volatile`, `crisis`).

## 2. Công nghệ Sử dụng (Technology Stack)

Hệ thống sử dụng các công nghệ hiện đại, tối giản và hiệu năng cao:

| Thành phần | Công nghệ | Phiên bản | Vai trò |
| :--- | :--- | :---: | :--- |
| **Ngôn ngữ** | TypeScript | ~6.0.2 | Đảm bảo an toàn kiểu dữ liệu và nâng cao trải nghiệm lập trình |
| **Thư viện chính** | React | ^19.2.6 | Xây dựng giao diện hướng thành phần, cập nhật DOM hiệu quả |
| **Công cụ Build** | Vite | ^8.0.12 | Trình đóng gói (bundler) siêu tốc phục vụ phát triển và build |
| **CSS Styling** | Vanilla CSS | N/A | Thiết kế giao diện đặc thù không dùng framework cồng kềnh |
| **Mã nguồn Linter**| ESLint | ^10.3.0 | Đảm bảo tính đồng nhất và chất lượng mã nguồn |

## 3. Kiến trúc Luồng Giao diện & Định tuyến (UI Layout & Routing)

Kiến trúc vỏ ứng dụng (App Shell) bao gồm các khối chính:

```
+-------------------------------------------------------------+
| Topbar (Kịch bản switch, Search, Đăng xuất)                  |
+-------------------+-----------------------------------------+
|                   | App Main (Vùng nội dung thay đổi)        |
|                   |                                         |
| SideRail          | * Dashboard: Tổng quan thị trường       |
| (Thanh điều hướng | * KG: Trình xem Đồ thị Tri thức         |
|  trái)            | * Stock: Chi tiết mã cổ phiếu           |
|                   | * News: Tin tức tổng hợp                |
|                   | * Chat: Khung tương tác AI Agent        |
|                   | * Alerts: Nhật ký cảnh báo bất thường    |
|                   | * Jobs: Quản lý crawler thu thập tin    |
|                   | * Settings: Cài đặt hệ thống            |
+-------------------+-----------------------------------------+
| TweaksPanel (Bảng cấu hình giả lập kịch bản chạy ẩn góc dưới)|
+-------------------------------------------------------------+
```

* **Cơ chế chuyển trang (Client-side Routing):** Thay vì sử dụng thư viện ngoài, hệ thống dùng biến trạng thái `screen` trong `App.tsx` làm bộ định tuyến nội bộ giúp tối giản kích thước gói bundle.
* **Bảng điều khiển chạy thử (Tweaks Panel):** Đóng vai trò là công cụ kiểm thử nhanh giao diện bằng cách cho phép thay đổi tức thì chủ đề (`theme: light/dark`), bật tắt các chỉ số tin cậy AI, hoặc chuyển đổi kịch bản thị trường để kiểm tra phản ứng của đồ thị tri thức và tin tức.

## 4. Kiến trúc Dữ liệu & Đồ thị Tri thức (Data & Knowledge Graph Architecture)

* **Bộ sinh dữ liệu (Generator):** Hàm `buildData(scenario)` khởi tạo toàn bộ trạng thái Dashboard dựa vào cơ chế sinh ngẫu nhiên có hạt giống (`seedRand`) tương ứng với từng mã cổ phiếu, đảm bảo tính nhất quán của chuỗi giá lịch sử qua mỗi phiên chạy.
* **Cơ chế Đồ thị Tri thức (Knowledge Graph):** 
  * Định nghĩa cấu trúc nút (`KGNode`) bao gồm các loại: `Event`, `Sector`, `Stock`, `Leader`, `Macro`, `Company`.
  * Liên kết giữa các thực thể thông qua cạnh (`KGEdge`) với các mối quan hệ ngữ nghĩa như: `BELONGS_TO`, `IMPACTS_POS`, `IMPACTS_NEG`, `REDUCES`, `MANAGES`.
  * Giao diện `KGViewer.tsx` chịu trách nhiệm diễn giải cấu trúc này thành đồ thị tương tác dạng lực hướng tâm (Force-directed graph) hoặc sơ đồ mạng lưới trực quan.

## 5. Quản lý Giao diện (UI Components & Design System)

Hệ thống giao diện sử dụng thiết kế tinh tế với bảng màu độc quyền HSL dark-mode và typography từ font **Be Vietnam Pro** (được lưu trữ tại [DesignSystem](file:///Users/tunganh252/Desktop/Projects/Finance/quantyFin-ai-agent/docs/design_ui_ux/DesignSystem)):

* **SharedUI.tsx:** Định nghĩa `<SideRail />` và `<Topbar />`.
* **ScreenComponents.tsx:** Gói tất cả các màn hình chức năng dưới dạng không gian tên `<Screens />` nâng cao khả năng quản lý và import mã nguồn.
* **Hệ thống CSS Modular:** Phân tách rõ ràng giữa cấu hình cốt lõi (`colors_and_type.css`), định kiểu ứng dụng chung (`app_kit.css`), các thành phần AI đặc thù (`ai_kit.css`), và phong cách riêng dự án (`project_styles.css`).

## 6. Chiến lược Kiểm thử & Đảm bảo Chất lượng (Testing Strategy)

* **Phân tích Tĩnh (Static Analysis):** Sử dụng ESLint kết hợp kiểm tra kiểu TypeScript (`tsc -b`) để bắt lỗi ngay trong quá trình viết mã.
* **Kiểm thử Thủ công (Manual Testing Verification):** Sử dụng thanh cấu hình `QuantyFin Tweaks` để kiểm tra trực quan các trạng thái giao diện khi thay đổi kịch bản dữ liệu (ví dụ: màn hình sẽ hiển thị cảnh báo nghiêm trọng màu đỏ khi chọn kịch bản `crisis`).
* **Handoff kiểm thử tự động:** Các thuộc tính HTML class/id được thiết kế rõ ràng giúp dễ dàng cấu hình bộ công cụ kiểm thử E2E (như Playwright hoặc Cypress) trong tương lai.
