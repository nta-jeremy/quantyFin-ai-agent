# Đặc tả Thiết kế KGViewer & Hướng dẫn Cấu hình Bộ Thu thập Tin tức (News Crawler)

Tài liệu này bao gồm hai phần chính: Đặc tả thiết kế kỹ thuật của thành phần trực quan hóa Đồ thị Tri thức ([KGViewer.tsx](file:///Users/tunganh252/Desktop/Projects/Finance/quantyFin-ai-agent/docs/sample_src/frontend/src/components/KGViewer.tsx)) và hướng dẫn thiết lập hệ thống tự động thu thập tin tức (News Crawler System) qua ba cấp độ công nghệ: RSS, API và Playwright.

---

## PHẦN I: ĐẶC TẢ THIẾT KẾ KỸ THUẬT THÀNH PHẦN KGVIEWER

Thành phần `KGViewer` chịu trách nhiệm biểu diễn mối quan hệ nhân quả phức tạp giữa các yếu tố vĩ mô (`Event`), nhóm ngành (`Sector`), doanh nghiệp/cổ phiếu (`Stock`) và ban lãnh đạo (`Leader`).

```mermaid
graph TD
    A[Dữ liệu Đầu vào: KGNode[] & KGEdge[]] --> B[Bộ Tính toán Bố cục: runForceLayout]
    B --> C[Tính lực đẩy Repulsion giữa các nút]
    B --> D[Tính lực hút Hooke dọc theo các cạnh]
    B --> E[Tính lực kéo Gravity về tâm màn hình]
    B --> F[Hạ nhiệt tích phân Cooling]
    F --> G[Tập hợp Tọa độ Nút: LayoutNode[]]
    G --> H[Trình render SVG tương tác]
    H --> I[Xử lý kéo thả Pan & Cuộn chuột Zoom]
    H --> J[Tương tác Click & Làm nổi bật trực quan]
```

### 1. Thuật toán Bố cục Hướng lực tự chế (Custom Force-directed Layout)
Để không phụ thuộc vào các thư viện nặng nề bên ngoài như D3.js, `KGViewer` sử dụng một thuật toán hướng lực thuần vật lý chạy trực tiếp trong luồng Render của React:

* **Hàm thực thi:** `runForceLayout(nodes, edges, opts)`
* **Số bước lặp (Iterations):** Mặc định chạy `220` bước lặp để đồ thị tự động đạt trạng thái cân bằng lực tĩnh trước khi vẽ.
* **Các loại lực vật lý được giả lập:**
  1. **Lực đẩy Coulomb (Repulsion):** Đẩy các nút ra xa nhau để tránh chồng chéo. Tỷ lệ nghịch với bình phương khoảng cách ($F_{rep} = \frac{repulsion}{d^2}$).
  2. **Lực hút Hooke (Attraction):** Co các nút có liên kết cạnh lại gần nhau. Tỷ lệ thuận với chiều dài tự nhiên của lò xo ($F_{att} = 0.04 \times w \times (d - linkDist)$).
  3. **Lực kéo xuyên tâm (Gravity):** Kéo tất cả các nút về tâm màn hình ($cx$, $cy$) với hệ số yếu $0.003$ để giữ đồ thị không bị trôi ra ngoài biên SVG.
  4. **Lớp hạ nhiệt (Cooling):** Ở mỗi bước lặp, tốc độ dịch chuyển của nút được nhân với hệ số giảm dần $cooling = 1 - \frac{it}{iters}$ để đồ thị dừng lại nhẹ nhàng khi đạt trạng thái cân bằng.

### 2. Định dạng trực quan (Visual Styles)

#### A. Định kiểu Nút (Nodes Style)
* **Stock (Hình chữ nhật bo góc):** Màu nền xanh đậm `#2A2B86`, viền `#16175A`. Hiển thị mã ticker (FPT, HPG,...) bằng font chữ Mono.
* **Event (Hình tròn):** Màu vàng cam `#FCAF16`, viền `#a36f00`. Hiển thị nhãn viết tắt.
* **Sector (Hình tròn):** Màu tím `#7C6CF5`, viền `#3a31a1`.
* **Leader (Hình tròn):** Màu xanh lá `#10b981`, viền `#0a5f44`.

#### B. Định kiểu Cạnh liên kết (Edges Style)

| Loại mối quan hệ | Kiểu đường vẽ | Màu sắc | Ý nghĩa |
| :--- | :---: | :---: | :--- |
| `IMPACTS_POS` / `MANAGES` | Đường liền nét | Xanh lá (`#10b981`) | Tác động tích cực / Quản lý |
| `IMPACTS_NEG` / `AMPLIFIES` | Đường liền nét | Đỏ (`#ef4444`) | Tác động tiêu cực / Khuyếch đại rủi ro |
| `PRESSURES` | Đường liền nét | Vàng (`#f59e0b`) | Gây áp lực tiêu cực lên chỉ số |
| `BELONGS_TO` | Đường liền nét | Xanh nhạt (`#cbd5f1`) | Thành viên thuộc nhóm ngành |
| `CORRELATES` | Đường đứt nét | Xám tím (`#a3a8d8`) | Quan hệ đồng biến/nghịch biến giá |
| `INFLUENCES` | Đường đứt nét | Tím (`#7C6CF5`) | Tác động gián tiếp từ lãnh đạo |
| `REDUCES` | Đường đứt nét | Xanh lá (`#10b981`) | Giảm thiểu áp lực/rủi ro |

### 3. Tương tác và Trải nghiệm Người dùng
* **Kéo & Thả (Pan):** Sử dụng sự kiện chuột `onMouseDown`, `onMouseMove` để dịch chuyển tọa độ nhóm `<g>` của SVG, cho phép người dùng di chuyển toàn bộ bản đồ tri thức.
* **Thu phóng (Zoom):** Đăng ký sự kiện cuộn chuột (`wheel`) chủ động (`{ passive: false }`) để tăng/giảm hệ số `scale` từ `0.4x` đến `2.5x` tại tâm con trỏ chuột.
* **Làm nổi bật vùng lân cận (Highlight Propagation):** Khi người dùng nhấp chọn một nút:
  * Nút được chọn sẽ hiển thị thêm vòng tròn hào quang bao quanh.
  * Toàn bộ các nút không có liên kết trực tiếp với nút được chọn sẽ bị giảm độ mờ (opacity) xuống `0.25`.
  * Các đường liên kết không kết nối với nút được chọn sẽ giảm độ mờ xuống `0.15`.
  * Giúp người dùng tập trung hoàn toàn vào luồng tác động trực tiếp của thực thể được chọn.

---

## PHẦN II: HƯỚNG DẪN THIẾT LẬP BỘ THU THẬP TIN TỨC (NEWS CRAWLER)

Để cung cấp dòng thông tin vĩ mô và tin doanh nghiệp liên tục cho Đồ thị Tri thức, hệ thống vận hành 3 cấp độ (Tiers) thu thập dữ liệu tự động. Dưới đây là hướng dẫn cài đặt và vận hành từng cấp độ dành cho Lập trình viên:

```
                  ┌──────────────────────────────────────────────┐
                  │        Tin tức tài chính từ internet         │
                  └──────┬──────────────┬──────────────┬─────────┘
                         │              │              │
                         ▼              ▼              ▼
                    [ RSS Tier ]   [ API Tier ]   [ Playwright Tier ]
                         │              │              │
                         └──────┬───────┴──────────────┘
                                │ (Dữ liệu thô / JSON)
                                ▼
                  ┌──────────────────────────────┐
                  │   AI Filtering & Clean up    │
                  └─────────────┬────────────────┘
                                ▼ (Cảm nhận & Quan hệ thực thể)
                  ┌──────────────────────────────┐
                  │    Knowledge Graph Update    │
                  └──────────────────────────────┘
```

### 1. Cấp độ 1: Thu thập qua RSS (RSS Ingestion Tier)
* **Phạm vi áp dụng:** Các trang tin lớn hỗ trợ định dạng chuẩn RSS (CafeF, Vietstock, VnEconomy,...).
* **Đặc điểm:** Tải dữ liệu siêu tốc, tiêu tốn cực ít băng thông, không sợ bị chặn (block IP).

#### Thiết lập mã nguồn Node.js thu thập RSS:
```typescript
import Parser from 'rss-parser';

const parser = new Parser();

interface RSSItem {
  title: string;
  link: string;
  pubDate: string;
  contentSnippet?: string;
}

async function fetchRSS(rssUrl: string): Promise<RSSItem[]> {
  try {
    const feed = await parser.parseURL(rssUrl);
    return feed.items.map(item => ({
      title: item.title || '',
      link: item.link || '',
      pubDate: item.pubDate || '',
      contentSnippet: item.contentSnippet
    }));
  } catch (error) {
    console.error(`Lỗi khi cào dữ liệu RSS từ ${rssUrl}:`, error);
    return [];
  }
}
```

### 2. Cấp độ 2: Tích hợp API Dữ liệu (Structured API Tier)
* **Phạm vi áp dụng:** Kết nối với các bên cung cấp dữ liệu tài chính chuyên nghiệp có API cấu trúc (FiinTrade, Vietstock API, hoặc API cổng thông tin nội bộ).
* **Đặc điểm:** Dữ liệu có cấu trúc định dạng JSON sạch, độ tin cậy cao, có sẵn mã cổ phiếu được gắn thẻ (tagged tickers).

#### Cấu hình Client kết nối API:
```typescript
import axios from 'axios';

interface APIConfig {
  baseUrl: string;
  apiKey: string;
}

const config: APIConfig = {
  baseUrl: process.env.FINANCIAL_API_URL || 'https://api.tin-tuc-tai-chinh.vn/v1',
  apiKey: process.env.FINANCIAL_API_KEY || 'your-secure-api-key'
};

async function getLatestNews(limit = 50) {
  try {
    const response = await axios.get(`${config.baseUrl}/news/latest`, {
      headers: { 'Authorization': `Bearer ${config.apiKey}` },
      params: { limit, fields: 'title,content,published_at,tickers,source' }
    });
    return response.data;
  } catch (error) {
    console.error('Lỗi kết nối API dữ liệu tài chính:', error);
    throw error;
  }
}
```

### 3. Cấp độ 3: Quét sâu bằng Playwright (Dynamic Browser Crawling Tier)
* **Phạm vi áp dụng:** Các trang tin tức dạng Single Page Application (SPA), sử dụng Ajax để tải tin, hoặc các trang chặn chặn bot cào tin thông thường.
* **Đặc điểm:** Giả lập trình duyệt Chrome thật, tải được toàn bộ nội dung dựng bằng Javascript, lấy được ảnh đại diện (thumbnail) và các siêu dữ liệu nâng cao.

#### Thiết lập kịch bản cào tin bằng Playwright:
```javascript
const { chromium } = require('playwright');

async function scrapeDynamicNews(url) {
  // 1. Khởi chạy trình duyệt ở chế độ ẩn danh (headless)
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
  });
  const page = await context.newPage();

  try {
    // 2. Điều hướng và đợi trang tải xong cấu trúc DOM chính
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });
    
    // Đợi phần tử chứa danh sách tin hiển thị
    await page.waitForSelector('.list-news-item', { timeout: 10000 });

    // 3. Trích xuất dữ liệu từ các phần tử DOM
    const articles = await page.evaluate(() => {
      const items = document.querySelectorAll('.list-news-item');
      return Array.from(items).map(el => {
        const titleEl = el.querySelector('.title-news');
        const linkEl = el.querySelector('a');
        const summaryEl = el.querySelector('.summary-news');
        
        return {
          title: titleEl ? titleEl.textContent.trim() : '',
          url: linkEl ? linkEl.href : '',
          summary: summaryEl ? summaryEl.textContent.trim() : '',
        };
      });
    });

    return articles;
  } catch (error) {
    console.error(`Lỗi quét Playwright tại trang ${url}:`, error);
    return [];
  } finally {
    // 4. Luôn luôn đóng trình duyệt để giải phóng tài nguyên bộ nhớ
    await browser.close();
  }
}
```

## BẢNG SO SÁNH GIỮA CÁC PHƯƠNG ÁN THU THẬP

| Tiêu chí | RSS Ingestion | Structured API | Playwright Crawler |
| :--- | :---: | :---: | :---: |
| **Băng thông** | Cực thấp (Chỉ tải XML) | Thấp (Chỉ tải JSON sạch) | Rất cao (Tải toàn bộ tài nguyên Web) |
| **Tải lượng CPU** | Không đáng kể | Rất thấp | Cao (Chạy engine trình duyệt Chromium) |
| **Độ ổn định** | Rất cao (Hiếm khi đổi link RSS) | Rất cao (API có phiên bản rõ ràng) | Trung bình (Dễ lỗi khi web đổi giao diện) |
| **Khả năng bị chặn** | Hầu như không | Không (Vì có API Key) | Cao (Cần cấu hình Proxy và User-Agent) |
| **Mức độ phức tạp**| Cực kỳ đơn giản | Đơn giản | Phức tạp (Cần bảo trì kịch bản DOM selector) |
