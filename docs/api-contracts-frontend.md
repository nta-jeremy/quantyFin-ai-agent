# Tài liệu Giao thức & API (Frontend)

Dự án QuantyFin Frontend hiện tại là một ứng dụng Client-only (chạy độc lập ở phía Client) phục vụ việc mô phỏng giao diện người dùng và kiểm thử kịch bản vĩ mô. 

## 1. Cơ chế Tích hợp Dữ liệu
Hiện tại, ứng dụng không kết nối trực tiếp với một hệ thống API Backend bên ngoài qua HTTP requests (fetch, axios). Thay vào đó, toàn bộ dữ liệu được khởi tạo và mô phỏng động ở Client thông qua mô-đun dữ liệu giả lập tại [mockData.ts](file:///Users/tunganh252/Desktop/Projects/Finance/quantyFin-ai-agent/docs/sample_src/frontend/src/lib/mockData.ts).

* **Cơ chế tải dữ liệu:** Sử dụng hàm khởi tạo `buildData(scenario)` với các kịch bản định sẵn:
  * `up` (Thị trường đi lên)
  * `down` (Thị trường đi xuống)
  * `volatile` (Biến động)
  * `crisis` (Khủng hoảng)
* **Lưu trữ trạng thái:** Sử dụng `localStorage` để lưu thông tin phiên đăng nhập giả lập (`qf_auth`).

## 2. Giao thức Mô phỏng Dữ liệu nội bộ
Trong tương lai, khi kết nối với Backend, các luồng dữ liệu giả lập sẽ được ánh xạ thành các API Endpoints tương ứng:

| Mô phỏng nội bộ | API Endpoint dự kiến | Phương thức | Mô tả |
| :--- | :--- | :---: | :--- |
| `buildStocks(scenario)` | `/api/v1/stocks` | GET | Lấy danh sách cổ phiếu kèm chỉ số cảm nhận thị trường (sentiment) |
| `buildIndices(scenario)` | `/api/v1/indices` | GET | Lấy danh sách các chỉ số thị trường (VN-Index, HNX-Index, VN30, UPCoM) |
| `buildMacros(scenario)` | `/api/v1/macros` | GET | Lấy các sự kiện vĩ mô ảnh hưởng tới thị trường |
| `buildNews(scenario, stocks)` | `/api/v1/news` | GET | Lấy danh sách tin tức tài chính được lọc và phân tích bởi AI |
| `buildAlerts(scenario, news, stocks)` | `/api/v1/alerts` | GET | Lấy danh sách cảnh báo bất thường hoặc phát hiện chuỗi rủi ro liên đới |
| `buildJobs(scenario)` | `/api/v1/jobs` | GET | Lấy trạng thái hoạt động của các tác vụ thu thập tin tức tự động (RSS, Playwright) |
| `localStorage qf_auth` | `/api/v1/auth/login` | POST | Xác thực người dùng và cấp mã thông báo phiên (session token) |
