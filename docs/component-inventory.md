# Danh mục Thành phần Giao diện (Component Inventory)

QuantyFin Frontend được cấu thành từ hệ thống React Components mô-đun hóa cao, tách biệt rõ ràng giữa thành phần giao diện chung (Shared UI), các màn hình chức năng chuyên biệt (Screens) và các công cụ bổ trợ phát triển (Development tools).

## 1. Thành phần giao diện dùng chung (Shared UI)

Được định nghĩa tại [SharedUI.tsx](file:///Users/tunganh252/Desktop/Projects/Finance/quantyFin-ai-agent/docs/sample_src/frontend/src/components/SharedUI.tsx):

* **SideRail (Thanh điều hướng trái):**
  * **Chức năng:** Quản lý chuyển đổi màn hình chính của ứng dụng bằng các nút bấm trực quan.
  * **Trạng thái tích hợp:** Hiển thị một badge màu đỏ chứa số lượng cảnh báo chưa xử lý lấy từ dữ liệu cảnh báo động.
* **Topbar (Thanh đầu trang):**
  * **Chức năng:** Hiển thị thanh tiêu đề động tương ứng với màn hình hiện tại, nút tìm kiếm nhanh (kích hoạt màn hình Chat AI) và nút đăng xuất.
  * **Bộ chuyển đổi kịch bản (Scenario Selector):** Cho phép thay đổi nhanh kịch bản thị trường ngay từ Topbar để kiểm tra phản ứng của toàn bộ dữ liệu.

## 2. Thành phần màn hình chức năng (Screen Components)

Được gói chung trong không gian tên `Screens` tại [ScreenComponents.tsx](file:///Users/tunganh252/Desktop/Projects/Finance/quantyFin-ai-agent/docs/sample_src/frontend/src/components/ScreenComponents.tsx):

* **Screens.Login (Màn hình Đăng nhập):**
  * **Chức năng:** Giao diện đăng nhập đơn giản yêu cầu mật khẩu giả lập để mở khóa giao diện chính.
* **Screens.Dashboard (Màn hình Tổng quan):**
  * **Chức năng:** Màn hình chính tổng hợp chỉ số thị trường (VN-Index, VN30,...), tin tức nóng nhất từ AI, và bảng theo dõi cổ phiếu rút gọn (Watchlist).
* **Screens.Stock (Chi tiết Cổ phiếu):**
  * **Chức năng:** Hiển thị biểu đồ sparkline lịch sử giá cổ phiếu, thông tin vốn hóa, khối lượng giao dịch, ngành, điểm sentiment từ AI và các tin tức riêng liên quan đến mã chứng khoán đó.
* **Screens.News (Bảng tin tức):**
  * **Chức năng:** Feed tin tức tài chính tổng hợp có gắn bộ lọc phân loại theo ngành và bộ lọc trạng thái xử lý AI (`filtered`, `pending`, `analyzed`).
* **Screens.Chat (Trò chuyện AI):**
  * **Chức năng:** Khung trò chuyện giả lập cho phép nhập câu hỏi và nhận câu trả lời mô phỏng từ AI Agent phân tích tài chính.
* **Screens.Alerts (Nhật ký cảnh báo):**
  * **Chức năng:** Hiển thị nhật ký các cảnh báo khẩn cấp hoặc bất thường của thị trường được xếp lớp theo độ nghiêm trọng (high, med, info).
* **Screens.Jobs (Giám sát Agent):**
  * **Chức năng:** Giao diện quản lý các crawler cào dữ liệu RSS, hiển thị tỷ lệ lọc tin và tốc độ xử lý của từng agent.
* **Screens.Settings (Cài đặt):**
  * **Chức năng:** Trang điều chỉnh các tham số cấu hình hiển thị và cấu hình tài khoản người dùng.

## 3. Trình xem Đồ thị Tri thức (Knowledge Graph Viewer)

Được định nghĩa tại [KGViewer.tsx](file:///Users/tunganh252/Desktop/Projects/Finance/quantyFin-ai-agent/docs/sample_src/frontend/src/components/KGViewer.tsx):

* **KGViewer:**
  * **Chức năng:** Component phức tạp nhất chịu trách nhiệm render sơ đồ mạng lưới liên kết các thực thể vĩ mô, mã cổ phiếu và ngành.
  * **Tương tác:** Cho phép người dùng rê chuột vào các nút (Nodes) để xem nhãn giải thích và nhấn vào nút cổ phiếu để chuyển nhanh sang màn hình chi tiết cổ phiếu đó (`Stock Screen`).

## 4. Công cụ hỗ trợ phát triển (Development Tweaks)

Được định nghĩa tại [TweaksPanel.tsx](file:///Users/tunganh252/Desktop/Projects/Finance/quantyFin-ai-agent/docs/sample_src/frontend/src/components/TweaksPanel.tsx):

* **TweaksPanel:**
  * **Chức năng:** Bảng điều khiển thu gọn gắn nổi ở góc dưới màn hình.
  * **Tính năng:** Cung cấp các công cụ kiểm thử nhanh giao diện người dùng như: đổi chủ đề Light/Dark, chuyển đổi kịch bản thị trường để cập nhật lại dữ liệu toàn hệ thống, hoặc bật/tắt hiển thị thẻ tin cậy AI (AI Confidence chips).
