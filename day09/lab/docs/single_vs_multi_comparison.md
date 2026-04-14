# Single Agent vs Multi-Agent Comparison — Lab Day 09

**Nhóm:** Helpdesk AI Assistant  
**Ngày:** 2026-04-14

> So sánh Day 08 (single-agent RAG) với Day 09 (supervisor-worker) dựa trên trace hiện có.

---

## 1. Metrics Comparison

> Day 08 trong repo hiện không có runtime trace tương thích với format Day 09, nên các cột Day 08 được ghi `N/A` và giải thích ở ghi chú.

| Metric | Day 08 (Single Agent) | Day 09 (Multi-Agent) | Delta | Ghi chú |
|--------|----------------------|---------------------|-------|---------|
| Avg confidence | N/A | `0.151` | N/A | Tính trên 15 trace mới nhất |
| Avg latency (ms) | N/A | `8995` | N/A | Graph + worker pipeline hiện vẫn còn khá nặng |
| Abstain rate (%) | N/A | `26.7%` (4/15) | N/A | Câu trả lời abstain thay vì bịa |
| Multi-hop accuracy | N/A | `0% full-answer` / `100% routing visibility` | N/A | q09 đi qua human review rồi retrieval, nhưng answer cuối vẫn chỉ abstain |
| Routing visibility | ✗ Không có | ✓ Có `route_reason` | N/A | Có thể truy vết theo trace |
| Debug time (estimate) | N/A | `~5 phút` | N/A | Đọc trace là đủ khoanh vùng lỗi chính |
| HITL trigger rate | N/A | `100%` (15/15) | N/A | Đây là đặc trưng của batch trace hiện tại |

> Ghi chú: Day 08 scorecard trong repo dùng các metric khác (faithfulness, relevance, completeness), nên không quy đổi trực tiếp sang confidence/latency.

---

## 2. Phân tích theo loại câu hỏi

### 2.1 Câu hỏi đơn giản (single-document)

| Nhận xét | Day 08 | Day 09 |
|---------|--------|--------|
| Accuracy | N/A | Mixed: q07 đúng, q11 abstain |
| Latency | N/A | Cao hơn vì pipeline qua supervisor + worker + synthesis |
| Observation | N/A | Routing rõ nhưng retrieval vẫn có thể kéo nhiễu từ doc không liên quan |

**Kết luận:** Multi-agent không tự động làm câu đơn giản tốt hơn; lợi ích lớn nhất là trace và kiểm soát lỗi. Với câu đơn giản, overhead của orchestration có thể làm latency tăng.

### 2.2 Câu hỏi multi-hop (cross-document)

| Nhận xét | Day 08 | Day 09 |
|---------|--------|--------|
| Accuracy | N/A | `0% full answer` trên q09 hiện tại |
| Routing visible? | ✗ | ✓ |
| Observation | N/A | q09 đi qua `human_review -> retrieval -> synthesis`, nên rất dễ thấy vì sao hệ thống chọn abstain thay vì bịa |

**Kết luận:** Với multi-hop, Day 09 tốt hơn ở khả năng kiểm soát và debug. Tuy nhiên chất lượng answer vẫn cần cải thiện vì synthesis còn dễ rơi vào abstain hoặc suy luận sai nếu evidence chưa sạch.

### 2.3 Câu hỏi cần abstain

| Nhận xét | Day 08 | Day 09 |
|---------|--------|--------|
| Abstain rate | N/A | `26.7%` |
| Hallucination cases | N/A | `1` rõ ràng trong batch mới nhất (`q12`) |
| Observation | N/A | Hệ thống có xu hướng thận trọng hơn, nhưng vẫn có case synthesis override policy_result và trả lời sai |

**Kết luận:** Day 09 giảm hallucination ở các case mơ hồ nhờ HITL và abstain, nhưng không loại bỏ hoàn toàn lỗi synthesis. Cần ưu tiên policy_result hơn raw text ở các query temporal scoping.

---

## 3. Debuggability Analysis

### Day 08 — Debug workflow
```text
Khi answer sai -> phải đọc toàn bộ RAG pipeline code -> tìm lỗi ở indexing / retrieval / generation
Không có trace theo route -> khó biết bắt đầu từ đâu
Thời gian ước tính: N/A trong repo hiện tại
```

### Day 09 — Debug workflow
```text
Khi answer sai -> đọc trace -> xem supervisor_route + route_reason
  -> Nếu route sai -> sửa supervisor routing logic
  -> Nếu retrieval sai -> test retrieval_worker độc lập
  -> Nếu policy sai -> kiểm tra mcp_tools_used + policy_result
  -> Nếu synthesis sai -> xem confidence + hitl_triggered
Thời gian ước tính: ~5 phút cho case điển hình
```

**Câu cụ thể nhóm đã debug:**

Case `q12` cho thấy policy_result đã bắt đúng temporal scoping và Flash Sale, nhưng synthesis vẫn kết luận sai rằng khách hàng được hoàn tiền. Nhờ trace, nhóm biết lỗi nằm ở synthesis/gounding chứ không phải routing.

---

## 4. Extensibility Analysis

| Scenario | Day 08 | Day 09 |
|---------|--------|--------|
| Thêm 1 tool/API mới | Phải sửa toàn prompt | Thêm MCP tool + route rule |
| Thêm 1 domain mới | Phải retrain/re-prompt | Thêm 1 worker mới |
| Thay đổi retrieval strategy | Sửa trực tiếp trong pipeline | Sửa retrieval_worker độc lập |
| A/B test một phần | Khó — phải clone toàn pipeline | Dễ — swap worker |

**Nhận xét:**

Day 09 rõ ràng dễ mở rộng hơn vì mỗi capability được gắn vào một worker riêng. Đặc biệt, MCP giúp mở rộng toolset mà không phải nhúng hard-code vào prompt chính.

---

## 5. Cost & Latency Trade-off

> Số LLM calls ở Day 09 phụ thuộc vào việc policy worker có bật LLM analysis hay không.

| Scenario | Day 08 calls | Day 09 calls |
|---------|-------------|-------------|
| Simple query | 1 LLM call | 1 LLM call (synthesis) |
| Complex query | 1 LLM call | 1-2 LLM calls (policy + synthesis) |
| MCP tool call | N/A | 1 call / mỗi tool |

**Nhận xét về cost-benefit:**

Day 09 tốn hơn về latency và orchestration, nhưng đổi lại có trace rõ, tách được lỗi theo tầng và thêm MCP tool được mà không phá core pipeline. Với bài toán nội bộ cần audit/debug, trade-off này chấp nhận được.

---

## 6. Kết luận

**Multi-agent tốt hơn single agent ở điểm nào?**

1. Trace rõ ràng hơn: biết câu hỏi đi qua worker nào, có gọi MCP hay không, và vì sao.
2. Dễ debug và mở rộng: worker độc lập, thay từng phần mà không phải viết lại toàn pipeline.

**Multi-agent kém hơn hoặc không khác biệt ở điểm nào?**

1. Latency cao hơn do có thêm lớp orchestration và nhiều bước xử lý hơn.

**Khi nào KHÔNG nên dùng multi-agent?**

Khi bài toán chỉ là Q&A đơn giản, không cần audit trace, không cần tool call ngoài và không có yêu cầu debug theo tầng.

**Nếu tiếp tục phát triển hệ thống này, nhóm sẽ thêm gì?**

1. Tăng chất lượng retrieval bằng chunking tốt hơn và giảm noisy chunks.
2. Siết synthesis để ưu tiên policy_result hơn raw retrieved text ở các case temporal scoping.
