## Outcome
Ứng dụng QuantiFin AI Agent: trợ lý tài chính đa tác nhân (Multi-Agent RAG) phân tích báo cáo tài chính doanh nghiệp, tin tức, chế tài/pháp lý, bối cảnh kinh tế vĩ mô/vi mô và dự đoán xu hướng cổ phiếu.

## Vấn đề & Người dùng
- Nhà đầu tư cá nhân thiếu thời gian tổng hợp dữ liệu phân tán, khó đánh giá rủi ro và xu hướng.
- Đối tượng: nhà đầu tư cá nhân, nhà phân tích, quỹ nhỏ.

## Giải pháp (ngắn gọn)
- Hệ RAG đa tác nhân với LangGraph/Google ADK: tìm kiếm, truy xuất, phân tích, tổng hợp và dự đoán có kiểm soát.
- Dẫn chứng nguồn, truy xuất tài liệu và lý giải quyết định (explainable output).

## Phạm vi MVP
- Câu hỏi tự nhiên → trả lời có dẫn nguồn từ: báo cáo tài chính PDF/HTML và tin tức đã index.
- Chỉ số cơ bản: trích xuất số liệu, tính P/E, ROE/ROA, nợ, tăng trưởng YoY/QoQ.
- Tìm kiếm ngữ nghĩa trên `pgvector`, top-k retrieval, tổng hợp câu trả lời có trích dẫn.
- Đăng nhập , RBAC cơ bản: Admin, User.

### Ngoài phạm vi (về sau)
- Dự đoán nâng cao theo thời gian thực, tích hợp dữ liệu thị trường thời gian thực, tối ưu chi phí inference nâng cao.

## Kiến trúc & Công nghệ
- Python, LangGraph/Google ADK, FastAPI.
- AI Agent: setup 2 luồng (Google ADK, LangChain/LangGraph), 1 luồng sử dụng Google ADK, luồng còn lại sử dụng Langchain/LangGraph.
- PostgreSQL (structured), `pgvector` (unstructured embeddings), Redis (session/cache/memory ngắn hạn).
- Docker, GitHub Actions (CI/CD).
- Nguyên tắc: Clean Architecture, Domain Driven Design, Test-Driven Development, SOLID, Clean Code.

## Dữ liệu & Knowledge Base
- Nguồn: báo cáo tài chính doanh nghiệp, tin tức/bài viết, văn bản pháp lý; sau bổ sung web search/API.
- Quy trình: chuẩn hóa → chunk → embedding → lưu `pgvector` (metadata: nguồn, ngày, loại tài liệu, doanh nghiệp, ticker).

## Bảo mật, Xác thực, Phân quyền
- OAuth2/OIDC, JWT, RBAC: Admin, User (người dùng, nhà phân tích, nhà đầu tư).

## Tác nhân (ngắn gọn)
- Guard Agent: kiểm tra input/output, chống injection, áp chính sách.
- Embedding Agent: tạo embedding từ tài liệu đã chuẩn hóa, lưu `pgvector`.
- Search Agent: tìm ngoài (tùy giai đoạn) và lập chỉ mục query.
- Retriever Agent: truy vấn PostgreSQL/`pgvector`, lọc/sắp xếp kết quả.
- Analyze Agent: trích xuất số liệu, tính chỉ số, tóm tắt, cảm xúc.
- Aggregator Agent: điều phối, hợp nhất kết quả, tạo câu trả lời cuối cùng có trích dẫn.
- Predict Agent: mô hình chuỗi thời gian/cơ bản (MVP có thể trì hoãn).

## Testing
- Pytest: unit, integration (retrieval, parsing), e2e tối thiểu.
- Fixtures cho tài liệu mẫu; coverage các đường đi chính.

## Lộ trình
- Sprint 1 (MVP Core): cấu trúc dự án, FastAPI health, kết nối Postgres + `pgvector`, Redis; Embedding & Retriever cơ bản; Analyze trích xuất chỉ số; Aggregator trả lời có trích dẫn.
- Sprint 2: nhập liệu tài liệu thật (5–10 doanh nghiệp), cải thiện chunking/metadata, tối ưu truy vấn.
- Sprint 3: RBAC cho API
- Sprint 4: bổ sung Predict Agent cơ bản (ARIMA/LSTM) và đánh giá.

## Thước đo thành công (Success Metrics)
- Độ chính xác truy xuất (Recall@K), tỷ lệ câu trả lời có trích dẫn hợp lệ.
- Thời gian phản hồi P50/P95; chi phí mỗi truy vấn.
- Điểm hài lòng người dùng (CSAT) cho 20 câu hỏi chuẩn hóa.

## Tech Stack (tham chiếu)
- Python, LangGraph/Google ADK, FastAPI
- LLM/Embedding: OpenAI, Anthropic, Gemini, DeepSeek...
- PostgreSQL, `pgvector`, Redis
- Docker, GitHub Actions

## Ghi chú triển khai tối thiểu
- Lưu trữ metadata đầy đủ để trace nguồn.
- Chuẩn hóa kiểu dữ liệu số và thời gian trước khi tính toán.
- Tách rõ tầng connector (client) và logic thuần hàm.

## Checklist triển khai (rút gọn)
- [ ] Khởi tạo cấu trúc Clean Architecture + FastAPI health
- [ ] Thiết lập Postgres + `pgvector` + Redis
- [ ] Pipeline nhập liệu: chuẩn hóa → chunk → embedding → lưu
- [ ] Retriever + Aggregator trả lời có trích dẫn
- [ ] Analyze tính chỉ số cơ bản (P/E, ROE/ROA, nợ, tăng trưởng)
- [ ] Guardrails tối thiểu (chặn injection, lọc PII cơ bản)
- [ ] Tests: unit/integration/e2e tối thiểu
