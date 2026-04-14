# Routing Decisions Log — Lab Day 09

**Nhóm:** Helpdesk AI Assistant  
**Ngày:** 2026-04-14

> Ghi lại các quyết định routing thật từ trace trong `artifacts/traces/`.

---

## Routing Decision #1

**Task đầu vào:**
> Sản phẩm kỹ thuật số (license key) có được hoàn tiền không?

**Worker được chọn:** `policy_tool_worker`  
**Route reason (từ trace):** `task contains policy/access/refund signal | mcp=yes`  
**MCP tools được gọi:** `search_kb`  
**Workers called sequence:** `policy_tool_worker -> synthesis_worker`

**Kết quả thực tế:**
- final_answer (ngắn): Không hoàn tiền cho license key theo policy hiện hành.
- confidence: `0.10`
- Correct routing? `Yes`

**Nhận xét:**

Routing đúng vì query chứa keyword refund/license và cần policy branch. Điểm yếu nằm ở synthesis: dù policy_result đã block refund, answer vẫn cần được ground chặt hơn để tránh lan sang các chunk nhiễu.

---

## Routing Decision #2

**Task đầu vào:**
> Ticket P1 được tạo lúc 22:47. Ai sẽ nhận thông báo đầu tiên và qua kênh nào? Escalation xảy ra lúc mấy giờ?

**Worker được chọn:** `retrieval_worker`  
**Route reason (từ trace):** `task contains P1/escalation/SLA/ticket signal | mcp=no`  
**MCP tools được gọi:** `None`  
**Workers called sequence:** `retrieval_worker -> synthesis_worker`

**Kết quả thực tế:**
- final_answer (ngắn): Absentia / không tìm thấy đủ thông tin, nhưng không bịa.
- confidence: `0.25`
- Correct routing? `Yes`

**Nhận xét:**

Routing đúng vì đây là câu SLA/ticket. Tuy nhiên retrieval vẫn kéo thêm policy/HR chunks, nên synthesis phải abstain. Đây là dấu hiệu cho thấy top-k và ranking cần sạch hơn.

---

## Routing Decision #3

**Task đầu vào:**
> Khách hàng đặt đơn ngày 31/01/2026 và yêu cầu hoàn tiền ngày 07/02/2026. Sản phẩm lỗi nhà sản xuất, chưa kích hoạt, không phải Flash Sale. Được hoàn tiền không?

**Worker được chọn:** `policy_tool_worker`  
**Route reason (từ trace):** `task contains policy/access/refund signal | mcp=yes`  
**MCP tools được gọi:** `search_kb`  
**Workers called sequence:** `policy_tool_worker -> synthesis_worker`

**Kết quả thực tế:**
- final_answer (ngắn): Trả lời có, nhưng synthesis kết luận sai rằng được hoàn tiền.
- confidence: `0.10`
- Correct routing? `Yes`

**Nhận xét:**

Routing đúng, nhưng đây là failure mode của synthesis: policy_result đã ghi `policy_version_note` và blocking exception, nhưng answer cuối vẫn đi sai hướng. Đây là case quan trọng để review prompt grounding và ưu tiên policy_result hơn raw retrieval text.

---

## Routing Decision #4 (tuỳ chọn — bonus)

**Task đầu vào:**
> ERR-403-AUTH xuất hiện khi truy cập hệ thống, nhưng không có thêm ngữ cảnh.

**Worker được chọn:** `retrieval_worker` sau khi qua `human_review`  
**Route reason:** `unknown ERR code with low context -> human review | mcp=no | human approved -> retrieval`

**Nhận xét: Đây là trường hợp routing khó nhất trong lab. Tại sao?**

Vì supervisor phải ưu tiên an toàn thay vì đoán. Trace cho thấy hệ thống đi qua human_review rồi mới quay lại retrieval; đây là nhánh đúng nhất cho mã lỗi không rõ. Case này giúp tránh hallucination khi không có đủ evidence.

---

## Tổng kết

### Routing Distribution

> Tổng hợp theo 15 trace mới nhất của batch chạy gần nhất.

| Worker | Số câu được route | % tổng |
|--------|------------------|--------|
| retrieval_worker | 10 | 66.7% |
| policy_tool_worker | 5 | 33.3% |
| human_review | 0 | 0% |

> Lưu ý: `human_review` đang xuất hiện như một bước trung gian trong trace hitl, không phải terminal route cuối của supervisor.

### Routing Accuracy

- Câu route đúng: `15 / 15`
- Câu route sai (đã sửa bằng cách nào?): `0`
- Câu trigger HITL: `15`

### Lesson Learned về Routing

1. Keyword-based supervisor đủ tốt cho bài lab này, vì các nhánh chính đều rõ tín hiệu: refund/license, P1/SLA/ticket, ERR-xxx.
2. `route_reason` cần nêu thêm signal chính và trạng thái tool/HITL để trace dễ debug hơn.

### Route Reason Quality

`route_reason` hiện đã đủ để debug ở mức high-level, nhưng vẫn có thể cải tiến bằng cách thêm 3 phần: signal chính, lý do chọn/không chọn MCP, và nhánh fallback cuối cùng. Điều này đặc biệt hữu ích cho case temporal scoping và multi-hop.
