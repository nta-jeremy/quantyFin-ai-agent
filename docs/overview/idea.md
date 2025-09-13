## Outcome: 
Ứng dụng QuantiFin AI Agent
Tôi muốn xây dựng app về AI Agentic RAG (hoặc Multi Agent RAG) về phân tích báo cáo tài chính doanh nghiệp kết hợp với phân tích các tin tức báo chí truyền thông, chế tài, pháp lý, kinh tế của đất nước và thế giới để và dự đoán xu hướng cổ phiếu trong tương lai. Tóm gọn lại là một chuyên gia tài chính với nhiều năm kinh nghiệm về cả vỹ mô lẫn vy mô.

## Tech stack:
- Python: programming language
- LangGraph: framework for AI Agentic RAG
- FastAPI: restful api
- LLM: OpenAI, Anthropic, Gemini, DeepSeek, etc.
- Embedding: OpenAI, HuggingFace, etc.
- PostgresDB: Database for structured data
- Postgres Vector Database: Vector Database for unstructured data
- Redis: Cache session
- Docker: Container
- Github: Repository and CI/CD pipeline

### System Architecture:
- Hexagonal Architecture
- Test Driven Development (TDD)
- Solid Principles
- Clean Code

### Testing: 
Test Driven Development (TDD): Unit Test, Integration Test, End to End Test...
- Pytest
- Mock
- Fixture
- Coverage
- etc.

### Authentication:
- Keycloak: SSO
- JWT: JSON Web Token
- OAuth2: Open Authorization 2.0

### Authorization:
- Keycloak: RBAC


### LLM: có thể sử dụng các API của OpenAI, Anthropic, Gemini, DeepSeek, etc.
- Gemini
- OpenAI
- Anthropic
- DeepSeek

### Knowledge base: 
- Sử dụng
- Kiến thức có thể từ Web search, database, documents (html, markdown, text, pdf, etc.), API...
- các tài liệu về báo cáo tài chính doanh nghiệp, tin tức báo chí truyền thông, chế tài, pháp lý, kinh tế của đất nước và thế giới etc. để tạo ra các vector embedding. Các tài liệu này sẽ được lưu trữ trong vector database.

### Memory:
- Áp dụng short term memory: Redis
- Áp dụng long term memory: Postgres Vector Database

### Session
- Redis: Session

### Cache:
- Redis: Cache

### Container:
- Docker: Container

## Agents:

### Guard Agent:
- Lớp bảo vệ cho ứng dụng và các agent khác không bị tấn công bởi các vấn đề như:
    - Chống lại prompt injection
- Nhiệm vụ kiểm tra user input

### Embedding Agent:
- Cho phép tạo các vector embedding cho các tài liệu về báo cáo tài chính doanh nghiệp, tin tức báo chí truyền thông, chế tài, pháp lý, kinh tế của đất nước và thế giới etc.
    - Tạo các vector embedding cho các thông tin về cổ phiếu
    - Tạo các vector embedding cho các thông tin về doanh nghiệp
    - Tạo các vector embedding cho các thông tin về ngành nghề
    - Tạo các vector embedding cho các thông tin về quốc gia
    - Tạo các vector embedding cho các thông tin về thị trường
    - Tạo các vector embedding cho các thông tin về ngành nghề

- Lưu trữ các vector embedding vào vector database (Postgres Vector Database).

### Aggregator Agent:

**Aggregator Agent** đóng vai trò là "người điều phối" hoặc "tổng hợp viên" cuối cùng, đảm bảo toàn bộ quá trình diễn ra hiệu quả.

Dưới đây là các vai trò cốt lõi của một Aggregator Agent:
#### 1. Điều phối và Quản lý Luồng
Aggregator Agent chịu trách nhiệm điều phối luồng xử lý giữa các Agent khác. Nó hoạt động như một trung tâm điều khiển, quyết định Agent nào nên được kích hoạt tiếp theo dựa trên trạng thái hiện tại của biểu đồ. Vai trò này bao gồm:
- **Định tuyến:** Dựa trên đầu vào của người dùng, Aggregator Agent có thể quyết định Agent nào sẽ xử lý tác vụ, ví dụ: Agent tìm kiếm tài liệu, Agent phân tích dữ liệu, hoặc Agent tạo câu trả lời.
- **Quản lý trạng thái:** Aggregator Agent theo dõi và cập nhật trạng thái của toàn bộ quá trình, đảm bảo các Agent hoạt động theo đúng trình tự.

#### 2. Tổng hợp Thông tin
Đây là vai trò quan trọng nhất của Aggregator Agent. Sau khi các Agent khác đã hoàn thành công việc của mình (ví dụ: **Retrieval Agent** đã tìm thấy tài liệu liên quan, **Analytics Agent** đã phân tích dữ liệu), Aggregator Agent sẽ thu thập tất cả các kết quả này. Nó có nhiệm vụ:
- **Tích hợp:** Kết hợp các đoạn văn bản, bảng biểu hoặc các kết quả đầu ra khác nhau từ nhiều nguồn.
- **Sắp xếp:** Loại bỏ các thông tin trùng lặp, mâu thuẫn hoặc không liên quan.

#### 3. Tạo ra câu trả lời cuối cùng
Dựa trên thông tin đã được tổng hợp, Aggregator Agent tạo ra câu trả lời cuối cùng, thân thiện với người dùng và chính xác. Vai trò này bao gồm:
- **Tạo văn bản tự nhiên:** Sử dụng mô hình ngôn ngữ lớn (LLM) để chuyển đổi thông tin tổng hợp thành một câu trả lời mạch lạc và dễ hiểu.
- **Kiểm tra và xác thực:** Đảm bảo câu trả lời cuối cùng đáp ứng các yêu cầu về chất lượng và không chứa thông tin sai lệch.

#### 4. Xử lý Lỗi và Hồi quy
Trong một hệ thống phức tạp, lỗi có thể xảy ra. Aggregator Agent có thể được thiết kế để:
- **Xử lý ngoại lệ:** Phát hiện các trường hợp lỗi (ví dụ: một Agent không tìm thấy thông tin cần thiết) và đưa ra giải pháp thay thế.
- **Hồi quy (fallback):** Nếu một tác vụ không thể hoàn thành, Aggregator Agent có thể chuyển hướng đến một quy trình dự phòng hoặc thông báo cho người dùng.

Kết luận: **Aggregator Agent** là "bộ não" của hệ thống **RAG Agentic**. Nó không chỉ thực hiện một tác vụ cụ thể mà còn đảm bảo toàn bộ quá trình được điều phối một cách hiệu quả, tổng hợp thông tin từ nhiều nguồn và tạo ra kết quả cuối cùng chất lượng cao.

### Search Agent:
**Search Agent** (tạm dịch là Tác nhân Tìm kiếm) đóng vai trò chính là chuyên gia tìm kiếm và truy xuất thông tin.

#### 1. Phân tích và Hiểu truy vấn
Vai trò đầu tiên của Search Agent là phân tích và hiểu rõ truy vấn từ người dùng. Nó không chỉ nhận một câu hỏi mà còn cần xác định các từ khóa, các khái niệm chính và mục đích thực sự của người dùng. Sau đó, nó có thể biến đổi câu hỏi phức tạp thành một hoặc nhiều truy vấn tìm kiếm hiệu quả hơn, phù hợp với hệ thống bên ngoài. Ví dụ, nếu người dùng hỏi "Điểm khác biệt giữa LLM và RAG là gì?", Search Agent sẽ hiểu rằng nó cần tìm kiếm thông tin về "định nghĩa LLM", "định nghĩa RAG", và "so sánh".


#### 2. Tìm kiếm và Truy xuất thông tin
Đây là vai trò cốt lõi. Sau khi phân tích truy vấn, Search Agent sẽ:
* **Truy vấn nguồn bên ngoài:** Gửi yêu cầu tìm kiếm đến một hoặc nhiều nguồn thông tin bên ngoài. Nguồn này có thể là cơ sở dữ liệu vector, công cụ tìm kiếm trên web, hoặc thậm chí là các API cụ thể.
* **Truy xuất thông tin liên quan:** Từ kết quả tìm kiếm, Search Agent sẽ chọn lọc và lấy ra các đoạn văn bản, tài liệu, hoặc dữ liệu phù hợp nhất với truy vấn ban đầu.


#### 3. Xử lý và Tiền xử lý dữ liệu
Sau khi truy xuất thông tin, Search Agent sẽ xử lý dữ liệu để chuẩn bị cho các bước tiếp theo trong luồng **LangGraph**.
* **Tiền xử lý:** Xóa các thông tin không cần thiết, chuẩn hóa định dạng văn bản.
* **Tóm tắt:** Có thể tạo ra một bản tóm tắt ngắn gọn của các tài liệu tìm thấy để giảm lượng thông tin cần xử lý ở các bước sau.
* **Gán nhãn:** Đánh dấu các thông tin quan trọng để các Agent khác (như **Aggregator Agent**) dễ dàng nhận biết và sử dụng.

Tóm lại, **Search Agent** là người chuyên trách việc đi "săn" thông tin, đảm bảo rằng hệ thống RAG Agentic có đủ các mảnh ghép dữ liệu cần thiết từ nguồn bên ngoài để tạo ra một câu trả lời chính xác, đầy đủ và đáng tin cậy.

### Retriever Agent:
Với yêu cầu trên, tôi sẽ phân tích và trình bày chi tiết các vai trò cốt lõi của một **Retriever Agent** (Tác nhân Truy vấn) trong hệ thống AI Agentic sử dụng LangGraph.

### Vai trò cốt lõi của Retriever Agent

**Retriever Agent** đóng vai trò là "chuyên gia" về truy vấn và tìm kiếm dữ liệu. Nó không chỉ đơn thuần là một công cụ tìm kiếm, mà còn là một tác nhân thông minh, có khả năng hiểu và biến đổi truy vấn của người dùng để tương tác hiệu quả với các cơ sở dữ liệu.


#### 1. Phân tích và Xử lý truy vấn
Vai trò đầu tiên và quan trọng nhất là phân tích truy vấn từ các agent khác (hoặc trực tiếp từ người dùng). Retriever Agent sẽ:
* **Chuyển đổi truy vấn:** Biến đổi các yêu cầu ngôn ngữ tự nhiên thành các truy vấn có cấu trúc phù hợp với cơ sở dữ liệu. Ví dụ, chuyển "dữ liệu tài chính gần nhất của FPT" thành một truy vấn SQL hoặc vector search.
* **Tạo truy vấn nhúng (embedding):** Nếu sử dụng cơ sở dữ liệu vector, Retriever Agent sẽ sử dụng một mô hình ngôn ngữ lớn (LLM) để tạo ra các vector nhúng (embedding vectors) từ truy vấn ban đầu. Điều này cho phép tìm kiếm ngữ nghĩa thay vì tìm kiếm từ khóa.


#### 2. Tương tác với cơ sở dữ liệu
Đây là vai trò kỹ thuật chính của Retriever Agent. Nó có trách nhiệm kết nối và tương tác với các cơ sở dữ liệu được chỉ định.
* **Truy vấn PostgreSQL:** Nếu yêu cầu là tìm kiếm dữ liệu có cấu trúc (ví dụ: ngày, số liệu cụ thể), Retriever Agent sẽ tạo và thực thi các câu lệnh SQL để truy xuất thông tin từ cơ sở dữ liệu PostgreSQL.
* **Truy vấn Vector Database:** Đối với các truy vấn ngữ nghĩa, Retriever Agent sẽ gửi vector nhúng đã tạo đến cơ sở dữ liệu vector (ví dụ: `pgvector`). Cơ sở dữ liệu sẽ tìm kiếm các vector có độ tương đồng cao nhất (sử dụng các thuật toán như k-nearest neighbors - KNN) và trả về các đoạn văn bản hoặc tài liệu liên quan.


#### 3. Lựa chọn và Lọc dữ liệu
Một khi đã có kết quả từ cơ sở dữ liệu, Retriever Agent không chỉ trả về tất cả mà còn:
* **Lọc nhiễu:** Loại bỏ các dữ liệu không liên quan hoặc trùng lặp.
* **Sắp xếp kết quả:** Sắp xếp các tài liệu tìm thấy theo mức độ phù hợp.
* **Lựa chọn tối ưu:** Chọn một số lượng tài liệu phù hợp nhất để chuyển tiếp cho các agent khác (ví dụ: `Analyze Agent` hoặc `Aggregator Agent`). Điều này giúp giảm lượng thông tin cần xử lý và tăng hiệu quả của toàn bộ hệ thống.


#### 4. Xử lý Lỗi và Hồi quy
Retriever Agent cũng cần có khả năng xử lý các tình huống không mong muốn.
* **Không tìm thấy dữ liệu:** Nếu không có kết quả phù hợp, agent có thể thông báo lại cho các agent khác hoặc quay trở lại bước trước để thử một truy vấn khác.
* **Lỗi kết nối:** Xử lý các lỗi kết nối đến cơ sở dữ liệu, đảm bảo rằng hệ thống không bị sập hoàn toàn.

Retriever Agent giống như một thủ thư thông minh, không chỉ biết nơi cất sách mà còn có thể hiểu ý định của người tìm kiếm để mang đến những cuốn sách chính xác nhất.

### Analyze Agent:
Để viết chi tiết vai trò của **Analyze Agent** trong mô hình **RAG Agentic** sử dụng **LangGraph**, chúng ta sẽ tập trung vào chức năng chuyên sâu của nó: phân tích các loại tài liệu phức tạp để trích xuất thông tin hữu ích và có cấu trúc.

---

### Vai trò cốt lõi của Analyze Agent

**Analyze Agent** là một tác nhân chuyên biệt, có nhiệm vụ chính là tiếp nhận các tài liệu thô từ **Search Agent** và **Retriever Agent** sau đó chuyển đổi chúng thành các thông tin có giá trị, dễ hiểu để các tác nhân khác có thể sử dụng. Tùy thuộc vào loại tài liệu, vai trò của nó sẽ được điều chỉnh cho phù hợp.

#### 1. Phân tích Báo cáo Tài chính Doanh nghiệp
- **Trích xuất số liệu:** Trích xuất các số liệu quan trọng như doanh thu, lợi nhuận, dòng tiền, các khoản nợ từ bảng cân đối kế toán, báo cáo kết quả kinh doanh và báo cáo lưu chuyển tiền tệ.
- **Tính toán chỉ số:** Tính toán các chỉ số tài chính cơ bản như P/E (giá trên thu nhập), ROE (lợi nhuận trên vốn chủ sở hữu), ROA (lợi nhuận trên tài sản), và tỷ lệ nợ để đánh giá sức khỏe tài chính của doanh nghiệp.
- **Phân tích xu hướng:** So sánh các số liệu và chỉ số qua các kỳ báo cáo để nhận diện xu hướng tăng trưởng hoặc suy giảm.

#### 2. Phân tích Tin tức, Báo chí và Truyền thông
- **Tóm tắt nội dung:** Tóm tắt các bài báo, tin tức thành các đoạn văn ngắn, trích xuất các ý chính để cung cấp thông tin cốt lõi một cách nhanh chóng.
- **Phân tích cảm xúc:** Đánh giá thái độ (tích cực, tiêu cực, trung lập) của các bài viết về một doanh nghiệp, ngành nghề hoặc thị trường cụ thể.
- **Nhận diện thực thể:** Nhận dạng và trích xuất các thực thể như tên công ty, tên người, địa điểm, sự kiện chính để tạo ra một bản đồ thông tin có cấu trúc.

#### 3. Phân tích Chế tài, Pháp lý và Chính sách
- **Trích dẫn điều khoản:** Phân tích các văn bản pháp lý, quy định để trích xuất các điều khoản, luật lệ liên quan đến một truy vấn cụ thể.
- **Nhận diện tác động:** Đánh giá tác động của các chính sách, quy định pháp lý mới đối với một ngành nghề hoặc một doanh nghiệp. Ví dụ: chính sách thuế mới ảnh hưởng đến lợi nhuận như thế nào?

#### 4. Phân tích Thông tin Cổ phiếu
- **Thu thập dữ liệu:** Phân tích các thông tin cơ bản về cổ phiếu như giá mở/đóng, khối lượng giao dịch, biến động giá trong ngày, tuần, tháng.
- **Phân tích xu hướng:** Nhận diện các mô hình giá (đồ thị hình thành), hỗ trợ và kháng cự để dự đoán xu hướng ngắn và dài hạn của cổ phiếu.

#### 5. Phân tích Ngành nghề và Thị trường
- **Định hình ngành:** Phân tích các tài liệu để xác định các xu hướng chính của một ngành, các yếu tố cạnh tranh và vị thế của các công ty trong ngành.
- **Đánh giá quy mô thị trường:** Thu thập thông tin từ các báo cáo nghiên cứu để ước tính quy mô, tiềm năng tăng trưởng của thị trường.

### Cơ chế hoạt động trong LangGraph
Analyze Agent sẽ là một **node** trong biểu đồ LangGraph. Khi **Search Agent** và **Retriever Agent** tìm thấy các tài liệu thô, **Aggregator Agent** sẽ chuyển các tài liệu này đến **Analyze Agent**. Sau khi phân tích xong, **Analyze Agent** sẽ trả về một phiên bản dữ liệu đã được xử lý, tóm tắt và có cấu trúc hơn. Quá trình này giúp **Aggregator Agent** dễ dàng tổng hợp và tạo ra câu trả lời cuối cùng chính xác và dễ hiểu cho người dùng.

### Predict Agent:
**Predict Agent** đóng vai trò là chuyên gia dự đoán, sử dụng các mô hình học máy và phân tích dữ liệu để dự báo xu hướng tương lai dựa trên thông tin đã được tổng hợp.

---

### Các vai trò cốt lõi

#### 1. Phân tích Dữ liệu Đầu vào
**Predict Agent** tiếp nhận các dữ liệu đã được xử lý và cấu trúc từ các agent khác, đặc biệt là **Analyze Agent**. Nó sẽ xác định các yếu tố quan trọng nhất ảnh hưởng đến dự đoán, bao gồm:
* **Dữ liệu định lượng:** Các chỉ số tài chính, giá cổ phiếu, khối lượng giao dịch.
* **Dữ liệu định tính:** Các thông tin từ tin tức, phân tích cảm xúc, và các yếu tố kinh tế vĩ mô.

#### 2. Xây dựng và Huấn luyện Mô hình Dự đoán
Đây là vai trò kỹ thuật chính của **Predict Agent**. Nó sử dụng các mô hình học máy để phân tích các mẫu và mối quan hệ trong dữ liệu. Các mô hình này có thể bao gồm:
* **Time-series models:** Các mô hình chuỗi thời gian như **ARIMA** hoặc **LSTM** để dự đoán xu hướng giá cổ phiếu.
* **Regression models:** Mô hình hồi quy để dự đoán các chỉ số kinh tế dựa trên các yếu tố đầu vào.

#### 3. Tạo Dự đoán và Kết quả
Sau khi mô hình được huấn luyện, **Predict Agent** sẽ tạo ra các dự đoán cụ thể. Các dự đoán này có thể bao gồm:
* **Dự đoán xu hướng cổ phiếu:** Dự báo giá cổ phiếu trong tương lai gần, xác định các điểm đảo chiều tiềm năng.
* **Dự đoán xu hướng doanh nghiệp:** Dự báo doanh thu, lợi nhuận hoặc các chỉ số tài chính khác của một doanh nghiệp.
* **Dự đoán xu hướng ngành nghề và thị trường:** Phân tích các yếu tố kinh tế để dự báo xu hướng phát triển của một ngành hoặc thị trường.

#### 4. Đánh giá và Tối ưu hóa
**Predict Agent** không chỉ tạo ra dự đoán mà còn đánh giá độ chính xác của chúng. Dựa trên kết quả đánh giá, nó có thể điều chỉnh các tham số của mô hình hoặc lựa chọn các mô hình khác để cải thiện hiệu suất dự đoán. Vai trò này giúp đảm bảo rằng hệ thống luôn hoạt động với độ chính xác cao nhất.


### Backlogs:
- Xây dựng project structure chuẩn cho dự án (Hexagonal Architecture, Test Driven Development (TDD), Solid Principles, Clean Code)
- Xây dựng code base chuẩn cho dự án để kết nối đến langgraph, kết nối database, vector database, keycloak, redis, authentication, authorization, API, etc. để dễ maintain và dễ scale theo các best practices (Hexagonal Architecture, Test Driven Development (TDD), Solid Principles, Clean Code).
- Xây dựng các API (fastAPI) làm mẫu cho dự án cơ bản như health check, hello world, etc.
- Xây dựng luồng log chuẩn cho dự án để track các hoạt động của người dùng và hệ thống
- Xác thực người dùng thông qua SSO (Single Sign-On), JWT, etc.
    - Log in/out, register, forgot password, reset password, get token, refresh token, revoke token, get user info, update user info, delete user, etc...
- Phân quyền: Role based access control (RBAC)
    - System
    - Super Admin
    - Admin
    - User
    - API