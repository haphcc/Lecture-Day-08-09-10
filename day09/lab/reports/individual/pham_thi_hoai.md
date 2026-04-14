# Báo Cáo Cá Nhân — Lab Day 09: Multi-Agent Orchestration

**Họ và tên:** Phạm Thị Hoài  
**Vai trò trong nhóm:** MCP Owner / Trace & Docs Owner  
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

Tôi phụ trách phần MCP và tài liệu trace của Day 09. File chính tôi chịu trách nhiệm là [day09/lab/mcp_server.py](../../mcp_server.py), còn phần docs tôi điền là [day09/lab/docs/system_architecture.md](../../docs/system_architecture.md), [day09/lab/docs/routing_decisions.md](../../docs/routing_decisions.md), và [day09/lab/docs/single_vs_multi_comparison.md](../../docs/single_vs_multi_comparison.md). Trong `mcp_server.py`, tôi implement các hàm `_simple_kb_search()`, `_validate_tool_input()`, `tool_search_kb()`, và `dispatch_tool()` để worker policy có thể gọi tool ổn định, có schema rõ ràng, và không văng exception. Công việc của tôi nối trực tiếp với phần của A và B: khi graph route sang `policy_tool_worker`, MCP của tôi là lớp cung cấp capability cho worker đó; còn trace do graph sinh ra là dữ liệu đầu vào để tôi viết docs và so sánh Day 08 với Day 09.

**Bằng chứng:** trace `run_20260414_152620_215706_ff10f2.json` và `run_20260414_152658_355725_770359.json` đều ghi `mcp_tools_used` có `search_kb`; test `dispatch_tool('get_ticket_info', {'ticket_id':'P1-LATEST'})` trả `IT-9847`; test `dispatch_tool('search_kb', {'query':'SLA', 'top_k':'2'})` trả lỗi validate đúng chuẩn.

---

## 2. Tôi đã ra một quyết định kỹ thuật gì? (150–200 từ)

**Quyết định:** Tôi chọn xây dựng MCP theo hướng mock nhưng production-like: có schema discovery, validate input trước khi gọi tool, và fallback search thật từ `data/docs` nếu ChromaDB chưa sẵn sàng.

**Lý do:**

Tôi không muốn worker policy phụ thuộc vào một backend vector có thể thiếu index hoặc input sai kiểu. Nếu `dispatch_tool()` không chặn sớm, trace sẽ không đáng tin, còn nếu `search_kb` chỉ trả mock text thì policy worker có thể hoạt động “trông có vẻ đúng” nhưng không có giá trị thật. Với cách này, MCP vẫn chạy ổn khi environment chưa hoàn hảo, nhưng trace vẫn giữ được tính kiểm chứng. Điều này phù hợp với mục tiêu của lab: trace rõ, dễ debug, và demo được end-to-end.

**Trade-off đã chấp nhận:**

Tôi chấp nhận việc search có thể chậm hơn lúc đầu vì phải thử retrieval thật trước, rồi mới fallback lexical. Đổi lại, hệ thống không crash và không trả dữ liệu giả. Đây là trade-off hợp lý cho một bài lab thiên về quan sát và truy vết.

**Bằng chứng từ trace/code:**

```text
dispatch_tool('get_ticket_info', {'ticket_id':'P1-LATEST'}) -> IT-9847
dispatch_tool('check_access_permission', {'access_level':2,'requester_role':'contractor','is_emergency':True}) -> emergency_override=True
dispatch_tool('search_kb', {'query':'SLA', 'top_k':'2'}) -> Invalid type for 'top_k' in 'search_kb': expected integer, got str

Trace q07: policy_tool_worker -> synthesis_worker, mcp_tools_used = [search_kb]
Trace q12: policy_tool_worker -> synthesis_worker, mcp_tools_used = [search_kb]
```

---

## 3. Tôi đã sửa một lỗi gì? (150–200 từ)

**Lỗi:** `search_kb` ban đầu dễ phụ thuộc vào trạng thái ChromaDB và chưa chặn đủ input sai kiểu, đặc biệt là `top_k` không phải số nguyên.

**Symptom (pipeline làm gì sai?):**

Khi policy worker gọi MCP, nếu tham số đầu vào sai hoặc index chưa sẵn sàng, tool có thể không trả về chunks hữu ích, khiến trace bị thiếu bằng chứng thật hoặc đẩy system sang mock data. Điều này làm phần routing/comparison khó tin cậy.

**Root cause (lỗi nằm ở đâu — indexing, routing, contract, worker logic?):**

Lỗi nằm ở lớp contract/tool trong `mcp_server.py`, không phải ở graph. `dispatch_tool()` trước đó chưa validate đủ sớm, và `tool_search_kb()` chưa có fallback lexical search có thật từ 5 tài liệu nội bộ.

**Cách sửa:**

Tôi thêm `_validate_tool_input()` để chặn missing field và sai kiểu trước khi gọi tool. Tôi cũng thêm `_simple_kb_search()` để fallback sang search trên `data/docs` khi Chroma không sẵn sàng hoặc không trả chunks. Sau sửa, `get_ticket_info` trả `IT-9847`, `check_access_permission` trả `emergency_override=True`, và `search_kb` báo lỗi rõ ràng nếu `top_k` là string thay vì âm thầm crash.

**Bằng chứng trước/sau:**

Trước sửa, `search_kb` phụ thuộc trạng thái môi trường và không đảm bảo input validation. Sau sửa, `dispatch_tool('search_kb', {'query':'SLA', 'top_k':'2'})` trả lỗi `Invalid type for 'top_k' in 'search_kb': expected integer, got str`. Đây là bằng chứng rõ nhất cho thấy tool layer đã được làm an toàn hơn.

---

## 4. Tôi tự đánh giá đóng góp của mình (100–150 từ)

**Tôi làm tốt nhất ở điểm nào?**

Tôi làm tốt nhất ở phần biến capability bên ngoài thành một MCP mock có thể gọi thật, có schema, có fallback và có trace. Phần này giúp policy worker của nhóm hoạt động ổn định hơn và giúp báo cáo nhóm có bằng chứng rõ ràng thay vì mô tả chung chung.

**Tôi làm chưa tốt hoặc còn yếu ở điểm nào?**

Tôi chưa xử lý được hết mọi lỗi về quality của synthesis. Trace q12 cho thấy policy_result đã đúng hơn, nhưng answer cuối vẫn có thể lệch nếu synthesis ưu tiên raw retrieved text quá nhiều. Đây là phần tôi cần phối hợp thêm với bạn làm worker synthesis để siết grounding hơn.

**Nhóm phụ thuộc vào tôi ở đâu?**

Nhóm phụ thuộc vào tôi ở chỗ policy worker cần MCP để lấy ticket/KB. Nếu `mcp_server.py` chưa ổn, `mcp_tools_used` sẽ thiếu, và docs/routing/comparison cũng không có dữ liệu để viết.

**Phần tôi phụ thuộc vào thành viên khác:**

Tôi phụ thuộc vào A để graph chạy full trace thật, và phụ thuộc vào B để policy/synthesis worker gọi MCP rồi sinh trace đúng format. Khi có trace đó, tôi mới viết được routing decisions và comparison có số liệu.

---

## 5. Nếu có thêm 2 giờ, tôi sẽ làm gì? (50–100 từ)

Nếu có thêm 2 giờ, tôi sẽ viết một script tổng hợp metrics tự động từ `artifacts/traces/` để xuất số liệu cho phần so sánh Day 08 vs Day 09. Tôi muốn làm việc này vì trace hiện tại cho thấy các case q07, q09, q11 và q12 đã có pattern khá rõ, nhưng việc rút số liệu thủ công vẫn tốn thời gian. Một script nhỏ sẽ giúp nhóm cập nhật report nhanh hơn mỗi khi chạy lại pipeline.

---

*Lưu file này với tên: `reports/individual/[ten_ban].md`*  
*Ví dụ: `reports/individual/nguyen_van_a.md`*
