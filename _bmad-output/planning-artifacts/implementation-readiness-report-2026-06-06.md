---
stepsCompleted:
  - "Step 1: Document Discovery"
  - "Step 2: PRD Analysis"
filesIncluded:
  prd: "/Users/tunganh252/Desktop/Projects/Finance/quantyFin-ai-agent/_bmad-output/planning-artifacts/prds/prd-quantyFin-ai-2026-06-03/prd.md"
  architecture: "/Users/tunganh252/Desktop/Projects/Finance/quantyFin-ai-agent/_bmad-output/planning-artifacts/architecture.md"
  epics: "/Users/tunganh252/Desktop/Projects/Finance/quantyFin-ai-agent/_bmad-output/planning-artifacts/epics.md"
  ux_design: "/Users/tunganh252/Desktop/Projects/Finance/quantyFin-ai-agent/_bmad-output/planning-artifacts/ux-designs/run-2026-06-05/"
---

# Implementation Readiness Assessment Report

**Date:** 2026-06-06
**Project:** quantyFin-ai

## 1. Kiểm kê tài liệu (Document Inventory)

Dưới đây là danh sách các tài liệu dự án được tìm thấy và sử dụng cho việc đánh giá:

### Tài liệu PRD
- **Tập tin:** [prd.md](file:///Users/tunganh252/Desktop/Projects/Finance/quantyFin-ai-agent/_bmad-output/planning-artifacts/prds/prd-quantyFin-ai-2026-06-03/prd.md)
  - Kích thước: 6868 bytes
  - Ngày sửa đổi: 05/06/2026 23:50

### Tài liệu Kiến trúc (Architecture)
- **Tập tin:** [architecture.md](file:///Users/tunganh252/Desktop/Projects/Finance/quantyFin-ai-agent/_bmad-output/planning-artifacts/architecture.md)
  - Kích thước: 37965 bytes
  - Ngày sửa đổi: 05/06/2026 09:04

### Tài liệu Epics & Stories
- **Tập tin:** [epics.md](file:///Users/tunganh252/Desktop/Projects/Finance/quantyFin-ai-agent/_bmad-output/planning-artifacts/epics.md)
  - Kích thước: 22158 bytes
  - Ngày sửa đổi: 05/06/2026 23:52

### Tài liệu Thiết kế UX (UX Design)
- **Folder:** [ux-designs/run-2026-06-05/](file:///Users/tunganh252/Desktop/Projects/Finance/quantyFin-ai-agent/_bmad-output/planning-artifacts/ux-designs/run-2026-06-05/)
  - [DESIGN.md](file:///Users/tunganh252/Desktop/Projects/Finance/quantyFin-ai-agent/_bmad-output/planning-artifacts/ux-designs/run-2026-06-05/DESIGN.md) (2383 bytes)
  - [EXPERIENCE.md](file:///Users/tunganh252/Desktop/Projects/Finance/quantyFin-ai-agent/_bmad-output/planning-artifacts/ux-designs/run-2026-06-05/EXPERIENCE.md) (3467 bytes)

## 2. Phân tích tài liệu PRD (PRD Analysis)

### Yêu cầu chức năng (Functional Requirements - FRs)

*   **FR-1: Thu thập Dữ liệu Giá & Chỉ số**
    *   Tự động lấy dữ liệu giao dịch hàng ngày (OHLCV) và các chỉ báo kỹ thuật cơ bản từ thư viện `vn-stock` hoặc các API miễn phí khác.
*   **FR-2: Thu thập Tin tức (News Scraping)**
    *   Tự động "cào" và làm sạch tin tức từ các báo tài chính và tin chính thống qua RSS hoặc cào trực tiếp từ các nguồn: CafeF, NDH, VnEconomy (RSS), Vietstock (RSS), Báo Tuổi Trẻ (RSS), Báo Thanh Niên (RSS), VnBusiness (RSS).
*   **FR-3: Lập lịch chạy tự động (Scheduling)**
    *   Pipeline thu thập tự động kích hoạt theo dạng batch (1 hoặc 2 lần/ngày, ví dụ sau giờ giao dịch 15:30) để tiết kiệm chi phí.
*   **FR-4: Trích xuất thực thể (Entity Extraction)**
    *   Dùng AI/NLP (mô hình chi phí thấp) để đọc tin tức và bóc tách thực thể: Mã cổ phiếu (Ticker), Công ty, Lãnh đạo, Ngành nghề, Sự kiện vĩ mô.
*   **FR-5: Xây dựng mối quan hệ (Relationship Mapping)**
    *   Gắn kết các thực thể tin tức thành mối quan hệ logic (Ví dụ: "Sự kiện A" -> [TÁC_ĐỘNG_TIÊU_CỰC_LÊN] -> "Ngành B" -> [CÓ_CỔ_PHIẾU] -> "Mã XYZ").
*   **FR-6: Lưu trữ dữ liệu (Storage)**
    *   Lưu trữ cấu trúc đồ thị (sử dụng Graph Database như Neo4j kết hợp Vector Database) phục vụ truy vấn ngữ nghĩa (semantic search).
*   **FR-7: Đánh giá tâm lý thị trường (Sentiment Analysis)**
    *   Chấm điểm cảm xúc (tích cực/tiêu cực/trung tính) của tin tức tác động lên từng mã cổ phiếu cụ thể.
*   **FR-8: Tổng hợp & Cảnh báo Rủi ro**
    *   Tự động phát hiện các chuỗi sự kiện rủi ro lây lan qua đồ thị hoặc các điểm bất thường, gửi cảnh báo qua Telegram Bot tới nhóm F1.
*   **FR-9: Trợ lý Truy vấn (Q&A Bot)**
    *   Giao diện chat cho phép truy vấn trực tiếp (Ví dụ: "Có tin xấu nào ảnh hưởng tới dòng Thép hôm nay không?"), AI sử dụng Knowledge Graph để trả lời kèm trích dẫn nguồn.
    *   Tích hợp bộ UI kit `quantyFin-ai` hỗ trợ các hiệu ứng Prompt, halo, mức độ tự tin (confidence score), và diff view hiển thị dữ liệu tài chính.
*   **FR-10: Giao diện Web (Web Dashboard)**
    *   Xây dựng giao diện AI-Native bằng React/Next.js và Tailwind v4 + shadcn.
    *   Tuân thủ cấu trúc 3 lớp của **QuantyFin Design System** (Foundation -> Surface adapters -> UI kits).
    *   Sử dụng bề mặt `[data-surface="app"]` cho dashboard (tỉ lệ chữ 13.5px / 1.5) và `[data-surface="portal"]` cho các báo cáo tổng hợp.
    *   Phông chữ: `Be Vietnam Pro`, `JetBrains Mono` (mã cổ phiếu, trạng thái), `Montserrat` (tiêu đề).
    *   Hệ màu: `--brand` (navy #2a2b86), `--iris` (AI default #7c6cf5), `--mint` (Tích cực), `--gap` (Tiêu cực/Cảnh báo).
    *   Trực quan hóa đồ thị và dữ liệu bằng các Chart/Card UI (`quantyFin-app` kit).

**Tổng số yêu cầu chức năng:** 10 FRs

### Yêu cầu phi chức năng (Non-Functional Requirements - NFRs)

*   **NFR-1: Tối ưu chi phí (Cost-efficiency)**
    *   Tận dụng tối đa công cụ mã nguồn mở và API miễn phí. Sử dụng mô hình AI giá rẻ (như GPT-4o-mini, Gemini Flash hoặc local model) cho bước xử lý NLP/trích xuất thực thể hàng loạt, và chỉ sử dụng mô hình cao cấp (GPT-4o, Claude 3.5 Sonnet) cho bước tóm tắt phân tích cuối cùng.
*   **NFR-2: Bảo mật nội bộ (Security)**
    *   Dữ liệu Knowledge Graph là tài sản nội bộ, chỉ giới hạn quyền truy cập cho nhóm người dùng nhỏ (F1).
*   **NFR-3: Khả năng mở rộng (Extensibility)**
    *   Thiết kế kiến trúc dạng module để dễ dàng tích hợp thêm nguồn báo mới (crawler) mà không ảnh hưởng tới toàn bộ hệ thống.

**Tổng số yêu cầu phi chức năng:** 3 NFRs

### Yêu cầu bổ sung & Giả định (Additional Requirements & Assumptions)
*   **Giả định 1 (Batch Processing):** Pipeline thu thập tin tức chạy batch 1-2 lần/ngày sau giờ giao dịch (15:30) thay vì real-time.
*   **Giả định 2 (Graph + Vector DB):** Kết hợp Neo4j và Vector Database để tối ưu hóa truy vấn ngữ nghĩa.
*   **Giả định 3 (Telegram Bot):** Chọn Telegram làm kênh gửi cảnh báo nhanh.
*   **Ngoài phạm vi (Out of Scope):** Không hỗ trợ đặt lệnh giao dịch tự động (No auto-trading) và không phục vụ giao dịch tần suất cao (HFT).

### Đánh giá tính đầy đủ của PRD (PRD Completeness Assessment)
*   PRD được biên soạn rất rõ ràng và chi tiết, đặc biệt là phần định nghĩa các nguồn tin cần cào (CafeF, NDH, RSS VnEconomy, Vietstock,...) và các yêu cầu cụ thể của QuantyFin Design System.
*   Các chức năng cốt lõi được định nghĩa tường minh bằng các mã yêu cầu (FR-1 đến FR-10).
*   Các giả định và phần "ngoài phạm vi" giúp khoanh vùng bài toán rõ ràng, giảm thiểu rủi ro phình to phạm vi (scope creep).
