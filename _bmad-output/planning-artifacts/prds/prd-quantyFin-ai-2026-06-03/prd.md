---
title: Product Requirements Document - quantyFin-ai
status: final
created: 2026-06-03
updated: 2026-06-04
---

# PRD: quantyFin-ai (Hệ thống phân tích chứng khoán AI dựa trên Knowledge Graph)

## 1. Tầm nhìn & Mục tiêu (Vision & Goals)
**Tầm nhìn:** Xây dựng một hệ thống phân tích chứng khoán tự động dành riêng cho thị trường Việt Nam. Hệ thống kết hợp sức mạnh của dữ liệu thị trường truyền thống và xử lý ngôn ngữ tự nhiên (đọc tin tức) để tạo thành một **Knowledge Graph** (Sơ đồ tri thức). Từ đó, AI có thể hiểu được các mối liên hệ chéo, nguyên nhân - kết quả và đưa ra những nhận định sâu sắc hơn.
**Mục tiêu cốt lõi:**
- Tự động hóa quá trình thu thập tin tức và dữ liệu giao dịch hàng ngày.
- Xây dựng và làm giàu Knowledge Graph chứng khoán Việt Nam một cách tự động.
- Trợ lý AI có khả năng phân tích, dự đoán xu hướng và đưa ra cảnh báo rủi ro cho danh mục đầu tư.

## 2. Đối tượng Người dùng (Target Audience)
- **Nhóm người dùng chính:** Sử dụng nội bộ (Bạn và một số ít nhà đầu tư F1).
- **Mức độ kỳ vọng:** Tập trung tối đa vào độ chính xác của luồng dữ liệu (data pipeline) và logic phân tích của AI. Không yêu cầu Giao diện người dùng (UI/UX) phức tạp hay hoàn hảo.

## 3. Các tính năng cốt lõi (Core Capabilities)

### 3.1. Pipeline Thu thập Dữ liệu (Data Ingestion)
- **FR-1: Thu thập Dữ liệu Giá & Chỉ số:** Tự động lấy dữ liệu giao dịch hàng ngày (OHLCV), chỉ báo kỹ thuật cơ bản từ thư viện `vn-stock` và các API miễn phí khác.
- **FR-2: Thu thập Tin tức (News Scraping):** Tự động "cào" và làm sạch tin tức từ các báo tài chính và tin tức chính thống có hỗ trợ RSS hoặc cào trực tiếp:
  - Các nguồn cào trực tiếp hoặc RSS bổ sung:
    1. **CafeF** (Cào trực tiếp chuyên mục chứng khoán/tài chính vĩ mô)
    2. **NDH** (Cào trực tiếp)
    3. **VnEconomy** (Hỗ trợ RSS: `https://vneconomy.vn/rss/chung-khoan.rss`)
    4. **Vietstock** (Hỗ trợ RSS: `https://vietstock.vn/rss/chung-khoan.rss`)
    5. **Báo Tuổi Trẻ** (Hỗ trợ RSS Kinh doanh: `https://tuoitre.vn/rss/kinh-doanh.rss`)
    6. **Báo Thanh Niên** (Hỗ trợ RSS Kinh tế: `https://thanhnien.vn/rss/kinh-te.rss`)
    7. **VnBusiness** (Hỗ trợ RSS Chứng khoán: `https://vnbusiness.vn/rss/chung-khoan.rss`)
- **FR-3: Lập lịch chạy tự động (Scheduling):** Pipeline thu thập tự động kích hoạt.
  - `[ASSUMPTION: Chạy batch 1 hoặc 2 lần/ngày (ví dụ sau giờ giao dịch 15:30) để tiết kiệm chi phí, thay vì chạy liên tục real-time]`

### 3.2. Xây dựng Knowledge Graph (Knowledge Graph Construction)
- **FR-4: Trích xuất thực thể (Entity Extraction):** Dùng AI/NLP để đọc tin tức và bóc tách: Mã cổ phiếu (Ticker), Công ty, Lãnh đạo, Ngành nghề, Sự kiện vĩ mô.
- **FR-5: Xây dựng mối quan hệ (Relationship Mapping):** Gắn kết các thông tin. (Ví dụ: "Sự kiện A" -> [TÁC_ĐỘNG_TIÊU_CỰC_LÊN] -> "Ngành B" -> [CÓ_CỔ_PHIẾU] -> "Mã XYZ").
- **FR-6: Lưu trữ dữ liệu:** Lưu trữ cấu trúc Graph để phục vụ truy vấn.
  - `[ASSUMPTION: Sẽ sử dụng Graph Database (như Neo4j) kết hợp với Vector Database để hệ thống AI có thể dễ dàng tìm kiếm ngữ nghĩa (semantic search)]`

### 3.3. Phân tích AI & Cảnh báo (AI Analysis & Alerts)
- **FR-7: Đánh giá tâm lý thị trường (Sentiment Analysis):** Chấm điểm cảm xúc (tích cực/tiêu cực/trung tính) của tin tức tác động lên từng mã cổ phiếu cụ thể.
- **FR-8: Tổng hợp & Cảnh báo Rủi ro:** Tự động phát hiện các chuỗi sự kiện rủi ro lây lan (thông qua Graph) hoặc các điểm bất thường, sau đó gửi cảnh báo.
  - `[ASSUMPTION: Cảnh báo sẽ được gửi qua Telegram Bot để nhóm F1 nhận được nhanh chóng và tiện lợi nhất]`
- **FR-9: Trợ lý Truy vấn (Q&A Bot):** Giao diện chat cho phép người dùng hỏi trực tiếp (VD: "Có tin xấu nào ảnh hưởng tới dòng Thép hôm nay không?"). AI sẽ dùng Knowledge Graph để trả lời kèm trích dẫn nguồn.

### 3.4. Giao diện Web (Web Dashboard)
- **FR-10: Giao diện cơ bản (MVP Web UI):** Cung cấp một Web Dashboard đơn giản (ví dụ: dùng Streamlit hoặc Next.js) để:
  - Trực quan hóa Knowledge Graph.
  - Hiển thị các biểu đồ kỹ thuật và tin tức tổng hợp cơ bản.
  - Đóng vai trò là trung tâm theo dõi bên cạnh các cảnh báo nhanh qua Telegram.

## 4. Yêu cầu Phi chức năng (Non-Functional Requirements)
- **Chi phí (Cost-efficiency):** Tận dụng tối đa công cụ mã nguồn mở và API miễn phí.
  - `[ASSUMPTION: Pipeline NLP trích xuất dữ liệu lớn sẽ dùng LLM giá rẻ (như GPT-4o-mini / Gemini Flash) hoặc các model local nhỏ, chỉ dùng model xịn (như GPT-4o/Claude 3.5 Sonnet) ở bước tóm tắt phân tích cuối cùng]`
- **Bảo mật nội bộ:** Dữ liệu Knowledge Graph là tài sản nội bộ, chỉ giới hạn quyền truy cập cho nhóm nhỏ.
- **Khả năng mở rộng:** Kiến trúc dạng module, dễ dàng thêm một nguồn báo (crawler) mới mà không ảnh hưởng tới hệ thống chung.

## 5. Ngoài phạm vi (Out of Scope)
- Không có tính năng tự động đặt lệnh mua bán vào hệ thống công ty chứng khoán (No Auto-trading).
- Không phục vụ giao dịch tần suất cao (HFT) yêu cầu dữ liệu mili-giây.
