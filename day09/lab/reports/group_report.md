# Báo Cáo Nhóm — Lab Day 09: Multi-Agent Orchestration

**Tên nhóm:** Day 09 Multi-Agent Helpdesk Team  
**Thành viên:**
| Tên | Vai trò | Email |
|-----|---------|-------|
| Phuoc | Supervisor Owner, Trace & Docs Owner | phuocha@outlook.com |
| Huyen | Worker Owner | nguyennguyen200455@gmail.com |
| Hoai | MCP Owner, Trace & Docs Owner | hoaihanh2501@gmail.com |

**Ngày nộp:** 2026-04-14  
**Repo:** haphcc/Lecture-Day-08-09-10  
**Độ dài khuyến nghị:** 600–1000 từ

---

> **Hướng dẫn nộp group report:**
> 
> - File này nộp tại: `reports/group_report.md`
> - Deadline: Được phép commit **sau 18:00** (xem SCORING.md)
> - Tập trung vào **quyết định kỹ thuật cấp nhóm** — không trùng lặp với individual reports
> - Phải có **bằng chứng từ code/trace** — không mô tả chung chung
> - Mỗi mục phải có ít nhất 1 ví dụ cụ thể từ code hoặc trace thực tế của nhóm

---

## 1. Kiến trúc nhóm đã xây dựng (150–200 từ)

> Mô tả ngắn gọn hệ thống nhóm: bao nhiêu workers, routing logic hoạt động thế nào,
> MCP tools nào được tích hợp. Dùng kết quả từ `docs/system_architecture.md`.

**Hệ thống tổng quan:**

Nhóm đã refactor bài toán trợ lý nội bộ CS + IT Helpdesk từ một pipeline RAG đơn khối sang kiến trúc Supervisor-Worker gồm 3 worker chính và 1 MCP server mock. `graph.py` giữ vai trò điều phối luồng, `workers/retrieval.py` lấy bằng chứng từ ChromaDB, `workers/policy_tool.py` xử lý policy và gọi MCP khi cần, còn `workers/synthesis.py` tổng hợp câu trả lời có citation và trigger HITL nếu confidence thấp. Dữ liệu nội bộ được index sẵn trong `chroma_db`, và toàn bộ luồng được ghi trace vào `artifacts/traces/` để kiểm tra lại từng bước.

**Routing logic cốt lõi:**

Supervisor dùng rule-based keyword matching, không dùng classifier ngoài. Các tín hiệu như “hoàn tiền”, “refund”, “flash sale”, “license”, “cấp quyền”, “access” đẩy sang `policy_tool_worker`, còn “P1”, “SLA”, “ticket”, “escalation”, “sự cố” ưu tiên `retrieval_worker`. Nếu task chứa mã lỗi mơ hồ dạng `ERR-xxx` và thiếu context, hệ thống chuyển sang `human_review`. Trong trace mới nhất, `route_reason` còn ghi rõ có chọn MCP hay không, ví dụ: `task contains P1/escalation/SLA/ticket signal | risk_high due to emergency/critical signal | chọn MCP`.

**MCP tools đã tích hợp:**

- `search_kb`: tìm knowledge base nội bộ qua HTTP MCP hoặc fallback in-process.
- `get_ticket_info`: tra cứu ticket mock, dùng cho case incident/P1.
- `check_access_permission`: kiểm tra cấp quyền theo Access Control SOP.
- `create_ticket`: tạo ticket mock để mở rộng khả năng của MCP server.

Ví dụ trace có gọi MCP: `run_20260414_160110_509064_02713e.json` ghi `mcp_tool_called: ["search_kb"]` và `mcp_result` chứa kết quả truy vấn từ `policy_refund_v4.txt`.

---

## 2. Quyết định kỹ thuật quan trọng nhất (200–250 từ)

> Chọn **1 quyết định thiết kế** mà nhóm thảo luận và đánh đổi nhiều nhất.
> Phải có: (a) vấn đề gặp phải, (b) các phương án cân nhắc, (c) lý do chọn phương án đã chọn.

**Quyết định:** Tách hệ thống thành Supervisor-Worker + MCP thay vì giữ monolithic pipeline như Day 08.

**Bối cảnh vấn đề:**

Nhóm phải giải quyết bài toán mà Day 08 không làm tốt: khi câu trả lời sai thì không biết lỗi nằm ở retrieval, policy check hay generation. Ngoài ra, Day 09 còn yêu cầu khả năng gọi tool ngoài và ghi trace phục vụ đánh giá, nên một pipeline đơn khối sẽ rất khó audit và khó mở rộng.

**Các phương án đã cân nhắc:**

| Phương án | Ưu điểm | Nhược điểm |
|-----------|---------|-----------|
| Giữ monolithic pipeline | Ít file, ít thay đổi, dễ chạy nhanh | Khó trace, khó thay từng phần, không phù hợp bài toán tool-call |
| Tách Supervisor-Worker + MCP | Trace rõ, mỗi phần test độc lập, mở rộng tool dễ | Latency cao hơn, cần contract chặt chẽ giữa các thành phần |

**Phương án đã chọn và lý do:**

Nhóm chọn tách Supervisor-Worker và MCP vì yêu cầu của lab ưu tiên trace, debug và mở rộng. Khi chạy pipeline, hệ thống ghi rõ `route_reason`, `workers_called`, `mcp_tools_used`, `mcp_tool_called` và `mcp_result`, nên có thể khoanh vùng lỗi nhanh theo tầng. Đây là lợi ích rõ nhất so với single-agent: câu hỏi nào sai có thể nhìn ngay worker nào đã xử lý, có gọi MCP hay không, và synthesis có trigger HITL hay không.

**Bằng chứng từ trace/code:**

```text
"route_reason": "task contains P1/escalation/SLA/ticket signal | risk_high due to emergency/critical signal | chọn MCP"
"mcp_tool_called": ["search_kb"]
"mcp_result": [...]
"workers_called": ["retrieval_worker", "synthesis_worker"]
```

---

## 3. Kết quả grading questions (150–200 từ)

> Sau khi chạy pipeline với grading_questions.json (public lúc 17:00):
> - Nhóm đạt bao nhiêu điểm raw?
> - Câu nào pipeline xử lý tốt nhất?
> - Câu nào pipeline fail hoặc gặp khó khăn?

**Tổng điểm raw ước tính:** chưa chốt / 96

**Câu pipeline xử lý tốt nhất:**
- ID: q01 — Lý do tốt: route đúng sang `retrieval_worker`, lấy được SLA P1 từ `sla_p1_2026.txt`, trace rõ ràng và không cần HITL.

**Câu pipeline fail hoặc partial:**
- ID: q12 — Fail ở đâu: policy temporal scoping + synthesis dễ lệch khi câu hỏi gắn ngày và hoàn tiền.  
  Root cause: synthesis vẫn còn phụ thuộc vào grounding và confidence thấp khi evidence không sạch.

**Câu gq07 (abstain):** Nhóm xử lý thế nào?

Nhóm để worker trả về abstain thay vì bịa khi evidence không đủ rõ. Cơ chế này thể hiện qua synthesis worker: nếu không có thông tin chắc chắn thì trả về thông báo liên hệ CS team và hạ confidence để kích hoạt HITL.

**Câu gq09 (multi-hop khó nhất):** Trace ghi được 2 workers không? Kết quả thế nào?

Có. Trace ghi được ít nhất `retrieval_worker` và `synthesis_worker`; với các case có policy hoặc tool call thì trace còn có `policy_tool_worker` và `mcp_tools_used`. Kết quả thực tế là trace đủ để nhìn được đường đi của câu hỏi, nhưng answer vẫn cần cải thiện ở phần synthesis để tránh lệch khi evidence nhiều nguồn.

---

## 4. So sánh Day 08 vs Day 09 — Điều nhóm quan sát được (150–200 từ)

> Dựa vào `docs/single_vs_multi_comparison.md` — trích kết quả thực tế.

**Metric thay đổi rõ nhất (có số liệu):**

Metric thay đổi rõ nhất là routing visibility và khả năng trace. Theo `eval_report.json`, Day 09 có `mcp_usage_rate: 10/55 (18%)`, `avg_latency_ms: 9272`, `avg_confidence: 0.423` trên toàn bộ trace đã chạy. Dù latency cao hơn, đổi lại hệ thống có thể biết chính xác câu nào chọn retrieval, câu nào chọn policy, và câu nào cần MCP.

**Điều nhóm bất ngờ nhất khi chuyển từ single sang multi-agent:**

Điều bất ngờ nhất là khả năng debug tốt hơn ngay cả khi quality answer chưa cao. Chỉ cần đọc trace là biết câu hỏi đi qua worker nào, có HITL hay không, và có gọi MCP hay không. Đây là thứ Day 08 không có.

**Trường hợp multi-agent KHÔNG giúp ích hoặc làm chậm hệ thống:**

Với câu đơn giản chỉ cần tra một tài liệu, multi-agent làm chậm hơn do phải qua supervisor, worker, synthesis và đôi khi phải load model/embedding. Batch trace gần nhất cho thấy latency vẫn ở mức cao, nên overhead này chỉ đáng giá khi cần audit, tool-call, hoặc multi-hop.

---

## 5. Phân công và đánh giá nhóm (100–150 từ)

> Đánh giá trung thực về quá trình làm việc nhóm.

**Phân công thực tế:**

| Thành viên | Phần đã làm | Sprint |
|------------|-------------|--------|
| Phuoc | `graph.py`, `eval_trace.py`, `reports/`, `report/trace integration` | Sprint 1, 4 |
| Worker Owner | `workers/retrieval.py`, `workers/policy_tool.py`, `workers/synthesis.py` | Sprint 2 |
| Hoai | `mcp_server.py`, `docs/`, MCP HTTP server, tool schema | Sprint 3 |

**Điều nhóm làm tốt:**

Nhóm chốt contract khá rõ nên mỗi người có thể làm song song mà không chờ nhau quá lâu. Việc trace hóa sớm giúp phát hiện lỗi nhanh, đặc biệt là các case policy và HITL.

**Điều nhóm làm chưa tốt hoặc gặp vấn đề về phối hợp:**

Một số trace đầu còn tạo nhiều file cũ do rerun nhiều lần, làm số liệu tổng hợp bị phình ra và khó đọc nếu không dọn workspace. Ngoài ra, synthesis vẫn còn nhạy với evidence nhiễu và confidence còn thấp.

**Nếu làm lại, nhóm sẽ thay đổi gì trong cách tổ chức?**

Nhóm sẽ khóa sớm chuẩn trace và quy ước số liệu ngay từ đầu, đồng thời tách một run folder riêng cho mỗi đợt test để tránh lẫn trace cũ với trace mới.

---

## 6. Nếu có thêm 1 ngày, nhóm sẽ làm gì? (50–100 từ)

> 1–2 cải tiến cụ thể với lý do có bằng chứng từ trace/scorecard.

Nhóm sẽ ưu tiên làm sạch synthesis để ưu tiên `policy_result` hơn raw retrieved chunks ở case temporal scoping, và giảm latency bằng cách hạn chế load embedding model lặp lại. Ngoài ra, sẽ dọn các trace cũ và chỉ giữ batch trace cuối cùng để báo cáo dễ đọc hơn.

---

*File này lưu tại: `reports/group_report.md`*  
*Commit sau 18:00 được phép theo SCORING.md*
