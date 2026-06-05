---
stepsCompleted: [1, 2]
inputDocuments: []
session_topic: 'Lập kế hoạch hành động chi tiết cho dự án AI Agentic phân tích chứng khoán Việt Nam (MVP: Knowledge Graph + MCP Server)'
session_goals: 'Tạo roadmap các công việc cần làm, xác định giải pháp kỹ thuật, ưu tiên phát triển MVP'
selected_approach: 'ai-recommended'
techniques_used: ['First Principles Thinking', 'Morphological Analysis', 'Constraint Mapping']
ideas_generated: []
context_file: ''
---

# Brainstorming Session Results

**Facilitator:** Jeremy Nguyen
**Date:** 2026-06-03

## Session Overview

**Topic:** Lập kế hoạch hành động chi tiết cho dự án AI Agentic phân tích chứng khoán Việt Nam (MVP: Knowledge Graph + MCP Server)
**Goals:** Tạo roadmap các công việc cần làm, xác định giải pháp kỹ thuật, ưu tiên phát triển MVP

### Context Guidance

_[Không có file context]_

### Session Setup

Phiên làm việc được thiết lập để tập trung vào việc định hướng chiến lược và lập kế hoạch thực thi kỹ thuật cho dự án AI phân tích chứng khoán. Trọng tâm là làm rõ luồng dữ liệu (Data Pipeline), xây dựng Knowledge Graph và tạo MCP Server.

## Technique Selection

**Approach:** AI-Recommended Techniques
**Analysis Context:** Lập kế hoạch hành động chi tiết cho dự án AI Agentic phân tích chứng khoán Việt Nam (MVP: Knowledge Graph + MCP Server) với trọng tâm là Tạo roadmap các công việc cần làm, xác định giải pháp kỹ thuật, ưu tiên phát triển MVP.

**Recommended Techniques:**
- **First Principles Thinking:** Đặt nền móng bằng cách tìm ra các cấu phần "Must-have" tuyệt đối cho MVP (KG & MCP Server).
- **Morphological Analysis:** Phát triển giải pháp bằng cách lập ma trận các biến số kỹ thuật để tìm ra tech-stack tối ưu.
- **Constraint Mapping:** Tinh chỉnh hành động bằng cách xác định các rào cản thực tế và tìm giải pháp vượt qua, chốt To-do list.

**AI Rationale:** Cách tiếp cận này được thiết kế để xử lý một hệ thống kỹ thuật phức tạp bằng cách bóc tách từ cốt lõi, khám phá các tổ hợp giải pháp, và cuối cùng là vạch ra con đường khả thi nhất để tránh rủi ro.

## Technique Execution Results

- **First Principles Thinking:**
  - **Interactive Focus:** Đi tìm "sự thật cốt lõi" và dữ liệu sống còn (Minimum Viable Data) cho MVP.
  - **Key Breakthroughs:** 
    - **[Dữ liệu] Dữ liệu định lượng (Giá, Khối lượng, Cơ bản):** Nền tảng "mỏ neo" sự thật, nên lưu ở Database truyền thống.
    - **[Kiến trúc Dữ liệu] Mạng lưới Vĩ mô - Vi mô (Macro-to-Micro Linkage):** Biến tin tức định tính thành mối quan hệ nhân quả nối tới cổ phiếu. Dùng LLM (như Claude 3.5 Haiku) tự động bóc tách tin tức thành JSON để lưu vào KG.
  - **User Creative Strengths:** Tư duy sắc sảo, thực tế (focus thẳng vào thanh khoản/chỉ số) và khả năng hình dung tốt về kiến trúc liên kết dữ liệu vĩ mô.
  - **Energy Level:** Tập trung, đi thẳng vào vấn đề cốt lõi.

**Morphological Analysis:**
- **Interactive Focus:** Thiết lập ma trận giải pháp công nghệ & chiến lược thu thập dữ liệu (Crawling Strategy).
- **Key Breakthroughs:**
  - **Tech Stack cốt lõi:** Chọn Python (Option B) làm ngôn ngữ lập trình chính cho MCP Server (`mcp-python-sdk`), xử lý dữ liệu (`pandas`), và LLM orchestration (`langchain` / `llamaindex`).
  - **Chiến lược Thu thập Phân tầng (Multi-tiered Crawling):**
    - *Tầng 1 (Nhanh & Tối ưu):* Web Search API (như Tavily/SerpAPI) hoặc RSS/Free APIs.
    - *Tầng 2 (Dự phòng/Fallback):* Tự động trigger mở trình duyệt thực tế (Playwright Python / Chrome Automation) để vượt rào cản (anti-bot, Javascript rendering) và đọc/crawl trực tiếp thông tin.
- **Đề xuất danh sách nguồn dữ liệu (Data Sources):**
  - *RSS/Free APIs (10 nguồn):*
    1. Cafef RSS (Kinh doanh, Thị trường...)
    2. Vietstock RSS (Doanh nghiệp, Vĩ mô...)
    3. Tin nhanh VnExpress RSS (Kinh tế, Tài chính...)
    4. Báo Đầu tư (Baodautu.vn) RSS
    5. Tin nhanh Chứng khoán (Tinnhanhchungkhoan.vn) RSS
    6. Báo Tuổi Trẻ (Tài chính - Kinh doanh) RSS
    7. VietNamNet (Kinh doanh) RSS
    8. SSI / HSC Web APIs (API public bảng giá hoặc thông tin phân tích nếu có)
    9. TradingEconomics API (Dữ liệu vĩ mô Việt Nam miễn phí có giới hạn)
    10. Alpha Vantage hoặc Yahoo Finance (Dữ liệu giá lịch sử của VN-Index và cổ phiếu VN dưới dạng ticker dạng `.HN` / `.HM`)
  - *Nguồn báo chí/tin tức uy tín để Crawl/Search (20-30 nguồn):*
    - *Tài chính chuyên sâu:* CafeF, Vietstock, Tinnhanhchungkhoan (ĐTCK), Nhịp cầu Đầu tư, Báo Đầu tư, Vietnam Business Forum, Vietnambiz.
    - *Vĩ mô & Thời sự:* VnExpress (Kinh tế), Tuổi Trẻ (Kinh doanh), Thanh Niên (Kinh tế), VietNamNet (Kinh doanh), Sài Gòn Giải Phóng (Tài chính - Kinh tế), Thời báo Tài chính Việt Nam, Báo Diễn đàn Doanh nghiệp (VCCI), Tạp chí Thị trường Tài chính Tiền tệ.
    - *Cơ quan quản lý & Hiệp hội:* Cổng thông tin Chính phủ, Ủy ban Chứng khoán Nhà nước (SSC), Sở Giao dịch Chứng khoán TP.HCM (HSX), Sở Giao dịch Chứng khoán Hà Nội (HNX), Tổng cục Thống kê (GSO), Ngân hàng Nhà nước Việt Nam (SBV), Bộ Tài chính, Hiệp hội Doanh nghiệp TP.HCM (HUBA).
    - *Báo cáo phân tích CTCK:* SSI Research, HSC Research, VNDIRECT Research, MAS Research, Vietcap Research.

## Technique 3: Constraint Mapping (Lập Bản đồ Rào cản & To-do List)

Bây giờ, chúng ta sẽ chuyển sang kỹ thuật cuối cùng để lập lộ trình thực thi tối ưu dựa trên các rào cản và tài nguyên hiện có.

### Xác định rào cản (Constraints)
1. **Rào cản về Anti-bot & IP block:** Nhiều trang báo tài chính Việt Nam (như CafeF) chặn request từ các IP đám mây hoặc bot thông thường.
2. **Rào cản về cấu trúc dữ liệu Knowledge Graph:** Khó khăn trong việc định nghĩa thể loại Node/Edge tối ưu để LLM không bị rối thông tin.
3. **Rào cản về độ trễ (Latency):** Việc dùng browser automation (Playwright) tốn thời gian và tài nguyên hơn nhiều so với API.
4. **Rào cản về độ tin cậy của thông tin:** Tin tức giả mạo hoặc tin đồn làm lệch phân tích của AI.

### Đề xuất Roadmap thực thi (To-do List cho MVP)

#### Phase 1: Nền tảng Dữ liệu & Pipeline Thu thập (Tuần 1)
- [ ] Khởi tạo dự án Python, cấu hình môi trường ảo, cài đặt các thư viện `mcp`, `playwright`, `pandas`, `networkx` (hoặc Neo4j driver).
- [ ] Phát triển module Crawl đa tầng:
  - Tầng RSS: Đọc tự động các nguồn RSS tin tức.
  - Tầng Search: Sử dụng công cụ web search (Tavily/DuckDuckGo) để lấy tin tức nhanh.
  - Tầng Playwright: Script tự động điều khiển trình duyệt thật để đọc bài viết chi tiết từ link thu thập được.
- [ ] Thiết lập SQLite hoặc PostgreSQL để lưu trữ dữ liệu định lượng và thông tin thô từ crawler.

#### Phase 2: Trích xuất tri thức & Xây dựng Knowledge Graph (Tuần 2)
- [ ] Thiết kế Schema cho Knowledge Graph (Các Node: `Stock`, `Sector`, `MacroEvent`, `Leader`, `News`; Các Edge: `IMPACTS`, `BELONGS_TO`, `MANAGES`, `RELATED_TO`).
- [ ] Phát triển LLM Extractor: Viết prompt/schema để LLM đọc bài viết thô và trả về JSON chứa các liên kết vĩ mô - vi mô (VD: Event X tác động tích cực đến Ngành Y, các cổ phiếu liên quan là Z).
- [ ] Tích hợp cơ sở dữ liệu đồ thị (dùng thư viện Python `networkx` cho file-based đồ thị gọn nhẹ hoặc `Neo4j` nếu cần chuyên nghiệp).

#### Phase 3: Xây dựng MCP Server & Tích hợp (Tuần 3)
- [ ] Phát triển MCP Server bằng Python hỗ trợ các tools:
  - `query_stock_graph(ticker)`: Truy vấn các node vĩ mô/vi mô liên kết với cổ phiếu.
  - `add_macro_news(title, content, url)`: Thêm bài báo mới vào hệ thống tự động chạy extractor và cập nhật Graph.
  - `get_market_snapshot()`: Trả về trạng thái giá/khối lượng/thanh khoản hiện tại kết hợp tin tức nổi bật.
- [ ] Tích hợp thử nghiệm MCP Server với Claude Desktop hoặc ứng dụng AI Agent cơ bản.

#### Phase 4: Xây dựng Frontend AI-Native (Tuần 4)
- [ ] Khởi tạo dự án Next.js (React) + Tailwind v4 theo cấu trúc shadcn-compatible registry được mô tả trong DESIGN.md.
- [ ] Import và cấu hình `colors_and_type.css` cùng các Surface adapters (đặc biệt là bề mặt `app` và `portal`).
- [ ] Cài đặt các UI Kits lõi: `quantyFin-app` (cho bố cục Dashboard) và `quantyFin-ai` (cho Q&A Bot, diff, confidence score).
- [ ] Kết nối Frontend với MCP Server để render Knowledge Graph và luồng dữ liệu thị trường bằng giao diện chuẩn chỉnh, chuyên nghiệp.

---
**Cập nhật trạng thái:** Hoàn thành cập nhật phiên Brainstorming tích hợp UI/UX mới từ QuantyFin Design System. Sẵn sàng tạo các file spec và tài liệu thực thi tiếp theo.
