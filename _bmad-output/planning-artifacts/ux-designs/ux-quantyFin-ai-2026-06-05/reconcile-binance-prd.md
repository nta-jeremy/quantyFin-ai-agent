# Báo cáo Đối chiếu Thiết kế (Reconciliation Report) - quantyFin-ai

Tài liệu đối chiếu sự đồng bộ giữa Yêu cầu sản phẩm (PRD), Hệ thống thiết kế tham chiếu (Binance Design System), và các quyết định thiết kế đã được ghi nhận trong `DESIGN.md` & `EXPERIENCE.md`.

## 1. Nguồn dữ liệu đối chiếu
*   **PRD:** `_bmad-output/planning-artifacts/prds/prd-quantyFin-ai-2026-06-03/prd.md` (FR-10: MVP Web UI, FR-9: Q&A Bot).
*   **Design System:** `docs/DESIGN-binance.md` (Giao diện tối, màu vàng Binance, hairlines, JetBrains Mono/Inter).

## 2. Đối chiếu chi tiết

| Yêu cầu gốc (PRD / Binance Spec) | Quyết định trong DESIGN.md / EXPERIENCE.md | Trạng thái |
| :--- | :--- | :--- |
| **Giao diện Web Dashboard MVP (FR-10)** | Định nghĩa bố cục 4 phân khu chính tại `EXPERIENCE.md` (Crawler, Agents Pipeline, Graph Visualizer, Q&A Assistant Console). | **Đã đáp ứng** |
| **Giao diện Chatbot & Q&A (FR-9)** | Thiết lập "Q&A Assistant Console" dạng panel chat tích hợp trực tiếp góc phải của Dashboard, cùng luồng dữ liệu trích dẫn nguồn tin. | **Đã đáp ứng** |
| **Nền tối sâu (Binance canvas-dark)** | Khởi tạo màu nền `#0B0E11` và màu thẻ `#1E2329` làm màu chủ đạo của Dashboard để tăng độ tương phản và hạn chế mỏi mắt. | **Đã đáp ứng** |
| **Màu vàng điểm nhấn (Binance primary)** | Thiết lập màu `#FCD535` cho các nút bấm hành động cốt lõi ("Run Now") và nhãn hiển thị số lượng thực thể quan trọng. | **Đã đáp ứng** |
| **Font Monospace cho số liệu (BinancePlex)** | Chỉ định phông JetBrains Mono / IBM Plex Mono cho toàn bộ dữ liệu số, Ticker, Sentiment Score tại `DESIGN.md` (Typography). | **Đã đáp ứng** |
| **Trạng thái cào tin (Active/Error)** | Sử dụng màu Trading Up (`#0ECB81` - Xanh lá) cho trạng thái cào tin thành công và Trading Down (`#F6465D` - Đỏ) cho lỗi crawler. | **Đã đáp ứng** |

## 3. Các ý kiến/Giả định đã được tích hợp
*   **Giả định về TG Bot:** Q&A Chat Console tích hợp trên Web sử dụng chung một lõi cơ chế phân tích tin tức và truy vấn với Telegram Bot để đảm bảo tính nhất quán của dữ liệu.
*   **Tối giản hóa (Minimalism):** Dashboard loại bỏ hoàn toàn các trang trí hoặc hiệu ứng đổ bóng mờ ảo, chỉ dùng ranh giới 1px `#2B3139` để phân cách các vùng, phù hợp với phong cách "flat" của Binance.
