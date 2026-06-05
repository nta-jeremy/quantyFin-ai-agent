---
name: quantyFin-ai
description: Hệ thống nhận diện hình ảnh và token thiết kế cho Admin Dashboard quantyFin-ai, kế thừa hệ thống thiết kế của Binance.
status: final
colors:
  primary: "#FCD535" # Binance Yellow
  primary-active: "#F0B90B"
  primary-disabled: "#3A3A1F"
  canvas-dark: "#0B0E11" # Near-black
  surface-card-dark: "#1E2329" # Card background
  surface-elevated-dark: "#2B3139" # Hover / elevated card
  hairline-on-dark: "#2B3139" # Border
  ink: "#181A20"
  body: "#EAECEF" # Text color on dark
  muted: "#707A8A" # Muted text
  trading-up: "#0ECB81" # Green (Crawl active, Up, Positive)
  trading-down: "#F6465D" # Red (Crawl error/stopped, Down, Negative)
  info: "#3B82F6"
typography:
  display-lg:
    fontFamily: "Inter, sans-serif"
    fontSize: 48px
    fontWeight: 700
    lineHeight: 1.1
    letterSpacing: -0.5px
  display-sm:
    fontFamily: "Inter, sans-serif"
    fontSize: 32px
    fontWeight: 600
    lineHeight: 1.2
  title-md:
    fontFamily: "Inter, sans-serif"
    fontSize: 20px
    fontWeight: 600
    lineHeight: 1.35
  title-sm:
    fontFamily: "Inter, sans-serif"
    fontSize: 16px
    fontWeight: 600
    lineHeight: 1.4
  body-md:
    fontFamily: "Inter, sans-serif"
    fontSize: 14px
    fontWeight: 400
    lineHeight: 1.5
  body-sm:
    fontFamily: "Inter, sans-serif"
    fontSize: 13px
    fontWeight: 400
    lineHeight: 1.5
  number-md:
    fontFamily: "JetBrains Mono, IBM Plex Mono, monospace"
    fontSize: 14px
    fontWeight: 500
    lineHeight: 1.4
rounded:
  sm: 4px
  md: 6px
  lg: 8px
  xl: 12px
  pill: 9999px
spacing:
  xs: 8px
  sm: 12px
  md: 16px
  lg: 24px
  xl: 32px
  section: 80px
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.ink}"
    rounded: "{rounded.md}"
    padding: "10px 20px"
    height: "38px"
  button-secondary:
    backgroundColor: "{colors.surface-card-dark}"
    textColor: "{colors.body}"
    rounded: "{rounded.md}"
    padding: "10px 20px"
    height: "38px"
  dashboard-card:
    backgroundColor: "{colors.surface-card-dark}"
    textColor: "{colors.body}"
    rounded: "{rounded.xl}"
    padding: "{spacing.lg}"
    border: "1px solid {colors.hairline-on-dark}"
  input-field:
    backgroundColor: "{colors.canvas-dark}"
    textColor: "{colors.body}"
    rounded: "{rounded.md}"
    border: "1px solid {colors.hairline-on-dark}"
    padding: "8px 12px"
---

# Quy chuẩn Thiết kế Visual (DESIGN.md) - quantyFin-ai

Tài liệu này xác định ngôn ngữ thiết kế và hệ thống Token cho giao diện Admin Dashboard của hệ thống **quantyFin-ai**, dựa trên cấu trúc thẩm mỹ tối giản (Minimalism) và kế thừa trực tiếp phong cách mạnh mẽ, tin cậy của **Binance Design System**.

> [!NOTE]
> Tham chiếu bố cục trực quan: [key-dashboard.html](file:///Users/tunganh252/Desktop/Projects/Finance/quantyFin-ai-agent/_bmad-output/planning-artifacts/ux-designs/ux-quantyFin-ai-2026-06-05/mockups/key-dashboard.html). Các quy chuẩn dạng văn bản trong spine này luôn là hợp đồng pháp lý tối cao nếu xảy ra bất kỳ xung đột thiết kế nào với các mockup hoặc hình ảnh minh họa.

## 1. Brand & Style (Phong cách Thương hiệu)

Giao diện Admin Dashboard của **quantyFin-ai** phục vụ trực tiếp nhà quản trị (Jeremy Nguyen) trong việc giám sát hệ thống crawler, luồng dữ liệu, trực quan hóa đồ thị tri thức (Knowledge Graph), và tiến trình phân tích của các AI Agent. 

*   **Tinh thần cốt lõi:** Tối giản (Minimalism), tin cậy, chú trọng dữ liệu lớn và thời gian thực.
*   **Trải nghiệm nền tảng:** Mặc định sử dụng **Dark Mode** trên nền tối sâu (`{colors.canvas-dark}`), tạo cảm giác tập trung như một buồng lái điều khiển (cockpit). Điểm nhấn chính là sắc vàng thương hiệu (`{colors.primary}`) dùng cho trạng thái kích hoạt, hành động chính, và các chỉ số tài chính quan trọng.
*   **Kế thừa từ Binance:** Sử dụng các đường hairline phân cách sắc nét, thiết kế dạng phẳng (Flat color blocks) không lạm dụng hiệu ứng đổ bóng hay mờ kính (glassmorphism), và tách biệt rõ ràng các khối thông tin bằng sự tương phản màu nền.

## 2. Colors (Màu sắc)

Bảng màu được chia làm các nhóm chức năng rõ rệt, kế thừa từ Binance:

### Màu thương hiệu & Điểm nhấn (Brand & Accent)
*   **Binance Yellow (`{colors.primary}` - `#FCD535`):** Màu chủ đạo thu hút sự chú ý. Được sử dụng cho các nút kêu gọi hành động (CTA) chính, các chỉ số nổi bật đặc biệt (ví dụ: Tổng số thực thể trong Graph), hoặc trạng thái đang hoạt động cốt lõi.
*   **Yellow Active (`{colors.primary-active}` - `#F0B90B`):** Trạng thái Hover hoặc Click của các phần tử màu vàng.

### Màu nền & Bề mặt (Canvas & Surface)
*   **Canvas Dark (`{colors.canvas-dark}` - `#0B0E11`):** Nền tảng không gian tối sâu, không phải màu đen tuyền để giảm mỏi mắt.
*   **Surface Card (`{colors.surface-card-dark}` - `#1E2329`):** Bề mặt của các thẻ widget dữ liệu, danh sách crawler, và bảng biểu phân tích.
*   **Surface Elevated (`{colors.surface-elevated-dark}` - `#2B3139`):** Nền cho các phần tử con nổi bật bên trong thẻ hoặc thanh điều hướng phụ.

### Đường viền & Phân tách (Borders & Hairlines)
*   **Hairline Dark (`{colors.hairline-on-dark}` - `#2B3139`):** Đường viền 1px phân tách các cột bảng biểu hoặc bo viền nhẹ xung quanh card. Tạo ranh giới tinh tế thay vì dùng bóng đổ.

### Trạng thái Kỹ thuật & Tín hiệu (Trading Semantics)
*   **Trading Up / Active (`{colors.trading-up}` - `#0ECB81`):** Sắc xanh lá đại diện cho các tiến trình chạy thành công (Active), Crawler đang thu thập tin tức ổn định, hoặc chỉ báo tâm lý thị trường tích cực.
*   **Trading Down / Error (`{colors.trading-down}` - `#F6465D`):** Sắc đỏ đại diện cho lỗi hệ thống (Crawl Error), luồng dữ liệu bị tắc nghẽn, hoặc trạng thái dừng hoạt động (Stopped).

## 3. Typography (Kiểu chữ)

Hệ thống sử dụng **Inter** cho phần chữ hiển thị (tiêu đề, nhãn, mô tả) nhằm đảm bảo sự hiện đại và rõ nét trên màn hình tối, kết hợp với các phông chữ monospace như **JetBrains Mono** hoặc **IBM Plex Mono** cho phần số liệu tài chính để giữ độ căn thẳng hàng (tabular figures).

*   **Văn bản mô tả & Điều khiển:** Sử dụng `{typography.body-md}` (14px) và `{typography.body-sm}` (13px).
*   **Tiêu đề khối dữ liệu:** Sử dụng `{typography.title-sm}` (16px) hoặc `{typography.title-md}` (20px).
*   **Dữ liệu số (Mã cổ phiếu, chỉ số tài chính, số lượng tin cào):** Luôn dùng `{typography.number-md}` (JetBrains Mono) để tăng tính chuyên nghiệp như một sàn giao dịch thực thụ.

## 4. Layout & Spacing (Bố cục & Khoảng cách)

*   **Hệ cơ sở:** Chia hết cho 4px.
*   **Khoảng cách tiêu chuẩn:**
    *   Khoảng cách giữa các Widget lớn: `{spacing.lg}` (24px).
    *   Padding bên trong các Card Widget: `{spacing.lg}` (24px) hoặc `{spacing.md}` (16px) cho các bảng nhỏ hơn.
*   **Bố cục Trang:** Thiết kế dạng **Grid 12 cột** linh hoạt. Bố cục tối ưu cho Admin Dashboard bao gồm một Side Nav (hoặc Top Nav tối giản cao 56px) và khu vực nội dung chính được chia thành các hàng Widget chức năng.

## 5. Elevation & Depth (Độ nổi & Chiều sâu)

*   **Nguyên tắc Phẳng hóa:** Không sử dụng đổ bóng lớn (large blur shadows). Chiều sâu được tạo ra bằng các lớp màu nền: Nền chính (`#0B0E11`) -> Thẻ Widget (`#1E2329`) -> Các trường nhập liệu/nút phụ (`#0B0E11` hoặc `#2B3139`).
*   **Đường hairline:** Sử dụng đường viền `1px solid {colors.hairline-on-dark}` để làm rõ ranh giới giữa các khối giao diện.

## 6. Shapes (Hình dáng & Bo góc)

*   Bo góc vừa phải để giữ nét góc cạnh, chuyên nghiệp như một nền tảng tài chính thực thụ:
    *   Nút & Input: `{rounded.md}` (6px).
    *   Thẻ thông tin lớn (Widgets): `{rounded.xl}` (12px) hoặc `{rounded.lg}` (8px).
    *   Hạt trạng thái (Badge): `{rounded.pill}` (9999px) hoặc bo góc nhỏ `{rounded.sm}` (4px).

## 7. Components (Thành phần Giao diện)

*   **Nút chính (`button-primary`):** Nền vàng Binance, chữ đen Ink để đạt độ tương phản cao nhất. Dùng cho các tác vụ kích hoạt quan trọng (ví dụ: "Run Crawl Now").
*   **Nút phụ (`button-secondary`):** Nền Surface Card, chữ trắng bạc Body. Dùng cho các tác vụ phụ hoặc nút hủy.
*   **Thẻ Widget (`dashboard-card`):** Khung chứa thông tin tổng thể với nền tối `#1E2329`, bo góc 12px, có viền hairline mỏng.
*   **Hạt trạng thái (Status Badge):**
    *   *Active:* Nền màu xanh lá mờ (hoặc chỉ dùng chữ màu xanh lá `{colors.trading-up}`).
    *   *Error:* Chữ hoặc viền màu đỏ `{colors.trading-down}` kèm mã lỗi chi tiết hiển thị dạng monospace.

## 8. Do's and Don'ts (Nên làm và Tránh làm)

| Nên làm (Do) | Tránh làm (Don't) |
| :--- | :--- |
| Sử dụng màu vàng thương hiệu `{colors.primary}` rất chắt lọc cho chỉ báo trọng tâm và nút hành động chính. | Sử dụng màu vàng làm màu nền hoặc viết chữ màu vàng trên nền sáng gây mất độ tương phản. |
| Sử dụng font monospace `{typography.number-md}` cho toàn bộ số liệu, mã cổ phiếu (Ticker) và mã định danh. | Sử dụng font sans-serif thông thường cho các bảng số liệu tài chính khiến các cột bị lệch hàng. |
| Phân biệt trạng thái hệ thống bằng cặp màu Trading Up (Xanh lá) và Trading Down (Đỏ). | Sử dụng màu xanh/đỏ này cho các mục đích trang trí thuần túy hoặc không mang ý nghĩa trạng thái. |
| Giữ thiết kế phẳng và sắc nét bằng các đường hairline 1px `#2B3139`. | Thêm các hiệu ứng đổ bóng mờ ảo, gradient nền rực rỡ hay hiệu ứng glassmorphism bóng bảy. |
