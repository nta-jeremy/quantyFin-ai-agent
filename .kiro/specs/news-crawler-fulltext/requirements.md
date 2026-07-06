# Requirements Document

## Introduction

Tính năng `news-crawler-fulltext` nâng cấp luồng thu thập tin tức hiện tại của hệ thống quantyFin-ai-agent (FastAPI, Python, httpx, SQLModel, Postgres) từ chỗ chỉ lấy được phần teaser của thẻ RSS `<description>` lên thành thu thập "bài viết thật sự" gồm tiêu đề, summary (teaser) và full body (toàn văn thân bài).

Việc nâng cấp xuất phát từ các vấn đề đã được kiểm chứng thực nghiệm:

1. Quá nửa nguồn RSS đang hỏng (sai URL, channel rỗng, trả HTML thay vì XML, domain chết) nhưng lỗi bị nuốt âm thầm — API vẫn trả HTTP 200 với `total_saved = 0`, không có cảnh báo.
2. Ngay cả nguồn còn sống, RSS chỉ cung cấp teaser 1–3 câu (không có `content:encoded`), nên pipeline AI (phân tích cảm xúc, bóc tách thực thể) đang chạy trên dữ liệu nghèo nàn.
3. Trang bài viết tĩnh (ví dụ TuoiTre) cho phép lấy full body bằng HTTP fetch + thư viện trích xuất (trafilatura/readability), không bắt buộc Playwright.

Giải pháp áp dụng kiến trúc 3 tầng: RSS làm tầng khám phá (discovery) lấy URL + tiêu đề + teaser; HTTP fetch + thư viện trích xuất làm tầng lấy full body; Playwright làm tầng dự phòng (fallback) có điều kiện cho các nguồn không có RSS hoặc khi web fetch không lấy đủ nội dung. Hệ thống vận hành trong ràng buộc tài nguyên 2 CPU / 2 GB RAM, nên phải kiểm soát chặt mức độ song song và giới hạn việc dùng Playwright.

Tính năng phải tương thích ngược với scheduler hiện có (`scheduled_crawler_task`), cấu hình `CrawlerConfig` trong DB, các endpoint API hiện tại, và pipeline AI hiện hành (pipeline AI sau nâng cấp sẽ chạy trên full body).

Phạm vi lấy full content mở rộng ngoài chứng khoán: các bài TOP/HOT (top N) thuộc các chủ đề kinh tế, kinh doanh, đầu tư, chứng khoán, xã hội, chính trị.

## Glossary

- **News_Crawler**: Hệ thống thu thập tin tức tổng thể, điều phối ba tầng discovery, extraction và fallback.
- **Source_Registry**: Cấu trúc cấu hình tập trung khai báo các nguồn tin, mỗi mục gồm tên nguồn, loại (rss/playwright), URL, danh sách chủ đề (topics), tầng (tier) và các tham số liên quan. Thay thế cách hard-code class scraper từng site.
- **RSS_Discovery**: Thành phần tầng 1, đọc feed RSS của một nguồn để lấy danh sách bài gồm tiêu đề, URL và teaser.
- **Content_Extractor**: Thành phần tầng 2, tải trang bài viết qua HTTP tĩnh và trích xuất toàn văn thân bài bằng thư viện trích xuất (trafilatura/readability).
- **Playwright_Fallback**: Thành phần tầng 3, dùng trình duyệt headless để lấy nội dung cho nguồn không có RSS hoặc khi Content_Extractor không lấy đủ nội dung.
- **Pre_Filter**: Bộ lọc nhẹ chạy trên tiêu đề và teaser trước khi tải full body.
- **Full_Content_Filter**: Bộ lọc/đánh giá chính xác chạy trên full body sau khi đã tải.
- **Dedup_Service**: Cơ chế chống trùng lặp dựa trên trường `url`, đảm bảo chỉ tải full body cho URL chưa có trong DB.
- **Source_Health_Report**: Báo cáo sức khỏe nguồn, ghi nhận trạng thái từng nguồn sau mỗi lần chạy.
- **Source_Status**: Trạng thái của một nguồn sau khi chạy, thuộc tập giá trị {ok, empty, dead, parse_error, blocked}.
- **Jobs_View**: Màn hình Jobs ở phía giao diện hiển thị kết quả Source_Health_Report.
- **Scheduler**: Tác vụ định kỳ `scheduled_crawler_task` chạy theo `CrawlerConfig` (schedule_time, active_sources) trong DB.
- **AI_Pipeline**: Pipeline AI hiện có (`process_pending_news_articles` dùng CrewAI) phân tích cảm xúc và bóc tách thực thể.
- **NewsArticle**: Bảng/Model lưu bài viết, gồm các cột `title`, `content`, `summary`, `url`, `source`, `status`, `published_at` và các trường sentiment/entities.
- **Teaser**: Đoạn tóm tắt ngắn lấy từ thẻ RSS `<description>`.
- **Full_Body**: Toàn văn thân bài lấy từ trang bài viết.
- **Topic**: Chủ đề nội dung, thuộc tập {kinh tế, kinh doanh, đầu tư, chứng khoán, xã hội, chính trị}.
- **Top_N**: Số lượng bài xếp hạng cao nhất (top/hot) cần lấy full content cho mỗi nguồn/chủ đề, là tham số cấu hình.
- **Fetch_Concurrency_Limit**: Giới hạn số lượng tải full body chạy song song tại một thời điểm, là tham số cấu hình.
- **Trace_Id**: Định danh truy vết một lần chạy crawl để gắn vào log.

## Requirements

### Requirement 1: Cấu hình nguồn tập trung (Source Registry)

**User Story:** Là một lập trình viên vận hành hệ thống, tôi muốn khai báo nguồn tin qua một cấu trúc cấu hình tập trung thay vì hard-code từng class scraper, để có thể thêm, sửa, xóa nguồn nhanh chóng và an toàn.

#### Acceptance Criteria

1. THE Source_Registry SHALL lưu trữ mỗi nguồn tin với các thuộc tính: tên nguồn duy nhất có độ dài từ 1 đến 100 ký tự, loại nguồn thuộc tập {rss, playwright}, URL theo giao thức http hoặc https, danh sách gồm ít nhất một Topic, và tầng (tier) là số nguyên từ 1 đến 5.
2. WHEN News_Crawler khởi tạo danh sách nguồn cần chạy, THE News_Crawler SHALL đọc cấu hình nguồn từ Source_Registry trước khi xử lý bất kỳ nguồn nào.
3. WHERE một nguồn được khai báo trong Source_Registry với loại nguồn là rss, THE News_Crawler SHALL xử lý nguồn đó bằng RSS_Discovery.
4. WHERE một nguồn được khai báo trong Source_Registry với loại nguồn là playwright, THE News_Crawler SHALL xử lý nguồn đó bằng Playwright_Fallback.
5. IF cấu hình `active_sources` trong CrawlerConfig tham chiếu một tên nguồn không tồn tại trong Source_Registry, THEN THE News_Crawler SHALL ghi log cảnh báo kèm tên nguồn đó và tiếp tục xử lý các nguồn hợp lệ còn lại.
6. THE News_Crawler SHALL cho phép thêm hoặc gỡ một nguồn bằng cách chỉnh sửa Source_Registry mà không cần thay đổi mã điều phối của News_Crawler.
7. IF một nguồn trong Source_Registry thiếu một thuộc tính bắt buộc hoặc có loại nguồn không thuộc tập {rss, playwright}, THEN THE News_Crawler SHALL bỏ qua nguồn đó, ghi log lỗi chỉ ra nguyên nhân, và tiếp tục xử lý các nguồn còn lại.
8. IF hai nguồn có cùng tên trong Source_Registry, THEN THE News_Crawler SHALL dùng bản khai báo xuất hiện đầu tiên và ghi log cảnh báo về tên nguồn trùng.

### Requirement 2: Khám phá bài viết qua RSS (RSS Discovery)

**User Story:** Là người vận hành, tôi muốn tầng RSS lấy đúng danh sách bài viết mới nhất kèm tiêu đề, URL và teaser từ các nguồn còn hoạt động, để cung cấp đầu vào cho các tầng trích xuất tiếp theo.

#### Acceptance Criteria

1. WHEN RSS_Discovery xử lý một nguồn loại rss, THE RSS_Discovery SHALL trích xuất từ tối đa 100 mục mới nhất theo thứ tự xuất hiện trong feed các trường tiêu đề, URL và Teaser, và gán Teaser bằng chuỗi rỗng khi mục feed không có teaser.
2. THE Source_Registry SHALL chứa URL RSS đã được xác nhận còn hoạt động cho mỗi nguồn loại rss.
3. WHEN RSS_Discovery nhận được nội dung feed hợp lệ, THE RSS_Discovery SHALL chuẩn hóa URL bài viết thành URL tuyệt đối.
4. IF nội dung trả về từ URL RSS không phải định dạng XML hợp lệ, THEN THE RSS_Discovery SHALL gán Source_Status `parse_error` cho nguồn đó và không tạo bài viết nào từ nguồn đó.
5. IF feed RSS hợp lệ nhưng không chứa mục bài viết nào, THEN THE RSS_Discovery SHALL gán Source_Status `empty` cho nguồn đó.
6. IF URL RSS không phản hồi trong vòng 30 giây, trả về mã lỗi HTTP từ 400 trở lên ngoài các mã 401, 403 và 429, hoặc không phân giải được tên miền, THEN THE RSS_Discovery SHALL gán Source_Status `dead` cho nguồn đó.
7. IF một nguồn vừa trả về mã lỗi HTTP từ 400 trở lên vừa có nội dung không phải XML hợp lệ, THEN THE RSS_Discovery SHALL ưu tiên gán Source_Status `dead` cho nguồn đó.
8. WHEN feed RSS hợp lệ chứa ít nhất một mục có đủ tiêu đề và URL, THE RSS_Discovery SHALL gán Source_Status `ok` cho nguồn đó.
9. IF URL RSS trả về mã lỗi HTTP 401, 403 hoặc 429, THEN THE RSS_Discovery SHALL gán Source_Status `blocked` cho nguồn đó.
10. IF một mục feed thiếu tiêu đề hoặc URL, THEN THE RSS_Discovery SHALL bỏ qua mục đó và không tạo bài viết từ mục đó.

### Requirement 3: Xếp hạng và chọn bài Top/Hot theo chủ đề

**User Story:** Là người dùng nghiệp vụ, tôi muốn hệ thống chỉ lấy full body cho các bài top/hot thuộc các chủ đề quan tâm, để tập trung tài nguyên vào nội dung giá trị cao thay vì tải toàn bộ.

#### Acceptance Criteria

1. THE News_Crawler SHALL gán mỗi nguồn với một hoặc nhiều Topic thuộc tập {kinh tế, kinh doanh, đầu tư, chứng khoán, xã hội, chính trị} theo khai báo trong Source_Registry.
2. WHEN RSS_Discovery trả về danh sách bài viết khác rỗng cho một nguồn, THE News_Crawler SHALL xác định thứ hạng các bài theo thứ tự xuất hiện trong feed, trong đó bài đứng trước được xếp hạng cao hơn bài đứng sau.
3. WHERE Top_N được cấu hình cho một nguồn, THE News_Crawler SHALL chọn các bài có thứ hạng cao nhất của nguồn đó với số lượng bằng giá trị nhỏ hơn giữa Top_N và tổng số bài hiện có của nguồn, để đưa vào bước tải full body.
4. IF một nguồn trong Source_Registry được khai báo với Topic nằm ngoài tập {kinh tế, kinh doanh, đầu tư, chứng khoán, xã hội, chính trị}, THEN THE News_Crawler SHALL loại nguồn đó khỏi quá trình xử lý và ghi nhận lỗi chỉ ra Topic không hợp lệ, đồng thời tiếp tục xử lý các nguồn còn lại.
5. THE Top_N SHALL là tham số cấu hình kiểu số nguyên có giá trị từ 1 đến 100, có thể điều chỉnh mà không cần thay đổi mã điều phối.
6. IF RSS_Discovery trả về danh sách bài viết rỗng cho một nguồn, THEN THE News_Crawler SHALL bỏ qua bước tải full body cho nguồn đó và ghi nhận sự kiện chỉ ra không có bài để xử lý.
7. WHERE Top_N không được cấu hình cho một nguồn, THE News_Crawler SHALL áp dụng giá trị Top_N mặc định cho nguồn đó.

### Requirement 4: Lọc hai giai đoạn và chống trùng lặp

**User Story:** Là người vận hành, tôi muốn áp dụng lọc nhẹ trước khi tải full body và lọc chính xác sau khi có full body, đồng thời không tải lại bài đã có, để tiết kiệm tài nguyên và tránh xử lý dư thừa.

#### Acceptance Criteria

1. WHEN News_Crawler nhận danh sách bài từ RSS_Discovery, THE Pre_Filter SHALL đánh giá từng bài dựa trên tiêu đề và Teaser theo bộ tiêu chí lọc đã cấu hình và gán kết quả đạt hoặc không đạt trước khi tải Full_Body.
2. IF một bài không đạt Pre_Filter, THEN THE News_Crawler SHALL loại bài đó khỏi bước tải Full_Body.
3. WHEN một bài đạt Pre_Filter, THE Dedup_Service SHALL kiểm tra trường `url` của bài đó với dữ liệu đã lưu trong NewsArticle và trả về kết quả `url` đã tồn tại hoặc chưa tồn tại.
4. IF `url` của một bài đã tồn tại trong NewsArticle, THEN THE News_Crawler SHALL bỏ qua việc tải Full_Body cho bài đó.
5. WHEN `url` của một bài chưa tồn tại trong NewsArticle, THE News_Crawler SHALL tiến hành tải Full_Body cho bài đó.
6. IF việc tải Full_Body cho một bài thất bại, THEN THE News_Crawler SHALL loại bài đó khỏi bước lưu trữ, ghi nhận trạng thái lỗi cho bài đó, và bảo toàn việc xử lý các bài còn lại.
7. WHEN một bài đã có Full_Body, THE Full_Content_Filter SHALL đánh giá bài đó dựa trên Full_Body theo bộ tiêu chí lọc đã cấu hình và gán kết quả đạt hoặc không đạt trước khi lưu vào NewsArticle.
8. IF một bài không đạt Full_Content_Filter, THEN THE News_Crawler SHALL loại bài đó khỏi bước lưu trữ.

### Requirement 5: Trích xuất toàn văn bằng HTTP tĩnh (Content Extractor)

**User Story:** Là người vận hành, tôi muốn lấy toàn văn thân bài từ trang bài viết tĩnh bằng HTTP fetch nhẹ kết hợp thư viện trích xuất, để có nội dung đầy đủ mà không tốn tài nguyên trình duyệt.

#### Acceptance Criteria

1. WHEN một bài đã được chọn để tải Full_Body và chưa trùng lặp, THE Content_Extractor SHALL tải trang bài viết qua HTTP tĩnh với thời gian chờ tối đa được cấu hình (mặc định 30 giây) và trích xuất Full_Body bằng thư viện trích xuất (trafilatura hoặc readability).
2. WHEN Content_Extractor trích xuất thành công Full_Body, THE News_Crawler SHALL lưu Full_Body vào cột `content` của NewsArticle.
3. WHEN Content_Extractor trích xuất thành công Full_Body, THE News_Crawler SHALL lưu Teaser vào cột `summary` của NewsArticle.
4. IF việc tải trang bài viết trả về mã lỗi HTTP từ 400 trở lên, THEN THE Content_Extractor SHALL ghi nhận bài đó là không trích xuất được kèm mã lỗi HTTP và không ghi đè dữ liệu hiện có của bài.
5. IF việc tải trang bài viết thất bại do vượt quá thời gian chờ tối đa hoặc do lỗi kết nối mạng, THEN THE Content_Extractor SHALL ghi nhận bài đó là không trích xuất được kèm lý do thất bại và không ghi đè dữ liệu hiện có của bài.
6. IF nội dung Full_Body trích xuất được có độ dài (tính bằng số ký tự) nhỏ hơn ngưỡng độ dài tối thiểu được cấu hình, THEN THE News_Crawler SHALL chuyển bài đó sang xử lý bằng Playwright_Fallback.

### Requirement 6: Trích xuất dự phòng bằng Playwright (Conditional Fallback)

**User Story:** Là người vận hành, tôi muốn dùng Playwright làm phương án dự phòng có điều kiện cho nguồn không có RSS hoặc khi HTTP fetch không lấy đủ nội dung, để tối đa khả năng lấy full body mà vẫn kiểm soát tài nguyên.

#### Acceptance Criteria

1. WHERE một nguồn được khai báo loại playwright trong Source_Registry, THE Playwright_Fallback SHALL thực hiện việc lấy nội dung cho nguồn đó.
2. WHEN Content_Extractor trả về Full_Body rỗng hoặc có độ dài nhỏ hơn 500 ký tự cho một bài, THE Playwright_Fallback SHALL thử lấy Full_Body cho bài đó tối đa một lần.
3. THE Playwright_Fallback SHALL xử lý các tác vụ trích xuất theo cơ chế tuần tự, tại mỗi thời điểm chỉ xử lý một bài.
4. THE Playwright_Fallback SHALL dùng tối đa một thực thể trình duyệt tại một thời điểm.
5. THE Playwright_Fallback SHALL vô hiệu hóa việc tải hình ảnh khi lấy nội dung.
6. IF Playwright_Fallback xử lý một bài vượt quá 30 giây, THEN THE Playwright_Fallback SHALL hủy việc xử lý bài đó và ghi nhận bài đó là không trích xuất được kèm lý do hết thời gian chờ.
7. IF sau khi Playwright_Fallback hoàn tất xử lý một bài mà Full_Body thu được vẫn rỗng hoặc có độ dài nhỏ hơn 500 ký tự, THEN THE News_Crawler SHALL ghi nhận bài đó là không trích xuất được kèm lý do nội dung không đủ, không lưu nội dung một phần, và loại bài đó khỏi bước lưu trữ.
8. IF Playwright_Fallback không lấy được Full_Body cho một bài do lỗi xử lý, THEN THE News_Crawler SHALL ghi nhận bài đó là không trích xuất được và loại bài đó khỏi bước lưu trữ.

### Requirement 7: Mở rộng schema và migration (summary + content)

**User Story:** Là lập trình viên, tôi muốn tách teaser và full body thành hai cột riêng trong NewsArticle, để lưu trữ rõ ràng và phục vụ pipeline AI chạy trên full body.

#### Acceptance Criteria

1. THE NewsArticle SHALL cung cấp cột `summary` để lưu Teaser với độ dài tối đa 5.000 ký tự, tách biệt với cột `content` dùng để lưu Full_Body.
2. WHEN migration được áp dụng trên bảng news_articles hiện có chưa có cột `summary`, THE migration SHALL thêm cột `summary` vào bảng đó.
3. WHERE một bản ghi NewsArticle đã tồn tại trước khi migration được áp dụng, THE migration SHALL giữ nguyên giá trị cột `content` của bản ghi đó.
4. THE cột `summary` SHALL cho phép giá trị rỗng (NULL) để tương thích với các bản ghi cũ chưa có Teaser, và các bản ghi tồn tại trước khi migration chạy SHALL mang giá trị `summary` rỗng sau khi migration hoàn tất.
5. IF migration gặp lỗi cơ sở dữ liệu hoặc vi phạm ràng buộc trong quá trình thêm cột `summary`, THEN THE migration SHALL hoàn tác (rollback) toàn bộ thay đổi và giữ nguyên cấu trúc cùng dữ liệu của bảng news_articles như trạng thái trước khi migration chạy.
6. IF migration gặp lỗi trong quá trình thêm cột `summary`, THEN THE migration SHALL phát ra thông báo lỗi chỉ ra nguyên nhân thất bại cho người vận hành.
7. IF cột `summary` đã tồn tại trong bảng news_articles khi migration được áp dụng lại, THEN THE migration SHALL bỏ qua thao tác thêm cột và giữ nguyên dữ liệu hiện có mà không phát sinh lỗi.

### Requirement 8: Báo cáo sức khỏe nguồn và màn Jobs

**User Story:** Là người vận hành, tôi muốn xem trạng thái chi tiết của từng nguồn sau mỗi lần chạy, để phát hiện sớm nguồn hỏng thay vì bị nuốt lỗi âm thầm.

#### Acceptance Criteria

1. WHEN một lần chạy crawl hoàn tất, THE Source_Health_Report SHALL ghi nhận cho mỗi nguồn: Source_Status, số lượng bài lấy được dưới dạng số nguyên không âm, thời gian chạy tính bằng mili-giây, và một thông điệp lỗi không rỗng khi Source_Status khác `ok`.
2. THE Source_Status SHALL nhận một trong các giá trị: `ok`, `empty`, `dead`, `parse_error`, `blocked`.
3. WHEN một nguồn xử lý thành công và lấy được ít nhất một bài, THE Source_Health_Report SHALL gán Source_Status `ok` cho nguồn đó.
4. WHEN một nguồn được truy cập thành công nhưng không lấy được bài nào, THE Source_Health_Report SHALL gán Source_Status `empty` cho nguồn đó.
5. IF một nguồn không phản hồi trong vòng 30 giây hoặc không thể kết nối được, THEN THE Source_Health_Report SHALL gán Source_Status `dead` cho nguồn đó.
6. IF một nguồn trả về phản hồi nhưng không trích xuất được nội dung, THEN THE Source_Health_Report SHALL gán Source_Status `parse_error` cho nguồn đó.
7. IF một nguồn trả về phản hồi cho biết truy cập bị từ chối hoặc bị chặn, THEN THE Source_Health_Report SHALL gán Source_Status `blocked` cho nguồn đó.
8. THE News_Crawler SHALL cung cấp Source_Health_Report cho Jobs_View để hiển thị trạng thái từng nguồn.
9. WHEN một hoặc nhiều nguồn có Source_Status khác `ok`, THE News_Crawler SHALL phản ánh các trạng thái nguồn này trong kết quả trả về của tiến trình crawl thay vì báo thành công chung chung.

### Requirement 9: Ràng buộc tài nguyên và kiểm soát song song

**User Story:** Là người vận hành trên server 2 CPU / 2 GB RAM, tôi muốn hệ thống giới hạn mức độ song song và hạn chế dùng Playwright, để tránh cạn kiệt bộ nhớ (OOM).

#### Acceptance Criteria

1. THE News_Crawler SHALL giới hạn số tác vụ tải Full_Body chạy song song không vượt quá Fetch_Concurrency_Limit.
2. THE Fetch_Concurrency_Limit SHALL là tham số cấu hình kiểu số nguyên có giá trị mặc định 4, trong khoảng từ 1 đến 10.
3. WHEN số tác vụ tải Full_Body sẵn sàng vượt quá Fetch_Concurrency_Limit, THE News_Crawler SHALL xếp hàng các tác vụ vượt giới hạn và khởi chạy chúng khi có vị trí xử lý trống.
4. THE Playwright_Fallback SHALL không chạy nhiều hơn một thực thể trình duyệt đồng thời.
5. WHILE Playwright_Fallback đang xử lý các tác vụ, THE News_Crawler SHALL xử lý các tác vụ Playwright theo cơ chế tuần tự.
6. WHEN Playwright_Fallback hoàn tất xử lý toàn bộ tác vụ của một lần chạy, THE Playwright_Fallback SHALL đóng thực thể trình duyệt để giải phóng bộ nhớ.

### Requirement 10: Không nuốt lỗi và khả năng quan sát (Observability)

**User Story:** Là người vận hành, tôi muốn mọi lỗi nguồn đều hiển thị rõ ràng và log gắn Trace_Id, để chẩn đoán nhanh khi crawl không trả về dữ liệu.

#### Acceptance Criteria

1. IF một nguồn gặp lỗi trong quá trình xử lý, THEN THE News_Crawler SHALL ghi nhận lỗi đó vào Source_Health_Report kèm thông điệp lỗi không rỗng chứa định danh nguồn và mô tả nguyên nhân lỗi.
2. WHEN News_Crawler ghi log cho một lần chạy crawl, THE News_Crawler SHALL gắn vào mỗi mục log một Trace_Id không rỗng mang cùng một giá trị cho toàn bộ lần chạy đó.
3. IF toàn bộ nguồn đều có Source_Status khác `ok`, THEN THE News_Crawler SHALL đánh dấu kết quả của tiến trình crawl là thất bại toàn phần kèm danh sách Source_Status của các nguồn.
4. THE News_Crawler SHALL truyền cùng một Trace_Id của lần chạy crawl sang các tác vụ tải full body chạy song song của lần chạy đó.
5. IF một nguồn gặp lỗi trong quá trình xử lý, THEN THE News_Crawler SHALL gán Source_Status cho nguồn lỗi đó và tiếp tục xử lý đến hết các nguồn còn lại.

### Requirement 11: Lịch sự với máy chủ nguồn (Politeness)

**User Story:** Là người vận hành có trách nhiệm, tôi muốn hệ thống truy cập các site nguồn một cách lịch sự, để giảm rủi ro bị chặn và tránh gây tải bất thường cho nguồn.

#### Acceptance Criteria

1. WHEN Content_Extractor hoặc Playwright_Fallback gửi yêu cầu tới một site nguồn, THE News_Crawler SHALL đính kèm chuỗi User-Agent được cấu hình vào tiêu đề yêu cầu.
2. IF chuỗi User-Agent chưa được cấu hình khi gửi yêu cầu tới một site nguồn, THEN THE News_Crawler SHALL sử dụng chuỗi User-Agent mặc định của hệ thống cho yêu cầu đó.
3. THE News_Crawler SHALL giới hạn tần suất yêu cầu tới cùng một site nguồn không vượt quá ngưỡng rate limit được cấu hình, tính bằng số yêu cầu mỗi giây trên mỗi site (mặc định 1 yêu cầu/giây, trong khoảng từ 0.1 đến 10 yêu cầu/giây).
4. WHEN tần suất yêu cầu tới cùng một site nguồn đạt ngưỡng rate limit được cấu hình, THE News_Crawler SHALL trì hoãn các yêu cầu tiếp theo tới site đó cho đến khi tần suất trở lại trong ngưỡng.
5. IF một yêu cầu tới site nguồn vượt quá thời gian chờ được cấu hình (mặc định 30 giây, trong khoảng từ 5 đến 120 giây), THEN THE News_Crawler SHALL hủy yêu cầu đó, ghi nhận bài liên quan là không trích xuất được, và ghi nhận chỉ báo lỗi cho biết nguyên nhân là hết thời gian chờ.

### Requirement 12: Lưu trữ idempotent (Upsert)

**User Story:** Là lập trình viên, tôi muốn việc lưu bài viết là idempotent theo `url`, để chạy lại crawl không tạo bản ghi trùng.

#### Acceptance Criteria

1. WHEN News_Crawler lưu một tập bài viết vào NewsArticle, THE News_Crawler SHALL dùng `url` làm khóa định danh để chống trùng, so khớp `url` theo chuỗi nguyên văn, phân biệt chữ hoa chữ thường và không áp dụng chuẩn hóa.
2. IF một bài viết có `url` đã tồn tại trong NewsArticle, THEN THE News_Crawler SHALL không tạo thêm bản ghi mới và không ghi đè bản ghi hiện có cho `url` đó.
3. WHEN News_Crawler nhận một tập bài viết chứa nhiều bài có cùng `url`, THE News_Crawler SHALL chỉ lưu bài xuất hiện đầu tiên theo thứ tự nhận được cho `url` đó và bỏ qua các bài trùng còn lại.
4. IF một bài viết có `url` rỗng hoặc thiếu, THEN THE News_Crawler SHALL bỏ qua bài đó và không lưu vào NewsArticle.
5. IF việc lưu một bài viết vào NewsArticle thất bại, THEN THE News_Crawler SHALL giữ nguyên trạng thái dữ liệu hiện có và tiếp tục lưu các bài còn lại.

### Requirement 13: Tương thích scheduler và pipeline AI hiện có

**User Story:** Là người vận hành, tôi muốn tính năng mới hoạt động liền mạch với scheduler và pipeline AI hiện có, để không phá vỡ các luồng đang chạy.

#### Acceptance Criteria

1. WHEN Scheduler kích hoạt tiến trình crawl theo CrawlerConfig, THE News_Crawler SHALL thực thi luồng thu thập full body mới và CHỈ thu thập từ các nguồn có trong `active_sources`, bỏ qua mọi nguồn không nằm trong `active_sources`.
2. IF News_Crawler không thể đọc hoặc áp dụng cấu hình `active_sources`, THEN THE News_Crawler SHALL dừng tiến trình crawl mà không thực hiện thu thập từ bất kỳ nguồn nào, ghi nhận một bản ghi lỗi nêu lý do dừng, và giữ nguyên trạng thái dữ liệu hiện có (không tạo hoặc sửa bài viết trong lần chạy bị dừng).
3. WHEN News_Crawler lưu một bài viết mới có Full_Body, THE News_Crawler SHALL gán trạng thái khởi tạo "đang chờ xử lý" (pending) để AI_Pipeline nhận diện bài đó là chưa được phân tích.
4. WHEN AI_Pipeline xử lý một bài viết ở trạng thái "đang chờ xử lý" có Full_Body, THE AI_Pipeline SHALL chạy phân tích trên giá trị cột `content` chứa Full_Body của bài viết đó.
5. IF AI_Pipeline xử lý một bài viết mà giá trị cột `content` rỗng hoặc null, THEN THE AI_Pipeline SHALL bỏ qua bước phân tích cho bài viết đó, gán trạng thái biểu thị không thể xử lý do thiếu nội dung, và không làm dừng việc xử lý các bài viết còn lại trong hàng chờ.
6. WHEN client gọi endpoint `POST /api/v1/news/ingest`, THE News_Crawler SHALL giữ nguyên toàn bộ trường phản hồi hiện có (không xóa, không đổi tên, không đổi kiểu dữ liệu của các trường mà client hiện tại đang dùng) và CHỈ bổ sung thông tin Source_Health_Report dưới dạng trường mới trong phản hồi.
