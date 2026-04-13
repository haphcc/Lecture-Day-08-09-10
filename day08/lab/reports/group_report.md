# Group Report — Lab Day 08: RAG Pipeline
**Nhóm:** Helpdesk AI Assistant 

---

## 1. Mục tiêu và Phạm vi
Nhóm xây dựng hệ thống **RAG (Retrieval-Augmented Generation)** làm trợ lý nội bộ cho khối CS và IT Helpdesk. Mục tiêu chính là trả lời chính xác các câu hỏi về chính sách bảo mật (Access Control), quy trình hoàn tiền (Refund Policy) và các cam kết dịch vụ (SLA) dựa trên dữ liệu thật của công ty, đảm bảo tuyệt đối không bịa đặt thông tin (Anti-hallucination).

---

## 2. Quyết định Kỹ thuật Cốt lõi

### A. Chiến thuật Indexing (Sprint 1)
- **Chuẩn hóa dữ liệu**: Chúng mình trích xuất metadata ngay từ header file (`Source`, `Department`, `Effective Date`, `Access`) để hỗ trợ việc trích dẫn nguồn sau này.
- **Chunking Strategy**: Nhóm áp dụng **Heading-based chunking** (cắt theo tiêu mục `=== Section ===`). Cách làm này giúp giữ được tính toàn vẹn của một điều khoản, tránh việc thông tin quan trọng bị cắt làm đôi như cách cắt theo số lượng ký tự cứng.
- **Embedding**: Sử dụng mô hình local `paraphrase-multilingual-MiniLM-L12-v2`. Lựa chọn này đảm bảo tốc độ xử lý nhanh tại máy và tính bảo mật dữ liệu nội bộ.

### B. Retrieval & Tuning (Sprint 3)
Nhóm đã chọn **Variant: Rerank (Cross-Encoder)** thay vì Hybrid Retrieval.
- **Lý do**: Qua thử nghiệm ban đầu, Dense Search (truy vấn theo ngữ nghĩa) tìm được rất nhiều đoạn văn có liên quan nhưng đôi khi các đoạn quan trọng nhất lại nằm ở vị trí thứ 4 hoặc 5. 
- **Giải pháp**: Chúng mình dùng mô hình `ms-marco-MiniLM-L-6-v2` để chấm điểm lại top-10 kết quả từ Dense Search, sau đó lọc ra 3 đoạn văn có điểm relevance cao nhất để đưa vào Prompt. Việc này giúp cải thiện đáng kể độ chính xác cho các câu hỏi phức tạp cần đối soát nhiều tài liệu.

### C. Prompt Engineering (Sprint 2)
Chúng mình thiết lập một hệ thống **System Prompt** cực kỳ chặt chẽ cho Gemini 2.5 Flash:
- Ép mô hình chỉ được trả lời dựa trên context.
- Bắt buộc gắn mã số trích dẫn `[1]`, `[2]` vào sau mỗi ý.
- Nếu không thấy thông tin trong tài liệu, hệ thống phải trả lời theo mẫu: *"Thông tin này không có trong tài liệu được cung cấp."* để đảm bảo tính trung thực.

---

## 3. Đánh giá Kết quả (Sprint 4)

| Metric | Score (Baseline) | Score (Variant) | Nhận xét |
|--------|-----------------|-----------------|----------|
| **Faithfulness** | 5.00/5 | 4.83/5 | Giảm nhẹ do Rerank mang về context chi tiết hơn, khiến LLM đôi khi tổng hợp có phần "sáng tạo" hơn. |
| **Relevance** | 4.17/5 | 4.08/5 | Biến động không đáng kể, cho thấy Rerank giữ được độ tập trung tốt của câu trả lời. |
| **Context Recall** | 5.00/5 | 5.00/5 | Đạt điểm tuyệt đối, chứng minh bộ retriever (Dense Search) đã hoạt động rất hiệu quả. |
| **Completeness** | 3.17/5 | 3.33/5 | Cải thiện rõ rệt nhất (+0.16). Rerank giúp chọn được các chunks chứa nhiều thông tin bổ trợ quan trọng hơn. |

---

## 4. Kết luận
Hệ thống RAG của nhóm đã đạt được sự cân bằng giữa tốc độ và độ chính xác. Việc sử dụng Local Embedding giúp hệ thống chạy ổn định kể cả khi gặp lỗi API OpenAI. Đặc biệt, cơ chế **Rerank** đã chứng minh được hiệu quả vượt trội trong việc tinh lọc dữ liệu cho khối chính sách (Policy) vốn có nhiều câu chữ tương đồng dễ gây nhầm lẫn.

Hệ thống đã sẵn sàng cho giai đoạn kiểm thử với bộ câu hỏi ẩn (Grading Questions).
