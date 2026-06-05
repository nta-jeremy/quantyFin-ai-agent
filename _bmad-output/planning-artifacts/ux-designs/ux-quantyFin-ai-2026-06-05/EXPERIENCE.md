---
name: quantyFin-ai
status: final
sources:
  - file:///Users/tunganh252/Desktop/Projects/Finance/quantyFin-ai-agent/_bmad-output/planning-artifacts/prds/prd-quantyFin-ai-2026-06-03/prd.md
updated: 2026-06-05
---

# Quy chuẩn Trải nghiệm Người dùng (EXPERIENCE.md) - quantyFin-ai

Tài liệu này định nghĩa cấu trúc thông tin, hành vi tương tác, các trạng thái hệ thống và luồng công việc của Admin Dashboard **quantyFin-ai**. Tài liệu này đồng bộ chặt chẽ với hệ thống token được định nghĩa trong `DESIGN.md`.

> [!NOTE]
> Tham chiếu bố cục trực quan: [key-dashboard.html](file:///Users/tunganh252/Desktop/Projects/Finance/quantyFin-ai-agent/_bmad-output/planning-artifacts/ux-designs/ux-quantyFin-ai-2026-06-05/mockups/key-dashboard.html). Các quy chuẩn dạng văn bản trong spine này luôn là hợp đồng pháp lý tối cao nếu xảy ra bất kỳ xung đột thiết kế nào với các mockup hoặc hình ảnh minh họa.

## 1. Foundation (Nền tảng Trải nghiệm)

*   **Loại ứng dụng:** Web Admin Dashboard (Single-page App dành cho màn hình lớn Desktop/Laptop).
*   **Mục tiêu:** Cung cấp cho quản trị viên (Jeremy Nguyen) cái nhìn toàn cảnh về hệ thống tự động hóa thu thập tin tức, tiến trình xử lý của các AI Agent và cấu trúc Sơ đồ tri thức (Knowledge Graph) chứng khoán Việt Nam.
*   **Thẩm mỹ tương tác:** Tối giản (Minimalism), ưu tiên mật độ thông tin cao để dễ dàng giám sát mà không phải cuộn trang nhiều lần. Sử dụng các đường hairline viền sắc nét của Binance làm ranh giới giữa các khối dữ liệu.

## 2. Information Architecture (Kiến trúc Thông tin)

Dashboard chính được tổ chức theo cấu trúc lưới (Grid layout) chia làm **4 phân khu chức năng chính** nằm trên một màn hình duy nhất để đảm bảo tính trực quan:

```
+--------------------------------------------------------------------------+
|  Top Navigation Bar (Logo, System Status, Global Active Agents Counter)  |
+--------------------------------------------------------------------------+
|  SECTION 1: Crawler Management       | SECTION 2: Multi-Agent Pipeline   |
|  - Danh sách nguồn tin (CafeF, NDH...) |  - Live activity log của các Agent|
|  - Status, Last Run, Action Trigger  |  - Hàng đợi xử lý (NLP Queue)      |
+--------------------------------------+-----------------------------------+
|  SECTION 3: Knowledge Graph Visualizer| SECTION 4: Q&A Assistant Console  |
|  - Đồ thị nút liên kết (Ticker/Event) |  - Khung chat truy vấn nhanh      |
|  - Bảng lọc thực thể tài chính       |  - Chi tiết nguồn tin trích dẫn   |
+--------------------------------------------------------------------------+
```

### Chi tiết các phân khu:

1.  **Crawler Management:**
    *   Hiển thị danh sách các nguồn cào tin (7 nguồn xác định trong PRD: CafeF, NDH, VnEconomy, Vietstock, Tuổi Trẻ, Thanh Niên, VnBusiness).
    *   Mỗi nguồn tin hiển thị: Tên nguồn, Tần suất lập lịch, Thời điểm chạy gần nhất, Số lượng tin tức thu thập được hôm nay, Trạng thái (Running/Idle/Failed), và nút "Run Now" (thao tác cào thủ công).
2.  **Multi-Agent Pipeline Trace:**
    *   Trực quan hóa luồng xử lý tin tức qua các AI Agent:
        *   *Ingestion Agent* -> *Sentiment Agent* (Chấm điểm cảm xúc) -> *Entity Extraction Agent* (Bóc tách thực thể: Ticker, Lãnh đạo, Ngành) -> *Relationship Mapping Agent* (Thiết lập quan hệ) -> *Neo4j/Vector DB Writer*.
    *   Hiển thị biểu đồ tiến trình dạng ngang (horizontal node steps) với các node sáng đèn xanh `{colors.trading-up}` khi Agent đang xử lý tài liệu.
    *   Bảng console log dạng text nhỏ hiển thị các tác vụ Agent đang làm theo thời gian thực (ví dụ: `[SentimentAgent] Scoring sentiment for VCB: +0.7`).
3.  **Knowledge Graph Visualizer (Trung tâm giao diện):**
    *   Một khung canvas lớn trực quan hóa sơ đồ mạng lưới tri thức (Nodes & Edges).
    *   Hỗ trợ zoom/pan, click vào node (ví dụ: mã cổ phiếu `HPG` hoặc sự kiện vĩ mô `Tăng thuế thép`) để mở bảng chi tiết các liên kết liên quan ở sidebar bên phải của card.
4.  **Q&A Assistant & Market Chart (Side Console):**
    *   Hộp thoại chatbot trực tuyến kết nối với Q&A Bot để truy vấn nhanh dữ liệu bằng tiếng Việt (giống như hoạt động của Telegram Bot).
    *   Biểu đồ kỹ thuật tối giản (Line chart) của mã cổ phiếu đang được chọn ở Graph Visualizer, kèm các điểm đánh dấu sự kiện tin tức/sentiment trên biểu đồ.

## 3. Voice and Tone (Ngôn ngữ & Giọng điệu)

Vì đây là dashboard quản trị kỹ thuật cá nhân, giọng điệu hướng tới sự ngắn gọn, rõ ràng, kỹ thuật và không mang tính trang trí:

| Nên viết (Do) | Tránh viết (Don't) |
| :--- | :--- |
| `[Active] CafeF crawler finished (24 items)` | `Wow! CafeF crawler đã hoàn thành cào tin siêu nhanh rồi nè! 🚀` |
| `[Error] Sentiment Agent API rate limit exceeded. Retrying...` | `Có lỗi xảy ra rồi, không thể kết nối API lúc này.` |
| `Sentiment: +0.85 (Strong Positive)` | `Tâm lý thị trường siêu tốt cho mã này.` |
| `Neo4j Write: Success (12 nodes, 15 relationships)` | `Đã lưu thành công dữ liệu vào database.` |

## 4. Component Patterns (Hành vi của các Thành phần)

*   **Crawler Row Widget:**
    *   Mỗi nguồn cào tin hiển thị dưới dạng một hàng trong bảng.
    *   Nút bấm "Run Now" dạng `{components.button-primary}` thu nhỏ. Khi được nhấn, nút chuyển sang trạng thái loading (icon xoay) và hàng đó nhấp nháy viền xanh nhẹ.
    *   Nếu cào lỗi, cột Status hiển thị chữ đỏ `Failed` thuộc tông màu `{colors.trading-down}` kèm biểu tượng cảnh báo nhỏ. Di chuột vào chữ sẽ hiện tooltip giải thích lỗi kỹ thuật (ví dụ: `Timeout 5000ms`).
*   **Interactive Node Graph:**
    *   Node chính (Mã cổ phiếu) có kích thước lớn hơn, nền vàng viền đen. Node phụ (Sự kiện vĩ mô, Lãnh đạo) có nền xám đen `#1E2329` và viền hairline trắng bạc `#2B3139`.
    *   Nhấp đúp chuột (Double click) vào một node bất kỳ sẽ mở rộng các mối liên kết trực tiếp của node đó trong Graph.
    *   Ranh giới liên kết (Edge) được vẽ bằng mũi tên mảnh màu xám. Mũi tên có màu xanh `{colors.trading-up}` nếu mối quan hệ mang tính tác động tích cực, hoặc màu đỏ `{colors.trading-down}` nếu tác động tiêu cực (ví dụ: `Tăng thuế xuất khẩu -> [TÁC_ĐỘNG_TIÊU_CỰC] -> HPG`).
*   **Q&A Chat Console:**
    *   Hộp thoại chat cuộn tự động xuống dưới khi có tin mới.
    *   Khung nhập câu hỏi dạng `{components.input-field}`.
    *   Khi AI trả lời, các nguồn tin dẫn chứng sẽ hiển thị dưới dạng các thẻ nhỏ (Metadata Chips) ở dưới cùng của bong bóng chat. Nhấp vào chip sẽ mở popover hiển thị nội dung tin tức gốc được cào.

## 5. State Patterns (Các trạng thái Hệ thống)

*   **Trạng thái cào tin đang hoạt động (Crawling In Progress):**
    *   Đèn tròn nhỏ bên cạnh nguồn cào nhấp nháy xanh lá cây (`{colors.trading-up}`).
    *   Hiển thị thanh tiến trình (Progress Bar) chạy ngang dạng phẳng (flat) màu vàng.
*   **Trạng thái rỗng (Empty States) trên Graph Visualizer:**
    *   Khi chưa chọn mã cổ phiếu hoặc chưa truy vấn thực thể: Hiển thị dòng chữ `{typography.body-md}` màu `{colors.muted}` căn giữa: *"Hãy chọn một mã cổ phiếu hoặc nhập truy vấn ở thanh tìm kiếm để trực quan hóa sơ đồ tri thức."*
*   **Trạng thái Agent xử lý nghẽn hàng (Pipeline Congestion):**
    *   Nếu số lượng tài liệu tin tức trong hàng đợi lớn hơn 50 tin, hiển thị một thông báo cảnh báo màu vàng ở góc điều hướng: `[Warning] Multi-Agent queue is high (72 items remaining)`.
*   **Lỗi kết nối Graph Database:**
    *   Toàn bộ phân khu Graph Visualizer hiển thị phủ xám mờ với thông báo đỏ ở giữa: `[Error] Database connection lost. Reconnecting...` kèm nút `Retry` màu đỏ.

## 6. Interaction Primitives (Các tương tác cơ bản)

*   Giao diện được thiết kế để thao tác thuận tiện bằng chuột trên Desktop (drag node, zoom graph).
*   **Lối tắt bàn phím (Keyboard Shortcuts):**
    *   `⌘K` hoặc `Ctrl+K`: Tiêu điểm (Focus) vào thanh tìm kiếm mã cổ phiếu toàn cục.
    *   `⌘/`: Focus trực tiếp con trỏ vào ô nhập câu hỏi Chatbot ở góc phải.
    *   `Esc`: Đóng toàn bộ các popover thông tin chi tiết node đang mở.
    *   `⌘R` (Custom): Kích hoạt chạy nhanh toàn bộ các Crawler đang rảnh rỗi.

## 7. Accessibility Floor (Tiêu chuẩn tiếp cận tối thiểu)

Giao diện admin được thiết kế cho chính nhà đầu tư quản trị (Jeremy Nguyen) nên cần đảm bảo hiển thị rõ nét trên màn hình máy tính cá nhân:
*   Độ tương phản của chữ trắng bạc (`#EAECEF`) trên nền tối card (`#1E2329`) đạt chuẩn WCAG AA (> 4.5:1).
*   Màu chữ đen trên nút vàng primary (`#FCD535`) đạt độ tương phản cực kỳ cao (> 7:1) giúp dễ đọc nhanh dưới mọi điều kiện ánh sáng.
*   Các vùng focus đầu vào luôn được bo viền xanh dương `#3B82F6` dày 2px khi người dùng di chuyển bằng phím `Tab`.

## 8. Key Flows (Luồng tương tác chính)

### Luồng 1: Giám sát cào tin tức hàng ngày và xử lý của Multi-Agent
1.  Jeremy truy cập vào Admin Dashboard sau phiên giao dịch lúc 15:30.
2.  Dashboard hiển thị tiến trình tự động: Crawler bắt đầu kích hoạt cào tin trên 7 nguồn.
3.  Jeremy thấy nguồn *VnEconomy* sáng đèn xanh nhấp nháy, hiển thị: `Crawling VnEconomy... (12 articles found)`.
4.  Ngay bên cạnh, tại khu vực **Multi-Agent Pipeline Trace**, các AI Agent chuyển trạng thái hoạt động:
    *   `IngestionAgent` phân tích cấu trúc bài viết.
    *   `SentimentAgent` chấm điểm cảm xúc (hiển thị trạng thái đang xử lý tin số 4/12).
    *   `EntityExtractionAgent` trích xuất thực thể mã `HPG` và sự kiện `áp thuế tự vệ`.
5.  **Kết quả cốt lõi (Climax):** Danh sách console log tự động đẩy dòng log mới: `[GraphAgent] Created relationship HPG -> [CÓ_SỰ_KIỆN] -> áp thuế tự vệ`. Cùng lúc đó, số lượng Thực thể tổng thể trên Top Navigation cập nhật tăng lên từ `14,205` lên `14,209`. Jeremy thấy toàn bộ dòng chảy dữ liệu được trơn tru mà không cần mở Terminal.

### Luồng 2: Truy vấn quan hệ chuỗi rủi ro của một cổ phiếu qua Đồ thị
1.  Jeremy nhận được tin nhắn Telegram cảnh báo mã cổ phiếu `VND` bị phân tích sentiment tiêu cực nghiêm trọng.
2.  Anh mở Dashboard, nhấn `⌘K` và nhập `VND` rồi nhấn Enter.
3.  **Knowledge Graph Visualizer** lập tức căn giữa và hiển thị Node `VND` ở trung tâm với kích thước lớn.
4.  Jeremy nhấp đúp (Double-click) vào Node `VND`. Sơ đồ bung ra các liên kết trực tiếp.
5.  Anh di chuột vào edge nối giữa `VND` và Node sự kiện `Vụ án VNDIRECT bị hack hệ thống`. Edge này có màu đỏ `{colors.trading-down}`.
6.  **Kết quả cốt lõi (Climax):** Khung thông tin chi tiết hiện ra tóm tắt của tin tức cào được, đi kèm danh sách các đối tác/cổ phiếu khác có liên kết gián tiếp với VND bị ảnh hưởng (như các công ty con hoặc quỹ đầu tư đang nắm giữ tỷ trọng lớn). Jeremy nhanh chóng đánh giá được mức độ lây lan rủi ro để đưa ra hành động quản trị danh mục đầu tư.
