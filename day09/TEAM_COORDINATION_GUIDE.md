# 📘 Bảng Phân Chia Công Việc — Day 09: Multi-Agent RAG
*Dành cho AI Agent điều phối dự án*

---

## 1. Phân vai và Quyền sở hữu file (Roles & Ownership)
Chia dự án thành 3 vai trò độc lập để tối ưu hóa việc làm việc nhóm trên Git:

### 👤 Vai trò A: Tech Lead (Kiến trúc sư)
- **File phụ trách:** `graph.py`, `eval_trace.py`, `requirements.txt`, `.gitignore`, `contracts/`.
- **Nhiệm vụ AI cần thực hiện:**
    - Thiết lập luồng `AgentState`.
    - Viết logic định tuyến (Supervisor Routing) trong `graph.py`.
    - Đảm bảo các Worker được kết nối đúng thứ tự.
    - Chạy Pipeline để sinh ra 15-20 file Traces JSON.

### 👤 Vai trò B: AI Lead (Chuyên gia AI)
- **File phụ trách:** Thư mục `workers/` (`retrieval.py`, `policy_tool.py`, `synthesis.py`).
- **Nhiệm vụ AI cần thực hiện:**
    - Cấu hình Hybrid Search (Dense + Sparse) trong `retrieval.py`.
    - Viết logic xử lý ngoại lệ chính sách trong `policy_tool.py`.
    - Thiết kế Prompt "chống bịa đặt" và trích dẫn trong `synthesis.py`.

### 👤 Vai trò C: Eval Lead (Chuyên gia Đánh giá)
- **File phụ trách:** `mcp_server.py`, `docs/`.
- **Nhiệm vụ AI cần thực hiện:**
    - Xây dựng MCP Tools giả lập (Ticket/KB) trong `mcp_server.py`.
    - Viết báo cáo so sánh kết quả Single-Agent (Day 08) và Multi-Agent (Day 09).

---

## 2. Lộ trình thực hiện (Sprints)

| Sprint | Nội dung | Phụ trách chính |
| :--- | :--- | :--- |
| **Sprint 1** | Refactor Graph & Supervisor, Chạy Eval | Vai trò A |
| **Sprint 2** | Triển khai 3 Workers chi tiết | Vai trò B |
| **Sprint 3** | Kết nối Mock MCP Server | Vai trò C |
| **Sprint 4** | Tổng kết báo cáo | Vai trò C + Cả nhóm |

---

## 3. Danh mục sản phẩm cần nộp (Deliverables)
AI Agent cần đảm bảo kiểm tra đủ các file sau trước khi nộp bài:
1.  **Code:** `graph.py`, `mcp_server.py`, `workers/*.py`.
2.  **Hợp đồng:** `contracts/worker_contracts.yaml`.
3.  **Tài liệu:** `docs/system_architecture.md`, `docs/routing_decisions.md`, `docs/single_vs_multi_comparison.md`.
4.  **Dữ liệu:** Thư mục `artifacts/traces/` chứa các câu trả lời mẫu.
