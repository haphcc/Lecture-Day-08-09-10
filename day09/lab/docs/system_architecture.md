# System Architecture — Lab Day 09

**Nhóm:** Helpdesk AI Assistant  
**Ngày:** 2026-04-14  
**Version:** 1.0

---

## 1. Tổng quan kiến trúc

**Pattern đã chọn:** Supervisor-Worker

**Lý do chọn pattern này thay vì single agent:**

Chúng tôi tách hệ thống thành supervisor và workers để debug được từng tầng thay vì để một agent làm toàn bộ retrieve, policy check, synthesis và tool call. Cách này giúp trace rõ hơn, thay worker dễ hơn, và đặc biệt phù hợp với bài toán helpdesk có cả câu hỏi SLA, refund policy, access control và multi-hop. Trong trace hiện tại, route_reason, workers_called, mcp_tools_used và hitl_triggered đều được ghi riêng, nên khi sai có thể khoanh vùng lỗi theo route, retrieval, policy hay synthesis.

---

## 2. Sơ đồ Pipeline

**Sơ đồ thực tế của nhóm:**

```text
User Request
  │
  ▼
┌──────────────────────────────┐
│ Supervisor                   │
│ - route_reason               │
│ - risk_high                  │
│ - needs_tool                 │
└──────────────┬───────────────┘
      │
      ▼
     [route_decision]
      │
   ┌────────┼───────────┐
   │        │           │
   ▼        ▼           ▼
Retrieval   Policy Tool   Human Review
 Worker      Worker       (HITL placeholder)
  │           │           │
  │           ├──────┐    │
  │           │ MCP   │    │
  │           │ tools │    │
  │           └──────┘    │
  └────────────┬───────────┘
      ▼
     Synthesis Worker
  (grounded answer + cite)
      │
      ▼
       Output
```

---

## 3. Vai trò từng thành phần

### Supervisor (`graph.py`)

| Thuộc tính | Mô tả |
|-----------|-------|
| **Nhiệm vụ** | Phân loại task, chọn route, đánh dấu risk và nhu cầu gọi tool |
| **Input** | `task` |
| **Output** | `supervisor_route`, `route_reason`, `risk_high`, `needs_tool` |
| **Routing logic** | Keyword-based: refund/license/access → policy; P1/SLA/ticket → retrieval; ERR-xxx mơ hồ → human_review |
| **HITL condition** | Mã lỗi không rõ + thiếu context, hoặc synthesis confidence thấp sẽ được flag trong trace |

### Retrieval Worker (`workers/retrieval.py`)

| Thuộc tính | Mô tả |
|-----------|-------|
| **Nhiệm vụ** | Query ChromaDB để lấy chunks bằng chứng liên quan |
| **Embedding model** | `SentenceTransformer(all-MiniLM-L6-v2)`; fallback sang OpenAI embedding nếu có API key |
| **Top-k** | Mặc định `3` |
| **Stateless?** | Yes |

### Policy Tool Worker (`workers/policy_tool.py`)

| Thuộc tính | Mô tả |
|-----------|-------|
| **Nhiệm vụ** | Kiểm tra policy, phát hiện exception, gọi MCP khi cần |
| **MCP tools gọi** | `search_kb`, `get_ticket_info` |
| **Exception cases xử lý** | Flash Sale, digital product, activated product, manufacturer defect, temporal scoping trước 01/02/2026 |

### Synthesis Worker (`workers/synthesis.py`)

| Thuộc tính | Mô tả |
|-----------|-------|
| **LLM model** | GPT-4o-mini hoặc Gemini 1.5 Flash tùy API key |
| **Temperature** | `0.1` |
| **Grounding strategy** | Chỉ trả lời từ `retrieved_chunks` + `policy_result`, citation theo `[source]` |
| **Abstain condition** | Nếu không đủ evidence thì trả lời abstain; confidence `< 0.4` sẽ trigger HITL |

### MCP Server (`mcp_server.py`)

| Tool | Input | Output |
|------|-------|--------|
| `search_kb` | `query`, `top_k` | `chunks`, `sources`, `total_found` |
| `get_ticket_info` | `ticket_id` | ticket details |
| `check_access_permission` | `access_level`, `requester_role`, `is_emergency` | `can_grant`, `required_approvers`, `emergency_override` |
| `create_ticket` | `priority`, `title`, `description` | `ticket_id`, `url`, `created_at` |

---

## 4. Shared State Schema

| Field | Type | Mô tả | Ai đọc/ghi |
|-------|------|-------|-----------|
| `task` | `str` | Câu hỏi đầu vào | supervisor đọc |
| `supervisor_route` | `str` | Worker được chọn | supervisor ghi |
| `route_reason` | `str` | Lý do route | supervisor ghi |
| `risk_high` | `bool` | Cảnh báo risk/khẩn cấp | supervisor ghi |
| `needs_tool` | `bool` | Có cần MCP hay không | supervisor ghi |
| `hitl_triggered` | `bool` | Có cần human review không | human_review hoặc synthesis ghi |
| `retrieved_chunks` | `list` | Evidence từ retrieval | retrieval ghi, synthesis đọc |
| `retrieved_sources` | `list` | Nguồn đã lấy | retrieval ghi |
| `policy_result` | `dict` | Kết quả kiểm tra policy | policy_tool ghi, synthesis đọc |
| `mcp_tools_used` | `list` | Tool calls đã thực hiện | policy_tool ghi |
| `final_answer` | `str` | Câu trả lời cuối | synthesis ghi |
| `sources` | `list` | Nguồn được cite | synthesis ghi |
| `confidence` | `float` | Mức tin cậy | synthesis ghi |
| `workers_called` | `list` | Chuỗi workers đã chạy | mọi worker ghi |
| `worker_io_logs` | `list` | Log input/output theo contract | workers ghi |
| `latency_ms` | `int` | Thời gian xử lý | graph ghi |
| `run_id` | `str` | ID trace | graph tạo |

---

## 5. Lý do chọn Supervisor-Worker so với Single Agent (Day 08)

| Tiêu chí | Single Agent (Day 08) | Supervisor-Worker (Day 09) |
|----------|----------------------|--------------------------|
| Debug khi sai | Khó — phải đọc toàn pipeline | Dễ hơn — xem route_reason, workers_called, worker_io_logs |
| Thêm capability mới | Phải sửa prompt/flow chính | Thêm worker hoặc MCP tool riêng |
| Routing visibility | Không có | Có trace rõ cho từng nhánh |
| Test độc lập | Khó | Có thể test retrieval/policy/synthesis riêng |

**Nhóm quan sát từ thực tế lab:**

- Case `q07` đi vào `policy_tool_worker`, gọi `search_kb`, rồi synthesis kết luận đúng là không hoàn tiền cho license key/Flash Sale.
- Case `q11` đi vào `retrieval_worker`, nhưng synthesis vẫn abstain vì evidence bị nhiễu, cho thấy routing đúng chưa đủ nếu retrieval top-k còn dư tài liệu không liên quan.
- Case `q09` kích hoạt `human_review` trước khi quay về retrieval, giúp tránh bịa với mã lỗi `ERR-403-AUTH`.

---

## 6. Giới hạn và điểm cần cải tiến

1. Retrieval vẫn còn kéo theo chunks nhiễu khi query ngắn hoặc có nhiều keyword chồng nhau.
2. Policy worker vẫn dựa khá nhiều vào keyword + rule-based; phần LLM chỉ bổ sung, chưa phải classifier chuẩn.
3. Synthesis vẫn có thể trả lời sai nếu context lấy về chưa đủ sạch; cần siết citation và ưu tiên abstain hơn nữa.
