---
title: Product Requirements Document - QuantyFin
status: draft
created: 2026-06-03
updated: 2026-06-06
---

# PRD — QuantyFin: AI Agentic Platform Phân Tích Chứng Khoán Việt Nam

**Slogan:** AI Agentic Platform for Vietnam Capital Markets  
**Loại sản phẩm:** SaaS Web App — Single-Page Application (SPA), standalone deployment  
**Phiên bản:** 1.1  
**Trạng thái:** Draft — đang hoàn thiện  

---

## 1. Tổng quan sản phẩm (Product Overview)
QuantyFin là nền tảng phân tích chứng khoán thị trường Việt Nam được tích hợp trí tuệ nhân tạo (AI) theo mô hình agentic. Platform cung cấp cho nhà đầu tư cá nhân và chuyên nghiệp các công cụ phân tích thị trường theo thời gian thực, bao gồm: dashboard tổng quan thị trường, phân tích cổ phiếu đơn lẻ, theo dõi tin tức, hệ thống cảnh báo thông minh, Sơ đồ tri thức (Knowledge Graph) biểu diễn mối quan hệ giữa các thực thể thị trường, và giao diện chat với AI agent.

### 1.1 Brand Identity
- **Màu sắc chủ đạo (Primary color):** `#2a2b86` (deep navy blue)
- **Màu nhấn (Accent color):** `#fcaf16` (gold/amber)
- **Giao diện (Theme):** Light (mặc định) / Dark mode
- **Typography:** Phông chữ mặc định: `Be Vietnam Pro` (thân bài), `JetBrains Mono` (mã cổ phiếu, trạng thái), `Montserrat` (tiêu đề lớn).

### 1.2 Mô hình Triển khai (Deployment Model)
Trong phiên bản Prototype hiện tại, nền tảng được đóng gói dưới dạng **self-contained HTML artifact** — toàn bộ ứng dụng (React, các UI components, mock data) được đóng gói trong một file HTML duy nhất, không phụ thuộc vào CDN hay API bên ngoài. Các phiên bản tiếp theo sẽ chuyển dần sang mô hình Client-Server hoàn chỉnh.

---

## 2. Tầm nhìn & Mục tiêu (Vision & Goals)

### 2.1 Tầm nhìn (Vision)
Trở thành "Bloomberg terminal" dành cho nhà đầu tư Việt Nam — với trải nghiệm người dùng (UX) thân thiện, AI-native và khả năng phân tích thị trường sâu sắc theo ngữ cảnh kinh tế vĩ mô và sơ đồ tri thức Việt Nam.

### 2.2 Mục tiêu sản phẩm (Product Goals)
1. **Tự động hóa dữ liệu & Tin tức:** Tự động hóa quá trình thu thập tin tức và dữ liệu giao dịch hàng ngày để xây dựng và làm giàu Knowledge Graph chứng khoán Việt Nam.
2. **Trực quan hóa kịch bản (Scenario Analysis):** Cho phép nhà đầu tư nhanh chóng chuyển đổi giữa 4 trạng thái thị trường (up/down/volatile/crisis) để xem phân tích phù hợp với từng bối cảnh.
3. **Động cơ Phân tích Tri thức (Knowledge Graph):** Biểu diễn mối quan hệ phức tạp giữa cổ phiếu, sự kiện, ngành, và tin tức dưới dạng đồ thị tương tác nhằm tối ưu hóa khả năng hiểu chéo của AI.
4. **Trợ lý AI Chat Agent:** Cung cấp giao diện hỏi đáp tự nhiên về phân tích cổ phiếu và thị trường dựa trên sơ đồ tri thức.
5. **Cảnh báo thông minh (Real-time Alerts):** Hệ thống cảnh báo tự động khi phát hiện rủi ro lây lan qua sơ đồ tri thức hoặc các điểm biến động bất thường.
6. **Cấu hình linh hoạt (Configurable AI):** Cho phép người dùng cấu hình LLM Gateway, nguồn dữ liệu và các tham số AI agent trực tiếp từ giao diện.

### 2.3 Chỉ số Thành công (Success Metrics / KPIs)
- **Thời gian sử dụng trung bình trên Dashboard:** > 5 phút/phiên.
- **Tỷ lệ chuyển đổi Chat → Xem chi tiết cổ phiếu:** > 30%.
- **Tỷ lệ tương tác với cảnh báo (Alert engagement rate):** > 60% cảnh báo được nhấp vào.
- **Độ sâu tương tác trên sơ đồ tri thức (Knowledge Graph session depth):** > 3 nodes/phiên.

---

## 3. Đối tượng Người dùng (User Personas)

### 3.1 Nhà đầu tư cá nhân (Retail Investor)
- **Mô tả:** Người dùng phổ thông, có kiến thức cơ bản về chứng khoán, muốn theo dõi danh mục và nhận cảnh báo tự động nhanh chóng qua giao diện Web hoặc Telegram Bot.
- **Nhu cầu:** Xem nhanh tình hình thị trường tổng thể; Nhận cảnh báo khi cổ phiếu đạt ngưỡng; Đọc tin tức và phân tích AI về danh mục đang nắm giữ.
- **Điểm đau (Pain points):** Tra cứu từ quá nhiều nguồn rời rạc; Khó đánh giá mối quan hệ nhân quả giữa tin tức vĩ mô và biến động giá cổ phiếu.

### 3.2 Nhà phân tích chứng khoán (Analyst)
- **Mô tả:** Chuyên gia tài chính, cần các công cụ phân tích sâu sắc hơn và có khả năng tùy biến quy trình làm việc (workflow) riêng.
- **Nhu cầu:** Phân tích kỹ thuật và cơ bản; So sánh hiệu suất ngành (sector comparison); Sử dụng Knowledge Graph để truy vết các sự kiện chuỗi cung ứng hoặc ảnh hưởng chéo.
- **Điểm đau:** Các công cụ phân tích hiện tại không liên kết dữ liệu cấu trúc với tin tức phi cấu trúc; Thiếu sơ đồ tri thức cho thị trường VN.

### 3.3 Nhà quản lý quỹ (Fund Manager)
- **Mô tả:** Người quản lý danh mục quy mô lớn, cần giám sát liên tục và phân tích tác động vĩ mô (macro analysis).
- **Nhu cầu:** Theo dõi nhiều cổ phiếu đồng thời; Phân tích theo kịch bản thị trường để phòng ngừa rủi ro (hedging); Tự động hóa tạo báo cáo định kỳ qua background jobs.

---

## 4. Các tính năng cốt lõi (Core Capabilities)

### 4.1. Hệ thống Thu thập Dữ liệu (Data Ingestion & Pipeline)
- **FR-1: Thu thập Dữ liệu Giá & Chỉ số:** Tự động lấy dữ liệu giao dịch hàng ngày (OHLCV) và chỉ báo kỹ thuật cơ bản từ thư viện `vn-stock` hoặc các nguồn dữ liệu tương đương.
- **FR-2: Thu thập Tin tức (News Scraping):** Tự động cào và làm sạch tin tức từ các nguồn hỗ trợ RSS hoặc cào trực tiếp:
  - CafeF (chuyên mục chứng khoán/tài chính vĩ mô)
  - NDH
  - VnEconomy (RSS: `https://vneconomy.vn/rss/chung-khoan.rss`)
  - Vietstock (RSS: `https://vietstock.vn/rss/chung-khoan.rss`)
  - Tuổi Trẻ (Kinh doanh RSS: `https://tuoitre.vn/rss/kinh-doanh.rss`)
  - Thanh Niên (Kinh tế RSS: `https://thanhnien.vn/rss/kinh-te.rss`)
  - VnBusiness (Chứng khoán RSS: `https://vnbusiness.vn/rss/chung-khoan.rss`)
- **FR-3: Lập lịch chạy tự động (Scheduling):** Pipeline thu thập tự động chạy định kỳ.
  - `[ASSUMPTION: Chạy batch 1 hoặc 2 lần/ngày (ví dụ sau giờ giao dịch 15:30) để tiết kiệm tài nguyên, thay vì chạy liên tục real-time trong giai đoạn đầu]`

### 4.2. Xây dựng Sơ đồ Tri thức (Knowledge Graph Construction)
- **FR-4: Trích xuất thực thể (Entity Extraction):** Sử dụng AI/NLP để đọc tin tức và trích xuất: Mã cổ phiếu (Ticker), Công ty, Lãnh đạo, Ngành nghề, Sự kiện vĩ mô.
- **FR-5: Xây dựng mối quan hệ (Relationship Mapping):** Kết nối các thực thể (Ví dụ: "Sự kiện A" -> [TÁC_ĐỘNG_TIÊU_CỰC_LÊN] -> "Ngành B" -> [CÓ_CỔ_PHIẾU] -> "Mã XYZ").
- **FR-6: Lưu trữ cấu trúc Graph:** Lưu trữ dữ liệu đồ thị dưới dạng Graph Database kết hợp với Vector Database để phục vụ tìm kiếm ngữ nghĩa (semantic search).
  - `[ASSUMPTION: Giai đoạn sản xuất sẽ sử dụng Neo4j kết hợp Vector Database làm hạ tầng lưu trữ]`

### 4.3. Các Màn hình & Tính năng Giao diện Web (Web Dashboard & 9 Screens)
Giao diện ứng dụng được tổ chức thành một Shell điều hướng chung gồm SideRail (thanh điều hướng trái) và Topbar (thanh tiêu đề trên), chứa 9 màn hình chức năng chi tiết:

- **FR-7: SideRail & Topbar (Navigation Shell):**
  - **SideRail:** Gồm các nút điều hướng chuyển màn hình: Dashboard, Knowledge Graph, Stock Detail, News, Chat, Alerts (có kèm badge hiển thị số lượng cảnh báo chưa đọc từ `data.alerts.length`), Jobs, Settings.
  - **Topbar:** Hiển thị Logo, Bộ chọn kịch bản thị trường (Scenario Switcher - 4 trạng thái), Nút Tìm kiếm nhanh (chuyển sang Chat) và Nút Đăng xuất.
- **FR-8: Màn hình Đăng nhập (Login Screen):**
  - Cung cấp form xác thực người dùng (Email/Username và Password).
  - Trải nghiệm đăng nhập trong bản Prototype: tự động đăng nhập khi truy cập lần đầu nếu `qf_auth = null`, lưu trạng thái vào `localStorage`.
- **FR-9: Màn hình Dashboard (Tổng quan thị trường):**
  - **Market Summary:** Hiển thị chỉ số VN-Index, HNX, UPCoM với màu sắc tương ứng theo kịch bản thị trường hiện tại.
  - **Top Movers:** Danh sách các cổ phiếu tăng/giảm mạnh nhất, click vào mã cổ phiếu để xem chi tiết.
  - **Portfolio Snapshot:** Tóm tắt danh mục theo dõi.
  - **Recent Alerts & News Teaser:** Hiển thị nhanh các cảnh báo và tin tức nổi bật.
- **FR-10: Màn hình Sơ đồ Tri thức (Knowledge Graph Screen):**
  - Hiển thị đồ thị liên kết thực thể dạng force-directed bằng thư viện D3.js.
  - Phân loại màu sắc các nút thực thể:
    - **Sự kiện (Event):** Màu vàng hổ phách (`#fcaf16`).
    - **Mã cổ phiếu / Công ty (Ticker/Company):** Màu xanh Navy.
    - **Tin tức (News) & Ngành (Sector):** Các màu sắc bổ trợ theo hệ thống thiết kế.
  - **Tương tác:** Hỗ trợ kéo thả (Pan), phóng to/thu nhỏ (Zoom), nhấp vào nút cổ phiếu để chuyển sang màn hình Chi tiết cổ phiếu, nhấp vào nút Sự kiện/Tin tức để mở panel chi tiết.
- **FR-11: Màn hình Chi tiết Cổ phiếu (Stock Detail Screen):**
  - Hiển thị thông tin mã cổ phiếu: Giá hiện tại, % thay đổi, khối lượng giao dịch.
  - **Biểu đồ giá:** Biểu đồ giá lịch sử dạng line chart hoặc nến.
  - **AI Confidence Indicator:** Chỉ báo hiển thị mức độ tin cậy của phân tích AI (có thể ẩn thông qua cấu hình UI).
  - **Phân tích của AI & Các chỉ số tài chính:** P/E, EPS, Vốn hóa, Tỷ suất cổ tức và tóm tắt nhận định của AI.
  - **Danh sách liên quan:** Cổ phiếu cùng ngành, tin tức liên quan đến mã.
- **FR-12: Màn hình Tin tức (News Screen):**
  - Danh sách tin tức tài chính được gán nhãn Sentiment bởi AI (Positive - Tích cực, Neutral - Trung tính, Negative - Tiêu cực).
  - Hỗ trợ bộ lọc tin tức theo ngành (sector), theo mã cổ phiếu và loại tin tức (vĩ mô, doanh nghiệp, pháp lý).
- **FR-13: Giao diện Chat với Trợ lý AI (Chat Screen):**
  - Giao diện chat dạng bong bóng thoại (bubble chat UI).
  - Gợi ý sẵn các câu lệnh nhanh (Quick Prompts).
  - **Tự động nhận diện mã cổ phiếu:** Khi AI nhắc đến các mã cổ phiếu trong câu trả lời, hệ thống tự động bôi đậm và chuyển thành link liên kết nhấp chuột để chuyển nhanh sang màn hình Stock Detail.
- **FR-14: Màn hình Quản lý Cảnh báo (Alerts Screen):**
  - Hiển thị danh sách các cảnh báo đang được kích hoạt (Triggered Alerts) với các mức độ: Critical (Nghiêm trọng), Warning (Cảnh báo), Info (Thông tin).
  - Form cho phép tạo mới các quy tắc cảnh báo dựa trên: mục tiêu giá, đột biến khối lượng hoặc từ khóa tin tức.
  - Cho phép Đóng (Dismiss) hoặc Xem chi tiết cảnh báo.
- **FR-15: Màn hình Tác vụ Chạy nền (Background Jobs Screen):**
  - Quản lý các tác vụ AI nền như: Phân tích danh mục định kỳ, quét sentiment toàn thị trường, tổng hợp báo cáo kết quả kinh doanh.
  - Hiển thị trạng thái đang chạy (Running với tiến trình progress bar) hoặc đã hoàn thành (Completed) kèm chi tiết kết quả.
- **FR-16: Màn hình Cấu hình Hệ thống (Settings Screen):**
  - Giao diện cấu hình chia theo nhóm (AI & Dữ liệu, Giao diện, Thông báo, Tài khoản, Nâng cao).
  - **Cấu hình LLM Gateway:** Cho phép điền API Endpoint, API Key, lựa chọn model (GPT-4, Claude 3, Gemini) và các tham số sinh văn bản (temperature, max tokens).

### 4.4. Tích hợp Đa kênh & Cảnh báo nâng cao
- **FR-17: Tích hợp Telegram Bot:** AI phân tích tự động gửi cảnh báo rủi ro danh mục và hỗ trợ truy vấn nhanh thông qua kênh Telegram dành cho các nhà đầu tư nội bộ.
  - `[ASSUMPTION: Sử dụng Telegram làm kênh tương tác chính cho các thông báo khẩn cấp và truy vấn di động nhanh]`

---

## 5. Kiến trúc kỹ thuật & Trạng thái (Technical Architecture)

### 5.1 Kiến trúc ứng dụng Prototype (Phase 1)
Bản Prototype hiện tại được triển khai hoàn toàn dưới dạng giao diện tĩnh chạy phía Client trong một file HTML:
- **UI Framework:** React 18 (sử dụng Babel standalone để biên dịch JSX trực tiếp trên trình duyệt).
- **Quản lý trạng thái:** React Local State và luồng dữ liệu một chiều (Props drilling).
- **Sơ đồ tri thức:** Trực quan hóa D3.js force-directed (nằm trong module `KGViewer`).
- **Lưu trữ cục bộ:** Sử dụng `localStorage` để lưu thông tin đăng nhập và tùy chỉnh hiển thị.

### 5.2 Trạng thái toàn cục (Global State)
- `authed`: boolean (trạng thái đăng nhập).
- `screen`: string (màn hình hiện tại, ví dụ: `'dashboard'`, `'kg'`, `'stock'`).
- `ticker`: string (mã cổ phiếu đang được chọn phân tích, mặc định là `'FPT'`).
- `tweaks.theme`: `'light'` | `'dark'` (theme hiện tại).
- `tweaks.scenario`: `'up'` | `'down'` | `'volatile'` | `'crisis'` (kịch bản thị trường hiện tại).
- `tweaks.showConfidence`: boolean (ẩn/hiển thị mức độ tin cậy AI).

### 5.3 Tổ chức Asset Bundle (Prototype)
- `24ec1f5a`: Root component (App entry point).
- `b4d9a841`: Chứa mã nguồn của 9 Screens chính.
- `c1106d82`: Settings screen (các form logic).
- `5ff38e32`: Mock data dữ liệu thị trường và kịch bản.
- `c9de8dcd`: Shared UI components và các Icons dạng SVG.
- `e1abcd1f`: Module Knowledge Graph D3.js (`KGViewer`).

---

## 6. Mô hình Dữ liệu & Kịch bản Thị trường (Data Model & Scenarios)

### 6.1 API Sinh Dữ liệu Mock
```typescript
window.QF_DATA = {
  build(scenario: 'up' | 'down' | 'volatile' | 'crisis'): DataObject
}
```
Khi kịch bản thay đổi từ thanh Topbar, ứng dụng sẽ gọi lại hàm này để sinh toàn bộ dữ liệu mock phù hợp với kịch bản đó nhằm đảm bảo giao diện hiển thị đúng trạng thái.

### 6.2 Các kịch bản thị trường (Market Scenarios)
- **up (Thị trường tăng trưởng):** Chỉ số tăng mạnh, rủi ro thấp, màu chủ đạo xanh lá.
- **down (Thị trường sụt giảm):** Chỉ số giảm, rủi ro cao, màu chủ đạo đỏ.
- **volatile (Thị trường biến động):** Thị trường đi ngang/dao động, rủi ro trung bình, màu chủ đạo vàng/cam. (Đây là kịch bản mặc định).
- **crisis (Khủng hoảng thị trường):** Chỉ số giảm sâu, rủi ro rất cao, màu chủ đạo đỏ đậm.

---

## 7. Các luồng người dùng chính (User Flows)

### 7.1 Luồng đăng nhập (Login Flow)
1. Người dùng truy cập ứng dụng lần đầu -> `qf_auth = null` -> Hệ thống tự động chuyển đổi thành trạng thái đã đăng nhập và hiển thị Dashboard.
2. Nếu người dùng chủ động Đăng xuất -> `qf_auth` chuyển thành `'0'` -> Chuyển hướng sang màn hình Login.
3. Người dùng điền Username/Password -> Nhấp "Đăng nhập" -> `qf_auth = '1'` -> Chuyển về Dashboard.

### 7.2 Luồng phân tích kịch bản thị trường (Market Analysis Flow)
1. Từ Dashboard, người dùng chọn kịch bản `"crisis"` trên Topbar.
2. Dữ liệu `QF_DATA` tự động tính toán lại theo trạng thái crisis.
3. Dashboard hiển thị các mã giảm sâu nhất. Người dùng click mã `"VCB"`.
4. Giao diện chuyển sang màn hình Stock Detail hiển thị phân tích VCB dưới góc độ khủng hoảng kèm các chỉ báo tin cậy và tin tức liên quan.

### 7.3 Luồng khám phá Sơ đồ Tri thức (KG Exploration Flow)
1. Người dùng nhấp chọn `"Knowledge Graph"` từ SideRail.
2. Sơ đồ thực thể tương tác mở ra, hiển thị các liên kết.
3. Người dùng click chọn nút Sự kiện `"Kết quả kinh doanh Q1/2026"` màu vàng để xem thông tin chi tiết trên side panel.
4. Người dùng click chọn một nút mã cổ phiếu `"FPT"`, hệ thống tự động chuyển hướng sang màn hình Stock Detail của FPT.

---

## 8. Yêu cầu phi chức năng (Non-Functional Requirements)

- **Hiệu năng (Performance):**
  - Thời gian tải trang ban đầu (Prototype HTML độc lập) < 3 giây trên kết nối mạng 4G.
  - Thời gian chuyển đổi kịch bản thị trường < 100ms.
  - Thời gian phản hồi chat (bản sản xuất) < 5 giây.
- **Khả năng tiếp cận (Accessibility - a11y):**
  - Đảm bảo độ tương phản màu sắc đạt chuẩn WCAG AA cho các đoạn text trên nền màu thương hiệu `#2a2b86`.
  - Hỗ trợ điều hướng bằng bàn phím trên SideRail và Topbar.
- **Responsive Design:**
  - Desktop (>1200px): Hiển thị đầy đủ SideRail, Topbar và Content.
  - Tablet (768px - 1200px): Thu gọn SideRail thành dạng chỉ hiển thị Icon.
  - Mobile (<768px): SideRail chuyển thành thanh điều hướng dưới cùng (Bottom navigation), hạn chế một số tính năng phức tạp như D3 Graph.
- **Bảo mật (Security - Bản sản xuất):**
  - Thay thế xác thực đơn giản bằng JWT Token có thời gian hết hạn.
  - Không lưu trữ API Key của LLM Gateway ở phía client, thực hiện proxy qua backend để đảm bảo bảo mật.
  - Vệ sinh đầu vào (Sanitize) để ngăn chặn các cuộc tấn công XSS.

---

## 9. Lộ trình phát triển & Phân kỳ (Roadmap)

### Phase 1 — Prototype (Hiện tại)
- **Mục tiêu:** Xây dựng bản demo độc lập chạy hoàn toàn phía Client.
- **Đầu ra:** File tĩnh tự chứa `QuantyFin_Standalone.html`.
- **Phạm vi:** 9 màn hình chức năng chạy dữ liệu mock theo 4 kịch bản, tích hợp D3 Knowledge Graph và cấu hình giao diện.

### Phase 2 — Tích hợp Backend & Dữ liệu thực (MVP Backend Integration)
- **Mục tiêu:** Kết nối hệ thống với dữ liệu thị trường và hạ tầng lưu trữ thực tế.
- **Phạm vi:**
  - Phát triển Backend API (Node.js/FastAPI) và cơ sở dữ liệu lưu trữ cấu hình người dùng, danh mục theo theo dõi.
  - Tích hợp cổng dữ liệu giá chứng khoán Việt Nam (HSX, HNX) thời gian thực.
  - Kết nối LLM Gateway thực tế.
  - Triển khai pipeline thu thập tin tức tự động và trích xuất thực thể để lưu trữ vào Neo4j Graph Database.

### Phase 3 — Tính năng AI Nâng cao (Advanced AI Features)
- **Mục tiêu:** Triển khai các khả năng thông minh độc quyền của Agent.
- **Phạm vi:**
  - Triển khai RAG từ các tài liệu tài chính doanh nghiệp Việt Nam.
  - Tạo lập và quản lý các tác vụ nền tự động phân tích sâu.
  - Tích hợp Telegram Bot cho phép nhận cảnh báo rủi ro lan truyền qua sơ đồ tri thức và trả lời câu hỏi trực tiếp.

### Phase 4 — Mở rộng & Hệ sinh thái (Scale & Ecosystem)
- **Mục tiêu:** Mở rộng quy mô người dùng và phát triển hệ sinh thái.
- **Phạm vi:** 
  - Xây dựng ứng dụng di động (React Native).
  - Cung cấp cổng API cho nhà phát triển khác và hỗ trợ các tính năng làm việc nhóm.

---

## 10. Phụ lục kỹ thuật (Technical Appendices)

### 10.1 Component Props Reference
```typescript
interface SideRailProps { active: string; onNav: (s: string) => void; alertCount: number }
interface TopbarProps   { scenario: string; onScenario: (s: string) => void; onSearch: () => void; onLogout: () => void; screen: string }

interface LoginScreenProps     { onSignIn: () => void }
interface DashboardScreenProps { data: DataObject; onNav: (s: string) => void; onTicker: (t: string) => void; scenario: string }
interface KGScreenProps        { onTicker: (t: string) => void }
interface StockScreenProps     { data: DataObject; ticker: string; onTicker: (t: string) => void }
interface NewsScreenProps      { data: DataObject; onTicker: (t: string) => void }
interface ChatScreenProps      { onTicker: (t: string) => void }
interface AlertsScreenProps    { data: DataObject; onTicker: (t: string) => void }
interface JobsScreenProps      { data: DataObject }
interface SettingsScreenProps  {} // Tự quản lý state cấu hình
```

### 10.2 Sơ đồ điều hướng màn hình (Screen Navigation Map)
- **Login** chuyển sang **Dashboard** khi đăng nhập thành công.
- Các màn hình **Dashboard, Stock Detail, KG, News, Chat, Alerts** đều hỗ trợ hàm gọi `onTicker(ticker)` để di chuyển và hiển thị mã cổ phiếu cụ thể trên màn hình Stock Detail.
- **Topbar** hỗ trợ nút tìm kiếm nhanh để mở màn hình **Chat** và nút Đăng xuất để quay lại màn hình **Login**.

### 10.3 CSS Class Conventions
- `.app-shell`: Vùng chứa chính của ứng dụng (Flex layout).
- `.app-main`: Vùng nội dung chính hỗ trợ cuộn trang.
- `body.qf-dark`: Kích hoạt các biến giao diện Dark mode.
- `body.qf-no-conf`: Ẩn toàn bộ các chỉ báo độ tin cậy AI `.confidence-indicator`.

### 10.4 Giới hạn đã biết của bản Prototype
1. **Dữ liệu giả lập:** Giá cổ phiếu và tin tức hoàn toàn tĩnh và đổi theo kịch bản.
2. **Không lưu trữ dài hạn:** Cảnh báo tự tạo và tùy chọn của người dùng chỉ tồn tại trên session/localStorage.
3. **AI Chat & Jobs chưa hoạt động thực:** Giao diện chat và danh sách công việc chạy nền chỉ hiển thị phản hồi mẫu, chưa kết nối LLM hoặc chạy tác vụ thật.

---
*Tài liệu này là đặc tả yêu cầu sản phẩm chuẩn của QuantyFin. Được cập nhật và đồng bộ vào ngày 06/06/2026 bởi AI Agent.*
