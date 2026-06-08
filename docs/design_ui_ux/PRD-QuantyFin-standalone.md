# PRD — QuantyFin: AI Agentic Platform Phân Tích Chứng Khoán Việt Nam

**Phiên bản:** 1.0  
**Ngày cập nhật:** 06/06/2026  
**Trạng thái:** Draft — chưa qua kiểm duyệt  
**Tác giả:** Jeremy Nguyen (CTO)  

---

## Mục lục

1. [Tổng quan sản phẩm](#1-tổng-quan-sản-phẩm)
2. [Vision & Goals](#2-vision--goals)
3. [User Personas](#3-user-personas)
4. [Kiến trúc kỹ thuật](#4-kiến-trúc-kỹ-thuật)
5. [Màn hình & Tính năng chi tiết](#5-màn-hình--tính-năng-chi-tiết)
6. [Data Model & Market Scenarios](#6-data-model--market-scenarios)
7. [Cấu hình & Settings](#7-cấu-hình--settings)
8. [User Flows chính](#8-user-flows-chính)
9. [Non-functional Requirements](#9-non-functional-requirements)
10. [Roadmap & Phân kỳ](#10-roadmap--phân-kỳ)
11. [Phụ lục kỹ thuật](#11-phụ-lục-kỹ-thuật)

---

## 1. Tổng quan sản phẩm

**Tên sản phẩm:** QuantyFin  
**Slogan:** AI Agentic Platform for Vietnam Capital Markets  
**Loại sản phẩm:** SaaS Web App — Single-Page Application (SPA), standalone deployment  

### 1.1 Mô tả ngắn

QuantyFin là nền tảng phân tích chứng khoán thị trường Việt Nam được tích hợp trí tuệ nhân tạo (AI) theo mô hình agentic. Platform cung cấp cho nhà đầu tư cá nhân và chuyên nghiệp các công cụ phân tích thị trường theo thời gian thực, bao gồm: dashboard tổng quan thị trường, phân tích cổ phiếu đơn lẻ, theo dõi tin tức, hệ thống cảnh báo thông minh, Knowledge Graph về mối quan hệ giữa các thực thể thị trường, và giao diện chat với AI agent.

### 1.2 Brand Identity

| Thuộc tính | Giá trị |
|---|---|
| Primary color | `#2a2b86` (deep navy blue) |
| Accent color | `#fcaf16` (gold/amber) |
| Theme | Light (default) / Dark mode |
| Typography | Sans-serif, hỗ trợ tiếng Việt |

### 1.3 Deployment Model

Platform được đóng gói dưới dạng **self-contained HTML artifact** — toàn bộ app (React, UI components, mock data) được bundle trong một file HTML duy nhất. Không phụ thuộc CDN hay external API trong phiên bản prototype hiện tại.

---

## 2. Vision & Goals

### 2.1 Vision

Trở thành "Bloomberg terminal" dành cho nhà đầu tư Việt Nam — với UX thân thiện, AI-native, và khả năng phân tích thị trường theo ngữ cảnh kinh tế vĩ mô Việt Nam.

### 2.2 Mục tiêu sản phẩm (Product Goals)

1. **Trực quan hóa thị trường theo scenario:** Cho phép nhà đầu tư nhanh chóng chuyển đổi giữa 4 trạng thái thị trường (up/down/volatile/crisis) để xem phân tích phù hợp với từng bối cảnh.
2. **Knowledge Graph as insight engine:** Biểu diễn mối quan hệ phức tạp giữa cổ phiếu, sự kiện, ngành, và tin tức dưới dạng đồ thị có thể tương tác.
3. **AI Chat agent:** Cung cấp giao diện hỏi đáp tự nhiên về phân tích cổ phiếu và thị trường, thay thế việc tìm kiếm thủ công.
4. **Real-time Alerts:** Hệ thống cảnh báo thông minh dựa trên các điều kiện thị trường được cài đặt sẵn hoặc tùy chỉnh.
5. **Configurable AI backbone:** Cho phép cấu hình LLM Gateway, data source, và các tham số AI agent.

### 2.3 Success Metrics (KPIs)

| KPI | Mục tiêu |
|---|---|
| Daily Active Users (DAU) | TBD (prototype phase) |
| Thời gian trung bình trên Dashboard | > 5 phút/session |
| Tỷ lệ chuyển đổi Chat → Stock detail | > 30% |
| Alert engagement rate | > 60% của alerts được click |
| Knowledge Graph session depth | > 3 nodes/session |

---

## 3. User Personas

### 3.1 Nhà đầu tư cá nhân (Retail Investor)

**Mô tả:** Người dùng phổ thông, có kiến thức cơ bản về chứng khoán, muốn theo dõi danh mục và nhận cảnh báo tự động.

**Nhu cầu:**
- Xem nhanh tình hình thị trường tổng thể
- Nhận cảnh báo khi cổ phiếu đạt ngưỡng mục tiêu
- Đọc tin tức và phân tích AI về cổ phiếu đang nắm giữ

**Pain points hiện tại:**
- Phải tra cứu thông tin từ nhiều nguồn khác nhau
- Khó đánh giá mối quan hệ nhân quả giữa tin tức và biến động giá
- Thiếu công cụ phân tích kịch bản (scenario analysis)

### 3.2 Nhà phân tích chứng khoán (Analyst)

**Mô tả:** Chuyên gia tài chính, cần công cụ phân tích chuyên sâu và có thể cấu hình theo workflow riêng.

**Nhu cầu:**
- Phân tích kỹ thuật và cơ bản cho từng cổ phiếu
- So sánh theo sector/ngành
- Knowledge Graph để trace các mối quan hệ ảnh hưởng giữa các công ty
- Tích hợp với LLM có khả năng tuỳ chỉnh (LLM Gateway)

**Pain points hiện tại:**
- Các tool phân tích rời rạc, không được tích hợp
- Thiếu knowledge graph cho thị trường VN
- Không có AI agent hỗ trợ viết báo cáo

### 3.3 Nhà quản lý quỹ (Fund Manager)

**Mô tả:** Người quản lý danh mục lớn, cần monitoring liên tục và phân tích macro.

**Nhu cầu:**
- Theo dõi nhiều cổ phiếu cùng lúc
- Phân tích theo market scenario để hedging
- Background jobs để tự động hóa báo cáo

---

## 4. Kiến trúc kỹ thuật

### 4.1 Frontend Stack

| Thành phần | Công nghệ | Ghi chú |
|---|---|---|
| UI Framework | React 18 | `useState`, `useEffect`, `useMemo` |
| JSX transpilation | Babel (browser-side) | Standalone, không build step |
| State management | React local state | Không Redux/Zustand trong prototype |
| Routing | Custom screen switcher | Không React Router |
| Data viz (KG) | D3.js (force-directed) | Asset riêng (`e1abcd1f`) |
| CSS | Custom CSS + class toggling | `qf-dark`, `qf-no-conf` |
| Persistence | `localStorage` | Auth (`qf_auth`), user preferences |

### 4.2 App Architecture

```
App (root)
├── [Unauthenticated]
│   └── Screens.Login
│
├── [Authenticated]
│   ├── SideRail (left navigation)
│   ├── Topbar (header)
│   └── app-main
│       ├── Screens.Dashboard
│       ├── Screens.KG (Knowledge Graph)
│       ├── Screens.Stock
│       ├── Screens.News
│       ├── Screens.Chat
│       ├── Screens.Alerts
│       ├── Screens.Jobs
│       └── Screens.Settings
│
└── QfTweaks (development overlay - non-production)
```

### 4.3 Global State (App-level)

| State | Type | Default | Mô tả |
|---|---|---|---|
| `authed` | boolean | Đọc từ `localStorage.qf_auth` | Trạng thái đăng nhập |
| `screen` | string | `'dashboard'` | Màn hình đang active |
| `ticker` | string | `'FPT'` | Mã cổ phiếu đang xem |
| `tweaks.theme` | string | `'light'` | Light hoặc dark mode |
| `tweaks.scenario` | string | `'volatile'` | Market scenario hiện tại |
| `tweaks.showConfidence` | boolean | `true` | Hiển thị AI confidence score |

### 4.4 Data Flow

```
window.QF_DATA.build(scenario) → data object
                                  ↓
                    App component (memoized)
                                  ↓
              Props drilling vào các Screens
              (data, onNav, onTicker callbacks)
```

Toàn bộ data trong prototype là **mock data** được sinh từ `window.QF_DATA.build(scenario)` — tái tính toán mỗi khi `scenario` thay đổi (useMemo dependency).

### 4.5 Asset Bundle Structure

| Asset ID | Nội dung | Kích thước |
|---|---|---|
| `24ec1f5a` | App entry point (root component) | ~3.7K chars |
| `b4d9a841` | Screen components (tất cả 9 screens) | ~80K chars |
| `c1106d82` | Settings screen (SET_NAV, form logic) | ~57K chars |
| `5ff38e32` | Mock data (QF_DATA, STOCKS, scenarios) | ~23K chars |
| `c9de8dcd` | Shared UI components, Icons | ~20K chars |
| `e1abcd1f` | Knowledge Graph viewer (KGViewer) | ~10K chars |

**Third-party dependencies (bundled, không phải app code):**
- Babel standalone (~880K)
- ReactDOM (~1.08M)
- React core (~109K)

### 4.6 Authentication

```
localStorage key: 'qf_auth'
  '1' → đã đăng nhập
  '0' → đã đăng xuất
  null → mặc định đăng nhập (first visit)
```

Logic: Lần đầu truy cập (null) → tự động login. Sau đó user tự quản lý trạng thái qua Login/Logout.

### 4.7 Theme System

```css
/* CSS class toggling trên document.body */
body.qf-dark     → Dark mode styles
body.qf-no-conf  → Ẩn AI confidence indicators
```

---

## 5. Màn hình & Tính năng chi tiết

### 5.1 Navigation Shell

#### SideRail (Left Navigation)

**Component:** `SideRail`  
**Props:** `active` (screen name), `onNav` (callback), `alertCount` (số)

**Navigation items:**
| Icon | Screen | Key |
|---|---|---|
| dashboard | Dashboard | `'dashboard'` |
| graph | Knowledge Graph | `'kg'` |
| stock/chart | Stock Detail | `'stock'` |
| news | News | `'news'` |
| chat/sparkle | AI Chat | `'chat'` |
| alerts/bell | Alerts | `'alerts'` (+ badge với alertCount) |
| jobs | Background Jobs | `'jobs'` |
| settings | Settings | `'settings'` |

**Alert badge:** Hiển thị số lượng alerts active lên icon mục Alerts, lấy từ `data.alerts.length`.

#### Topbar (Header)

**Component:** `Topbar`  
**Props:** `scenario`, `onScenario`, `onSearch`, `onLogout`, `screen`

**Thành phần:**
- Logo / Brand name "QuantyFin"
- **Scenario switcher:** Dropdown/toggle chọn một trong 4 market scenarios
- **Search button:** Click → chuyển tới màn hình Chat (`onSearch`)
- **Logout button:** Gọi `onLogout`, cập nhật localStorage về `'0'`

---

### 5.2 Màn hình Login

**Component:** `Screens.Login`  
**Props:** `onSignIn` (callback)

**Mô tả:** Màn hình xác thực người dùng. Trong prototype, không có backend auth thực sự — chỉ cần submit form để `onSignIn` được gọi, localStorage cập nhật `qf_auth = '1'`.

**Requirements:**
- Form đăng nhập với email/username và password fields
- Hiển thị brand colors (#2a2b86 primary, #fcaf16 accent)
- Responsive layout, centered card
- Không có registration flow trong prototype

---

### 5.3 Màn hình Dashboard

**Component:** `Screens.Dashboard`  
**Props:** `data`, `onNav` (navigate to screen), `onTicker` (navigate to stock detail), `scenario`

**Mục đích:** Tổng quan thị trường — điểm bắt đầu sau khi login.

**Thành phần UI (suy luận từ props và conventions):**
- **Market summary bar:** Tổng quan index (VN-Index, HNX, UPCoM), màu sắc theo scenario
- **Top movers widget:** Cổ phiếu tăng/giảm mạnh nhất trong ngày, clickable → `onTicker`
- **Portfolio snapshot:** (nếu có) Danh mục tóm tắt
- **Recent alerts:** Preview một số alerts mới nhất, link → màn hình Alerts
- **News teaser:** Tin tức nổi bật, link → màn hình News
- **Quick navigation:** Shortcut đến các màn hình khác qua `onNav`

**Behavior:**
- `data` được tính toán từ scenario — khi scenario thay đổi trên Topbar, Dashboard tự re-render
- Click vào mã cổ phiếu → `onTicker(ticker)` → chuyển sang Screens.Stock với ticker đó

---

### 5.4 Màn hình Knowledge Graph (KG)

**Component:** `Screens.KG`  
**Props:** `onTicker` (callback khi select node là cổ phiếu)

**Sub-component:** `window.KGViewer` (asset riêng `e1abcd1f`)

**Mô tả:** Biểu diễn mạng lưới quan hệ giữa các thực thể thị trường dưới dạng force-directed graph (D3.js).

**Node Types & Styling:**

| Node Type | Màu fill | Mô tả |
|---|---|---|
| Event | `#FCAF16` (gold) | Sự kiện thị trường (earnings, ĐHCĐ, chính sách) |
| Ticker/Company | TBD (navy family) | Công ty niêm yết |
| News | TBD | Bài báo/tin tức liên quan |
| Sector | TBD | Ngành/lĩnh vực |

**Interactions:**
- **Pan:** Kéo khoảng trống để di chuyển viewport
- **Zoom:** Scroll/pinch để zoom in/out
- **Select node:** Click vào node để xem chi tiết
  - Node là Ticker/Company → gọi `onTicker(ticker)` → chuyển sang Stock detail
  - Node là Event/News → hiện tooltip/panel chi tiết
- **Force simulation:** Nodes tự sắp xếp theo gravity và edge repulsion

**Technical notes:**
- `window.KGViewer` được exposed từ asset `e1abcd1f`
- Force-directed layout dùng D3 simulation
- TYPE_STYLE object kiểm soát màu sắc theo node type

---

### 5.5 Màn hình Stock Detail

**Component:** `Screens.Stock`  
**Props:** `data`, `ticker`, `onTicker`

**Mô tả:** Phân tích chi tiết một mã cổ phiếu.

**Thành phần UI (suy luận từ props và context):**
- **Header:** Tên công ty, mã ticker, logo (nếu có)
- **Price widget:** Giá hiện tại, % thay đổi, volume — màu theo scenario
- **AI Confidence indicator:** Hiển thị mức độ tin cậy của AI trong phân tích (ẩn khi `qf-no-conf` class active)
- **Price chart:** Biểu đồ giá lịch sử (line chart hoặc candlestick)
- **Financial metrics:** P/E, EPS, Market Cap, Dividend yield
- **AI Analysis summary:** Phân tích ngắn gọn từ AI về cổ phiếu
- **Related tickers:** Gợi ý cổ phiếu liên quan, clickable → `onTicker(ticker)`
- **News section:** Tin tức gần đây về cổ phiếu này

**Behavior:**
- Hiển thị data tương ứng với `ticker` từ `data`
- Click related ticker → `onTicker(newTicker)` — cập nhật App state, re-render cùng screen với ticker mới

---

### 5.6 Màn hình News

**Component:** `Screens.News`  
**Props:** `data`, `onTicker`

**Mô tả:** Feed tin tức thị trường chứng khoán Việt Nam, được phân tích và gắn nhãn bởi AI.

**Thành phần UI:**
- **Filters:** Lọc theo sector, ticker, loại tin tức (macro, corporate, regulatory)
- **News list:** Danh sách bài viết với:
  - Tiêu đề (tiếng Việt)
  - Tóm tắt / excerpt
  - Thời gian đăng
  - Sentiment tag: Positive / Neutral / Negative (AI-generated)
  - Related tickers (clickable → `onTicker`)
- **News detail:** Click vào bài → xem chi tiết hoặc mở link gốc

**Mock data notes:**
- News content sử dụng "placeholder VN-tone news" từ asset `5ff38e32`
- Nội dung tin tức được điều chỉnh theo scenario (tin khác nhau cho up/down/volatile/crisis)

---

### 5.7 Màn hình Chat (AI Agent)

**Component:** `Screens.Chat`  
**Props:** `onTicker`

**Mô tả:** Giao diện hội thoại với AI agent chuyên về phân tích chứng khoán Việt Nam.

**Entry points:**
- Từ Topbar search button → `onSearch()` → màn hình Chat
- Từ SideRail navigation item Chat

**Thành phần UI:**
- **Chat history:** Lịch sử cuộc trò chuyện (bubble chat UI)
- **Input field:** Nhập câu hỏi tự do về thị trường/cổ phiếu
- **Quick prompts:** Các câu hỏi gợi ý (ví dụ: "Phân tích FPT", "Tình hình ngân hàng hôm nay", "Cổ phiếu nào tốt trong crisis?")
- **Stock mention detection:** Khi AI đề cập mã cổ phiếu → hiện link clickable → `onTicker(ticker)`

**AI Capabilities (prototype):**
- Phân tích cổ phiếu dựa trên mock data
- So sánh theo scenario
- Trả lời câu hỏi về ngành/sector
- Giải thích các chỉ số tài chính

**Production requirements (future):**
- Kết nối với LLM Gateway (cấu hình trong Settings)
- RAG (Retrieval Augmented Generation) từ news feed thực
- Tool calling để fetch real-time data

---

### 5.8 Màn hình Alerts

**Component:** `Screens.Alerts`  
**Props:** `data`, `onTicker`

**Mô tả:** Quản lý và xem các cảnh báo thị trường thông minh.

**Thành phần UI:**
- **Active alerts list:** Danh sách alerts đang triggered (source của `alertCount` trong SideRail badge)
- **Alert cards:** Mỗi alert có:
  - Icon mức độ (critical/warning/info)
  - Mô tả điều kiện triggered
  - Thời gian
  - Ticker liên quan (clickable → `onTicker`)
  - Action buttons: Dismiss / View detail
- **Create alert:** Form tạo alert mới (price target, volume spike, news keyword)
- **Alert history:** Các alerts đã được xử lý

**Data:**
- `data.alerts` là array được generate từ `QF_DATA.build(scenario)`
- Số lượng và nội dung alerts thay đổi theo scenario

---

### 5.9 Màn hình Jobs

**Component:** `Screens.Jobs`  
**Props:** `data`

**Mô tả:** Quản lý các background jobs — tác vụ AI chạy nền như phân tích portfolio định kỳ, tạo báo cáo tự động, hoặc theo dõi điều kiện thị trường.

**Thành phần UI:**
- **Running jobs:** Danh sách tác vụ đang chạy với progress indicator
- **Completed jobs:** Kết quả của các jobs đã hoàn thành
- **Job types (suy luận):**
  - Portfolio analysis job
  - Sector sentiment scan
  - Earnings report digest
  - Custom watchlist monitor
- **Job detail:** Click vào job → xem output/result

**Đặc điểm của màn hình này:**
- Không có `onTicker` prop → Jobs screen là read-only, không navigate sang stock detail trực tiếp
- Reflect agentic nature của platform — AI agents chạy task tự động

---

### 5.10 Màn hình Settings

**Component:** `Screens.Settings`  
**Props:** _(không có props từ App — self-contained)_

**Sub-component:** `window.QFSettings` được expose từ asset `c1106d82`

**Mô tả:** Cấu hình toàn bộ platform — LLM, data sources, display preferences, notifications.

**Navigation structure (SET_NAV):**

Settings được tổ chức theo groups, mỗi group có nhiều items:

```javascript
SET_NAV = [
  {
    group: 'AI · Dữ liệu',
    items: [
      { k: 'llm', label: 'LLM Gateway', icon: 'sparkle', ... },
      // ... các items khác trong nhóm này
    ]
  },
  // ... các groups khác
]
```

**Groups Settings (suy luận từ context):**

| Group | Items (dự kiến) | Mô tả |
|---|---|---|
| AI · Dữ liệu | LLM Gateway, Data Source, Model params | Cấu hình AI backend |
| Giao diện | Theme, Language, Confidence display | UI preferences |
| Notifications | Alert channels, Email, Push | Cài đặt thông báo |
| Tài khoản | Profile, Password, API keys | User account |
| Nâng cao | Cache, Debug mode, Export | Advanced options |

**LLM Gateway configuration (key feature):**
- Endpoint URL
- API Key
- Model selection
- Temperature / sampling parameters
- Context window size
- Fallback behavior

---

## 6. Data Model & Market Scenarios

### 6.1 QF_DATA API

```javascript
// Public API
window.QF_DATA = {
  build(scenario: 'up' | 'down' | 'volatile' | 'crisis'): DataObject
}
```

**DataObject structure (suy luận từ usage patterns):**

```typescript
interface DataObject {
  stocks: StockData[]    // Dữ liệu giá, metrics của các cổ phiếu
  alerts: Alert[]        // Alerts active trong scenario này
  news: NewsItem[]       // Tin tức phù hợp với scenario
  market: MarketSummary  // VN-Index, HNX, UPCoM overview
  sectors: Sector[]      // Phân tích theo ngành
}
```

### 6.2 Market Scenarios

| Scenario | Mô tả | VN-Index | Risk level | Màu UI (dự kiến) |
|---|---|---|---|---|
| `up` | Thị trường tăng trưởng | Tăng mạnh | Thấp | Xanh lá |
| `down` | Thị trường sụt giảm | Giảm | Cao | Đỏ |
| `volatile` | Biến động cao, không xu hướng rõ | Dao động | Trung bình | Vàng/Cam |
| `crisis` | Khủng hoảng thị trường | Giảm sâu | Rất cao | Đỏ đậm |

**Default scenario:** `'volatile'` (xem App entry point)

### 6.3 VN Ticker Universe

Mock data sử dụng các mã cổ phiếu thực của thị trường Việt Nam:

**Ngân hàng (Banking):**
- VCB (Vietcombank)
- BID (BIDV)
- CTG (VietinBank)
- ACB (ACB Bank)
- MBB (MB Bank)
- TCB (Techcombank)
- VPB (VPBank)
- STB (Sacombank)

**Công nghệ & Viễn thông:**
- FPT (FPT Corporation) — **default ticker**
- VHM (Vinhomes)

**Bất động sản, Tiêu dùng, và các ngành khác** (dự kiến có thêm trong STOCKS array)

### 6.4 News Data

- Format: "placeholder VN-tone news" — nội dung tiếng Việt, phong cách báo tài chính
- Gắn với tickers liên quan
- Sentiment được gán theo scenario context
- 4 tập news tương ứng 4 scenarios (news trong crisis khác với news trong up)

---

## 7. Cấu hình & Settings

### 7.1 Runtime Configuration (Tweaks)

Trong prototype, `useTweaks` hook quản lý 3 tham số runtime:

```javascript
useTweaks({
  theme: 'light',           // 'light' | 'dark'
  scenario: 'volatile',     // 'up' | 'down' | 'volatile' | 'crisis'
  showConfidence: true,     // boolean
})
```

`QfTweaks` component (TweaksPanel) hiển thị UI để thay đổi các giá trị này — đây là **development overlay**, không phải Settings production.

### 7.2 Persistent Settings (localStorage)

| Key | Giá trị | Mô tả |
|---|---|---|
| `qf_auth` | `'0'` hoặc `'1'` | Trạng thái đăng nhập |
| (future) `qf_theme` | `'light'` / `'dark'` | Theme preference |
| (future) `qf_scenario` | scenario string | Scenario preference |

### 7.3 LLM Gateway Settings (Production)

Màn hình Settings/LLM Gateway cho phép cấu hình:

- **Provider:** OpenAI, Anthropic, Azure OpenAI, hoặc self-hosted
- **Endpoint:** Custom API endpoint URL
- **API Key:** Được lưu encrypted hoặc per-session
- **Model:** Chọn model cụ thể (GPT-4, Claude 3, Gemini, v.v.)
- **Parameters:** temperature, max_tokens, system prompt
- **Connection test:** Nút test kết nối và xem latency

---

## 8. User Flows chính

### 8.1 Login Flow

```
Truy cập app (lần đầu)
  → localStorage.qf_auth = null
  → App: setAuthed(true) [auto-login]
  → Màn hình Dashboard

Truy cập app (đã logout trước)
  → localStorage.qf_auth = '0'
  → App: setAuthed(false)
  → Màn hình Login
    → User điền form
    → Click "Đăng nhập"
    → onSignIn() → localStorage = '1' → setAuthed(true)
    → Màn hình Dashboard
```

### 8.2 Market Analysis Flow (Primary Flow)

```
Dashboard
  → Topbar: Chọn scenario "crisis"
  → data = QF_DATA.build('crisis') [re-computed]
  → Dashboard re-render với crisis context
  → Xem top movers giảm mạnh
  → Click mã "VCB"
  → onTicker('VCB') → setTicker('VCB') → setScreen('stock')
  → Màn hình Stock Detail: VCB trong crisis scenario
  → Xem phân tích AI, confidence indicator
  → Click "Xem tin tức liên quan"
  → Màn hình News: filter theo VCB
```

### 8.3 Knowledge Graph Exploration Flow

```
SideRail: Click icon "graph"
  → setScreen('kg')
  → Màn hình KG: force-directed graph load
  → User pan/zoom để explore
  → Click node Event (vàng #FCAF16): "Kết quả kinh doanh Q1/2026"
  → Panel hiện chi tiết event
  → Click edge → xem các công ty liên quan đến event này
  → Click node Ticker "FPT"
  → onTicker('FPT') → setTicker('FPT') → setScreen('stock')
  → Màn hình Stock Detail: FPT
```

### 8.4 AI Chat Flow

```
Topbar: Click search icon
  → onSearch() → setScreen('chat')
  → Màn hình Chat

User gõ: "Phân tích cổ phiếu ngân hàng trong giai đoạn khủng hoảng"
  → AI agent process
  → Trả về phân tích với mention các mã: VCB, BID, CTG, ...
  → Mỗi ticker mention là link clickable
  → User click "VCB"
  → onTicker('VCB') → chuyển sang Stock Detail
```

### 8.5 Alert Management Flow

```
SideRail: Alert icon badge hiện "5" alerts
  → Click → setScreen('alerts')
  → Màn hình Alerts: hiện 5 alerts active
  → User review từng alert
  → Click alert có ticker "MBB giảm 5%"
  → onTicker('MBB') → Stock Detail: MBB
  → Quay lại Alerts
  → Dismiss các alerts đã xử lý
```

### 8.6 Logout Flow

```
Topbar: Click "Logout"
  → onLogout()
  → localStorage.setItem('qf_auth', '0')
  → setAuthed(false)
  → Render Screens.Login
```

---

## 9. Non-functional Requirements

### 9.1 Performance

| Yêu cầu | Target |
|---|---|
| Initial load time (standalone HTML) | < 3s trên 4G |
| Scenario switch re-render | < 100ms (QF_DATA.build là synchronous) |
| Knowledge Graph render (100 nodes) | < 2s cho initial layout |
| Chat response time (production) | < 5s cho LLM response |

### 9.2 Accessibility

- Hỗ trợ keyboard navigation cho SideRail và Topbar
- Color contrast đạt WCAG AA cho text trên background #2a2b86
- Knowledge Graph: tooltip text cho node không chỉ dựa vào màu sắc
- Alert badges: có aria-label chứa số lượng

### 9.3 Responsive Design

| Breakpoint | Behavior |
|---|---|
| Desktop (>1200px) | Full layout: SideRail + Topbar + Main content |
| Tablet (768-1200px) | SideRail collapse thành icon-only |
| Mobile (<768px) | Bottom navigation thay SideRail; limited features |

### 9.4 Security (Production)

- **Authentication:** Thay thế localStorage bằng JWT token với proper expiry
- **LLM API Key:** Không store trên client — proxy qua backend
- **XSS Prevention:** Sanitize mọi user input trước khi render
- **HTTPS Only:** Enforce HTTPS, HSTS header
- **Rate limiting:** Giới hạn Chat API calls để tránh abuse

### 9.5 Internationalization (i18n)

- **Primary:** Tiếng Việt (VN)
- **Secondary:** Tiếng Anh (EN)
- Số tiền: định dạng VNĐ (triệu, tỷ đồng)
- Ngày giờ: GMT+7 (Asia/Ho_Chi_Minh)
- Số thập phân: dùng dấu phẩy (,) theo chuẩn VN

---

## 10. Roadmap & Phân kỳ

### Phase 1 — Prototype (Hiện tại)

**Status:** Hoàn thiện demo/prototype  
**Deliverable:** `QuantyFin_Standalone.html`

**Scope:**
- [x] 9 screens với mock data
- [x] 4 market scenarios
- [x] Knowledge Graph visualization (D3 force-directed)
- [x] AI Chat UI (mock responses)
- [x] Alert system (mock data)
- [x] Background Jobs UI
- [x] Settings UI với LLM Gateway config form
- [x] Light/Dark theme toggle
- [x] Confidence indicator toggle

### Phase 2 — MVP Backend Integration

**Timeline:** TBD  
**Target:** Production-ready với real data

**Scope:**
- [ ] Backend API (Node.js/FastAPI)
- [ ] Real-time market data feed (HSX, HNX APIs hoặc data provider)
- [ ] LLM Gateway integration (OpenAI/Anthropic/Azure)
- [ ] Proper authentication (JWT, OAuth2)
- [ ] Database cho user data, alerts, portfolio
- [ ] WebSocket cho real-time price updates
- [ ] News aggregation + NLP sentiment pipeline
- [ ] Knowledge Graph với real relationships (từ news NER)

### Phase 3 — Advanced AI Features

**Timeline:** TBD  
**Target:** Differentiated AI capabilities

**Scope:**
- [ ] Agentic task automation (scheduled analysis jobs)
- [ ] RAG pipeline từ VN financial documents
- [ ] Multi-agent orchestration (analysis + execution agents)
- [ ] Portfolio optimization suggestions
- [ ] Backtesting engine
- [ ] Alert ML model (anomaly detection thay vì rule-based)
- [ ] Report generation (xuất PDF/DOCX)

### Phase 4 — Scale & Ecosystem

**Timeline:** TBD  
**Target:** Platform ecosystem

**Scope:**
- [ ] API marketplace cho data providers
- [ ] Plugin system cho custom screens
- [ ] Mobile app (React Native)
- [ ] Team collaboration features
- [ ] White-label option cho brokerage firms

---

## 11. Phụ lục kỹ thuật

### 11.1 Component Props Reference

```typescript
// App-level callbacks
type OnNavCallback = (screen: string) => void
type OnTickerCallback = (ticker: string) => void
type OnSignInCallback = () => void
type OnLogoutCallback = () => void

// Screen Props
interface LoginScreenProps     { onSignIn: OnSignInCallback }
interface DashboardScreenProps { data: DataObject; onNav: OnNavCallback; onTicker: OnTickerCallback; scenario: string }
interface KGScreenProps        { onTicker: OnTickerCallback }
interface StockScreenProps     { data: DataObject; ticker: string; onTicker: OnTickerCallback }
interface NewsScreenProps      { data: DataObject; onTicker: OnTickerCallback }
interface ChatScreenProps      { onTicker: OnTickerCallback }
interface AlertsScreenProps    { data: DataObject; onTicker: OnTickerCallback }
interface JobsScreenProps      { data: DataObject }
interface SettingsScreenProps  {}  // self-contained

// Navigation Shell Props
interface SideRailProps { active: string; onNav: OnNavCallback; alertCount: number }
interface TopbarProps   { scenario: string; onScenario: (s: string) => void; onSearch: () => void; onLogout: OnLogoutCallback; screen: string }
```

### 11.2 Screen Navigation Map

```
Login ──────────────────────────────────────────► Dashboard
                                                       │
Dashboard ◄──── onTicker ──── (any screen) ──────┐    │
    │                                             │    │
    ├──► Stock Detail ◄─── onTicker ─────────────┤    │
    ├──► Knowledge Graph ──── onTicker ──────────┤    │
    ├──► News ──── onTicker ──────────────────────┤    │
    ├──► Chat ──── onTicker ──────────────────────┘    │
    ├──► Alerts ──── onTicker ────────────────────┘    │
    ├──► Jobs (read-only)                              │
    └──► Settings (self-contained)                     │
                                                       │
Topbar Search ──────────────────────────────────► Chat │
Topbar Logout ──────────────────────────────────► Login◄┘
```

### 11.3 Icon Registry (Shared UI)

Icons được định nghĩa dưới dạng SVG path strings trong `ICONS` object:

| Key | Dùng tại |
|---|---|
| `dashboard` | SideRail - Dashboard item |
| `graph` | SideRail - Knowledge Graph item |
| `stock` / `chart` | SideRail - Stock item |
| `news` | SideRail - News item |
| `chat` / `sparkle` | SideRail - Chat item; Settings LLM Gateway |
| `bell` | SideRail - Alerts item |
| `jobs` | SideRail - Jobs item |
| `settings` | SideRail - Settings item |

### 11.4 CSS Class Conventions

| Class | Scope | Effect |
|---|---|---|
| `.app-shell` | Root div | App container (flex layout) |
| `.app-main` | Content area | Main scrollable region |
| `body.qf-dark` | Global | Activate dark mode CSS variables |
| `body.qf-no-conf` | Global | Hide all `.confidence-indicator` elements |

### 11.5 Known Limitations (Prototype)

1. **Mock data only:** Không có real market data — mọi giá, tin tức đều là mock
2. **No persistence beyond localStorage:** User data (portfolio, custom alerts) không persist qua sessions
3. **AI Chat is non-functional:** Chat UI có nhưng không kết nối LLM thực
4. **Jobs are static:** Background jobs không thực sự chạy
5. **Authentication is trivial:** localStorage toggle — không có real auth security
6. **Single-user:** Không có multi-user, team, hoặc role-based access control
7. **No real-time:** Không có WebSocket, price updates là static trong scenario

---

*Tài liệu này được sinh tự động từ phân tích source code của `QuantyFin_Standalone.html`. Được gắn nhãn "chưa qua kiểm duyệt" — cần review bởi Product Owner trước khi dùng làm tài liệu chính thức.*
