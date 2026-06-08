# Tổng quan Dự án (Project Overview)

Chào mừng bạn đến với tài liệu kỹ thuật của dự án **QuantyFin AI Agent**. 

QuantyFin là một hệ thống trợ lý ảo thông minh hỗ trợ đầu tư tài chính được phát triển để tối ưu hóa quá trình phân tích thông tin thị trường chứng khoán Việt Nam. Hệ thống kết hợp phân tích cảm nhận tin tức bằng AI (AI Sentiment Analysis) và mô hình hóa dữ liệu dạng Đồ thị Tri thức (Knowledge Graph) để giúp nhà đầu tư phát hiện sớm các cơ hội hoặc rủi ro vĩ mô tiềm ẩn.

## 1. Mục tiêu Dự án
* **Trực quan hóa Đồ thị Tri thức:** Biểu diễn các mối liên kết chéo giữa các chính sách vĩ mô, các ngành kinh tế, ban lãnh đạo doanh nghiệp và biến động giá cổ phiếu.
* **Cá nhân hóa Phân tích Cảm nhận (Sentiment):** Thu thập tin tức thời gian thực từ các nguồn CafeF, Vietstock, VnEconomy,... lọc nhiễu và gán nhãn cảm nhận bằng các mô hình LLM chuyên dụng.
* **Tự động hóa Giám sát:** Chạy ngầm các crawler để liên tục cập nhật dòng chảy tin tức và gửi cảnh báo tức thì khi có biến động bất thường xảy ra.

## 2. Tóm tắt Công nghệ & Cấu trúc

* **Ngôn ngữ & Khung phát triển chính:** React 19 + TypeScript + Vite 8.
* **Cấu trúc lưu trữ:** Monolith (Mã nguồn được đóng gói gọn trong thư mục `docs/sample_src/frontend`).
* **Phong cách Giao diện:** Thiết kế tối giản, chuyên nghiệp với hệ thống HSL Dark-mode và bảng điều khiển giả lập kịch bản chạy thử (Tweaks Panel).

## 3. Bản đồ Tài liệu kỹ thuật (Documentation Index)

Dưới đây là sơ đồ hướng dẫn tra cứu tài liệu phục vụ cho các nhà phát triển và các AI Coding Agents:

* **Kiến trúc cốt lõi:**
  * [Tài liệu Kiến trúc hệ thống](./architecture.md): Tổng quan thiết kế luồng giao diện, bộ sinh dữ liệu và mô hình hoạt động.
  * [Phân tích cấu trúc thư mục](./source-tree-analysis.md): Sơ đồ chi tiết và giải thích chức năng từng thư mục/tệp tin mã nguồn.
* **Giao thức & Dữ liệu:**
  * [Mô hình dữ liệu (Data Models)](./data-models-frontend.md): Đặc tả chi tiết các interfaces trao đổi dữ liệu như Stock, News, Alert, KGNode.
  * [Giao thức kết nối & API](./api-contracts-frontend.md): Đặc tả cơ chế tích hợp và lộ trình chuyển đổi từ mock-data sang API thực tế.
* **Hướng dẫn vận hành:**
  * [Hướng dẫn phát triển cục bộ](./development-guide.md): Các bước cài đặt dự án, chạy dev server và biên dịch đóng gói sản phẩm.
  * [Danh mục thành phần UI](./component-inventory.md): Mô tả chi tiết các component UI cấu thành giao diện.
