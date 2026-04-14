# Báo Cáo Cá Nhân — Lab Day 09: Multi-Agent Orchestration

**Họ và tên:** Nguyễn Thị Thanh Huyền
**Vai trò trong nhóm:** Worker Owner   
**Ngày nộp:** 14/04/2026
**Độ dài yêu cầu:** 500–800 từ

---

> **Lưu ý quan trọng:**
> - Viết ở ngôi **"tôi"**, gắn với chi tiết thật của phần bạn làm
> - Phải có **bằng chứng cụ thể**: tên file, đoạn code, kết quả trace, hoặc commit
> - Nội dung phân tích phải khác hoàn toàn với các thành viên trong nhóm
> - Deadline: Được commit **sau 18:00** (xem SCORING.md)
> - Lưu file với tên: `reports/individual/[ten_ban].md` (VD: `nguyen_van_a.md`)

---

## 1. Tôi phụ trách phần nào? (100–150 từ)

> Trong dự án Lab Day 09, tôi đảm nhận vai trò **Worker Owner**. Trách nhiệm chính của tôi là xây dựng "bộ não" thực thi cho hệ thống thông qua việc triển khai toàn bộ các worker trong thư mục `workers/` và định nghĩa hợp đồng dữ liệu trong `contracts/`.

**Module/file tôi chịu trách nhiệm:**
- File chính: `workers/retrieval.py`, `workers/policy_tool.py`, `workers/synthesis.py`, contracts/worker_contracts.yaml`
- Functions tôi implement: `retrieve_dense(query, top_k)`, `_get_collection()`, `run(state)`, `analyze_policy(task, chunks)`, `_call_llm_for_policy(task, chunks)`, `run(state)`, `synthesize(task, chunks, policy_result)`, `_call_llm(messages)`, `_estimate_confidence(chunks, answer, policy_result)`, `run(state)`

**Cách công việc của tôi kết nối với phần của thành viên khác:** Tôi nhận input đã được Supervisor phân loại và cung cấp kết quả truy xuất/tổng hợp đã qua kiểm chứng chính sách để Supervisor trả lời người dùng.

**Bằng chứng:** 
- **Commit hash:** `2c24583309c09eeea9032df70b8fa80f7d962475`
- **Tên tác giả in code:** Đầu mỗi file worker, sau khi import cac thu vien đều có comment: `# Huyen - Worker Owner`

---

## 2. Tôi đã ra một quyết định kỹ thuật gì? (150–200 từ)

**Quyết định:** Sử dụng chiến lược **Hybrid Strategy (Rule-based + LLM)** cho `policy_tool_worker`.

**Lý do:** Các chính sách hoàn tiền nội bộ có nhiều quy tắc cứng (như Flash Sale luôn bị chặn). Việc gọi LLM cho mọi câu hỏi không chỉ tốn tài nguyên và latency mà còn dễ gây ra hiện tượng "ảo giác". Tôi thiết kế Rule-based chạy trước để bắt ngay các quy định cứng với latency thấp (<20ms). LLM chỉ được gọi khi task mang tính đa điều kiện phức tạp. Quyết định này giúp tối ưu hóa chi phí API và tăng độ chính xác lên mức tuyệt đối cho các quy trình cơ bản.

**Trade-off đã chấp nhận:** Chấp nhận việc phải bảo trì danh sách từ khóa logic trong code thay vì chỉ cập nhật tài liệu docs.

**Bằng chứng từ trace/code:**
Logic hybrid trong `policy_tool.py`:
```python
is_flash_sale = "flash sale" in task_lower or "flash sale" in context_text
if is_flash_sale:
    exceptions_found.append({
        "type": "flash_sale_exception",
        "rule": "Đơn hàng Flash Sale không được hoàn tiền. Override mọi điều kiện khác.",
        "allows_refund": False, 
    })
```
Kết quả Trace cho thấy với câu hỏi Flash Sale, worker trả về kết quả nhanh chóng mà không cần gọi LLM (log: `LLM supplemented: no`).

---

## 3. Tôi đã sửa một lỗi gì? (150–200 từ)

**Lỗi:** `retrieval_worker` không lấy được dữ liệu và sai Collection khi chạy độc lập.

**Symptom:** Khi test standalone file `retrieval.py`, log báo `Connected to collection: 'day09_docs'` và retrieved 0 chunks, dù thực tế dữ liệu đang nằm ở collection `rag_lab`.

**Root cause:** Lỗi do file worker chưa nạp biến môi trường từ `.env` khi chạy độc lập (thiếu `load_dotenv`), dẫn đến việc nó sử dụng giá trị mặc định trong code thay vì giá trị thực tế trong file cấu hình.

**Cách sửa:**
- Thêm `from dotenv import load_dotenv; load_dotenv()` vào các file worker.
- Đồng bộ hóa file `.env` với collection thực tế là `rag_lab`.
- Chỉnh sửa code retrieval để ưu tiên đọc tên collection từ biến môi trường.

**Bằng chứng trước/sau:**
- **Trước:** `⚠️ Collection 'day09_docs' chưa có data. Retrieved: 0 chunks`.
- **Sau:** 
```text
✅ Connected to ChromaDB collection: 'rag_lab' at ./chroma_db
▶ Query: SLA ticket P1 là bao lâu?
  Retrieved: 3 chunks từ sla_p1_2026.txt
```

---

## 4. Tôi tự đánh giá đóng góp của mình (100–150 từ)

**Tôi làm tốt nhất ở điểm nào?**
Tôi đã thiết kế lớp worker rất linh hoạt (auto-detect OpenAI/Gemini) và đảm bảo I/O luôn khớp với contract, giúp giai đoạn tích hợp với Supervisor diễn ra rất mượt mà.

**Tôi làm chưa tốt hoặc còn yếu ở điểm nào?**
Quá trình chunking tài liệu ban đầu chưa thực sự tối ưu, dẫn đến context đưa vào Synthesis thi thoảng bị thừa thông tin nhiễu.

**Nhóm phụ thuộc vào tôi ở đâu?**
Supervisor phụ thuộc hoàn toàn vào kết quả từ Worker để trả lời. Nếu Worker trả về sai format hoặc bị lỗi logic, toàn bộ Pipeline sẽ bị sập.

**Phần tôi phụ thuộc vào thành viên khác:**
Tôi phụ thuộc vào Supervisor Owner cung cấp input `task` sạch và cờ `needs_tool` chính xác.

---

## 5. Nếu có thêm 2 giờ, tôi sẽ làm gì? (50–100 từ)

Tôi sẽ triển khai **LLM-as-Judge** để thẩm định lại điểm số tin cậy (confidence score) thay vì chỉ dựa vào avg chunk score từ database. Việc dùng mô hình nhỏ để đánh giá độ khớp thực tế giữa câu trả lời và context sẽ giúp giảm thiểu tối đa các trường hợp trả lời không đúng trọng tâm khi database trả về chunks có độ tương đồng thấp.

---
