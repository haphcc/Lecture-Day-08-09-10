# Báo Cáo Cá Nhân — Lab Day 09: Multi-Agent Orchestration

**Họ và tên:** Ha Hung Phuoc
**Vai trò trong nhóm:** Supervisor Owner, Trace & Docs Owner  
**Ngày nộp:** 2026-04-14  
**Độ dài yêu cầu:** 500–800 từ

---

## 1. Tôi phụ trách phần nào? (100–150 từ)

Tôi phụ trách phần điều phối luồng và phần trace/evaluation của hệ thống Day 09. Cụ thể, tôi làm trên `graph.py` và `eval_trace.py`.

**Module/file tôi chịu trách nhiệm:**
- File chính: `graph.py`, `eval_trace.py`
- Functions tôi implement: `supervisor_node()`, `route_decision()`, `build_graph()`, `run_graph()`, `run_test_questions()`, `analyze_traces()`, `compare_single_vs_multi()`

**Cách công việc của tôi kết nối với phần của thành viên khác:**

Phần của tôi là trục chính để nối các worker và MCP. Worker Owner triển khai `retrieval/policy/synthesis`, MCP Owner triển khai `mcp_server.py`, còn tôi đảm bảo `graph.py` route đúng và ghi trace đủ fields để chấm điểm. Nếu supervisor route sai hoặc trace thiếu fields thì dù worker và MCP chạy đúng, pipeline vẫn bị mất điểm Sprint 1/3/4.

**Bằng chứng:**

- `graph.py` có `route_reason` chi tiết và ghi rõ “chọn MCP vs không chọn MCP”.
- `eval_trace.py` xuất report vào `artifacts/eval_report.json`.

---

## 2. Tôi đã ra một quyết định kỹ thuật gì? (150–200 từ)

**Quyết định:** Tôi chọn supervisor rule-based routing thay vì gọi LLM để classify route.

**Lý do:**

Tôi cân nhắc 2 cách: (1) gọi LLM để phân loại câu hỏi sang retrieval/policy/human_review, hoặc (2) dùng tập keyword + risk rules. Tôi chọn cách (2) vì lab cần trace rõ, dễ debug và latency ổn định. Rule-based giúp tôi giải thích trực tiếp vì sao route, thông qua `route_reason` trong trace, thay vì “black-box” từ LLM classifier.

Ngoài ra, với bài toán helpdesk nội bộ, tín hiệu route tương đối rõ: cụm “refund/flash sale/access” nghiêng về policy, còn “P1/SLA/ticket/escalation” nghiêng về retrieval. Trường hợp mã lỗi mơ hồ `ERR-xxx` thì tôi route `human_review` để an toàn.

**Trade-off đã chấp nhận:**

Tôi chấp nhận việc rule-based có thể bỏ sót các câu diễn đạt lạ. Đổi lại, tính minh bạch và khả năng kiểm tra trace cao hơn, phù hợp yêu cầu chấm điểm của Day 09.

**Bằng chứng từ trace/code:**

```text
route_reason: "task contains P1/escalation/SLA/ticket signal | risk_high due to emergency/critical signal | chọn MCP"
workers_called: ["retrieval_worker", "synthesis_worker"]
```

---

## 3. Tôi đã sửa một lỗi gì? (150–200 từ)

**Lỗi:** Trace chưa khớp rubric ở Sprint 3 vì chỉ có `mcp_tools_used`, thiếu `mcp_tool_called` và `mcp_result`.

**Symptom (pipeline làm gì sai?):**

Pipeline vẫn chạy, nhưng format trace không trùng hoàn toàn checklist/SCORING của Sprint 3. Điều này có rủi ro mất điểm dù logic MCP thực tế đã hoạt động.

**Root cause:**

Trong `policy_tool.py`, hệ thống chỉ append vào `state["mcp_tools_used"]` (danh sách object call), không có alias fields theo tên rubric. `eval_trace.py` cũng chưa export 2 field alias này ở output record.

**Cách sửa:**

Tôi thêm đồng thời 2 alias fields vào state và trace:
- `mcp_tool_called`: danh sách tên tool gọi
- `mcp_result`: danh sách kết quả MCP trả về

Tôi cập nhật ở 3 chỗ:
1. `graph.py`: khởi tạo state có 2 field mới.
2. `workers/policy_tool.py`: mỗi lần gọi MCP append vào cả 3 field (`mcp_tools_used`, `mcp_tool_called`, `mcp_result`).
3. `eval_trace.py`: export 2 field mới ra trace record.

**Bằng chứng trước/sau:**

Trước: trace chỉ có `mcp_tools_used`.  
Sau: file `artifacts/traces/run_20260414_160110_509064_02713e.json` có:
- `mcp_tool_called: ["search_kb"]`
- `mcp_result: [...]`
- `transport: "http"` trong call record

---

## 4. Tôi tự đánh giá đóng góp của mình (100–150 từ)

**Tôi làm tốt nhất ở điểm nào?**

Tôi làm tốt phần orchestration và chuẩn hóa trace. Tôi ưu tiên khả năng giải thích quyết định route và làm cho trace đủ chi tiết để team debug nhanh.

**Tôi làm chưa tốt hoặc còn yếu ở điểm nào?**

Tôi chưa tối ưu latency tốt; hiện pipeline vẫn chậm ở nhiều query do load embeddings/worker flow. Tôi cũng cần siết thêm tiêu chí quality ở synthesis để giảm confidence thấp.

**Nhóm phụ thuộc vào tôi ở đâu?**

Nhóm phụ thuộc vào tôi ở phần supervisor route và chuẩn trace. Nếu phần này không ổn thì kết quả worker/MCP khó được chấm đúng.

**Phần tôi phụ thuộc vào thành viên khác:**

Tôi phụ thuộc Worker Owner để có output retrieval/policy/synthesis đủ chất lượng, và phụ thuộc MCP Owner để server/tool dispatch hoạt động ổn định khi chạy real flow.

---

## 5. Nếu có thêm 2 giờ, tôi sẽ làm gì? (50–100 từ)

Tôi sẽ chuẩn hóa pipeline chạy theo “fresh run folder” cho mỗi lần test để tách trace cũ/mới, vì hiện metrics tổng hợp bị nhiễu khi cộng dồn nhiều batch trace. Tôi chọn cải tiến này vì trong `artifacts/traces/` đã có nhiều đợt run khác nhau, làm việc đọc tỷ lệ route/HITL và so sánh giữa các lần chạy không còn sạch.

---

*Lưu file này với tên: `reports/individual/[ten_ban].md`*  
*Ví dụ: `reports/individual/nguyen_van_a.md`*
