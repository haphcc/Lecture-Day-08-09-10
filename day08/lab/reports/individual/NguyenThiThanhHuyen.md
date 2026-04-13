# Báo Cáo Cá Nhân — Lab Day 08: RAG Pipeline

**Họ và tên:** Nguyễn Thị Thanh Huyền  
**Vai trò trong nhóm:** Tech Lead 
**Ngày nộp:** 13/04/2026  
**Độ dài yêu cầu:** 500–800 từ

---

## 1. Tôi đã làm gì trong lab này? (100-150 từ)

Với vai trò **Tech Lead**, mình chịu trách nhiệm chính trong việc xây dựng khung xương (foundation) cho toàn bộ pipeline tại **Sprint 2 và Sprint 3**. Cụ thể, mình đã trực tiếp implement cơ chế kết nối và quản lý collection trên **ChromaDB**, đảm bảo việc chuyển đổi dữ liệu từ văn bản thô sang các vector embedding thông qua thư viện `sentence-transformers` diễn ra trơn tru. Mình cũng là người thiết lập hàm `call_llm` sử dụng Google Gemini, đồng thời xây dựng cấu trúc **Grounded Prompt** để ép mô hình phải trích dẫn nguồn (citation) và từ chối trả lời (abstain) khi thiếu dữ liệu. Công việc của mình là "điểm nối" quan trọng: nhận dữ liệu đã được Retrieval Owner tối ưu hóa metadata để đưa vào prompt cho LLM xử lý, tạo tiền đề cho Eval Owner thực hiện chấm điểm ở Sprint 4.

---

## 2. Điều tôi hiểu rõ hơn sau lab này (100-150 từ)

Concept mà mình cảm thấy tâm đắc nhất chính là **Grounded Generation và cơ chế Citations**. Trước đây mình nghĩ chỉ cần đưa đủ context là AI sẽ trả lời đúng, nhưng thực tế qua Lab này, mình thấy dù có context, LLM vẫn có xu hướng tự "sáng tạo" thêm thông tin theo thói quen. Việc đưa ra các quy tắc nghiêm ngặt trong **System Prompt** (như rule: Evidence-only và No-hallucination) kết hợp với việc đánh số thứ tự `[1]`, `[2]` cho từng đoạn văn bản trích xuất là chìa khóa để xây dựng một trợ lý AI đáng tin cậy. Mình hiểu rằng metadata không chỉ để lọc dữ liệu mà còn là "chứng minh thư" để người dùng kiểm chứng tính xác thực của câu trả lời.

---

## 3. Điều tôi ngạc nhiên hoặc gặp khó khăn (100-150 từ)

Khó khăn lớn nhất và gây mất thời gian nhất chính là **các lỗi về Encoding và cấu hình API trên môi trường Windows**. Mình đã gặp lỗi `UnicodeDecodeError` ngay khi cài đặt thư viện do file `requirements.txt` có chứa các ký tự đặc biệt tiếng Việt. Tiếp đó là lỗi **404 Model Not Found** khi gọi Gemini 1.5 Flash. Qua đó, mình rút ra bài học rằng môi trường thực thi (OS, SDK version) ảnh hưởng rất lớn đến pipeline. Ban đầu mình giả định chỉ cần copy API key là chạy được, nhưng thực tế phải debug sâu vào logic gọi model và cấu hình biến môi trường `.env`. Điều này rèn luyện cho mình kỹ năng quản lý cấu hình (configuration management) cực kỳ cẩn thận cho các dự án AI sau này.

---

## 4. Phân tích một câu hỏi trong scorecard (150-200 từ)

**Câu hỏi:** "Khách hàng có thể yêu cầu hoàn tiền trong bao nhiêu ngày?"

**Phân tích:** 
Đây là một câu hỏi dạng trích xuất thông tin trực tiếp và hệ thống **Baseline (Dense Retrieval)** của nhóm mình đã xử lý rất tốt. 
- **Retrieval:** Thuật toán Dense search đã tìm đúng đoạn văn trong file `policy/refund-v4.pdf` (Điều 2: Điều kiện được hoàn tiền) với điểm cosine similarity là **0.676** (đứng top 1 ưu tiên).
- **Generation:** Do context lấy về rất chính xác ("Yêu cầu được gửi trong vòng 7 ngày làm việc kể từ thời điểm xác nhận đơn hàng"), mô hình Gemini đã trả lời ngắn gọn là "7 ngày làm việc" và gắn citation `[1]` chuẩn xác. 
- **Kết luận:** Với các câu hỏi có từ khóa rõ ràng và xuất hiện trực tiếp trong văn bản, cơ chế Dense Retrieval đơn giản là đủ hiệu quả. Tuy nhiên, nếu câu hỏi phức tạp hơn liên quan đến mã lỗi (ví dụ `ERR-403`), có lẽ chúng ta sẽ cần Hybrid Retrieval để cải thiện điểm số.

---

## 5. Nếu có thêm thời gian, tôi sẽ làm gì? (50-100 từ)

Mình muốn triển khai thêm **Hybrid Retrieval (Dense + BM25)**. Qua kết quả scorecard, mình nhận thấy khi người dùng hỏi về các mã lỗi kỹ thuật cụ thể, search theo vector embedding đôi khi bị "loãng" do mô hình tập trung vào ngữ nghĩa thay vì ký tự chính xác. Nếu kết hợp được BM25 để bắt các từ khóa cứng như "ERR-403" hoặc "P1", độ chính xác (Precision) của hệ thống sẽ đạt mức tuyệt đối hơn, giảm thiểu áp lực lọc noise cho mô hình Rerank ở phía sau.
---