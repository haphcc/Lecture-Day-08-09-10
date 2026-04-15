# Phân chia công việc Nhóm (3 người) - Lab Day 10: Data Pipeline & Data Observability

Danh sách phân công này được thiết kế để đảm bảo cả 3 thành viên chia đều khối lượng công việc kỹ thuật (Code) và tài liệu (Docs / Reports), giúp tối đa hoá điểm nhóm (60đ) và điểm cá nhân (40đ).

---

## 👤 Thành viên 1: Data Engineer (Ingestion & Cleaning)
**Trọng tâm:** Xử lý dữ liệu thô (raw), làm sạch dữ liệu, và quản lý các bản ghi lỗi (quarantine).

### 🛠 Nhiệm vụ Code:
- **[Sprint 1 & 2]** Mở file `transform/cleaning_rules.py`. Viết thêm **ít nhất 3 rule làm sạch mới** (Ví dụ: chuẩn hóa format số điện thoại, lọc các version tài liệu cũ, loại bỏ mã HTML rác, v.v.).
- Chạy thử `etl_pipeline.py` để đảm bảo log sinh ra có ghi nhận chính xác số lượng `raw_records`, `cleaned_records`, và `quarantine_records`.
- Phối hợp nghiệm thu: File `cleaning_rules.py` chạy không bị lỗi và thực sự đẩy được các dòng dữ liệu xấu vào thư mục `artifacts/quarantine/`.

### 📝 Nhiệm vụ Docs/Report:
- Chỉnh sửa file `docs/data_contract.md`: Cập nhật phần Source Map (ít nhất 2 nguồn dữ liệu, failure mode, metric).
- Chỉnh sửa file `contracts/data_contract.yaml`: Điền thông tin owner và SLA.
- Viết báo cáo cá nhân: `reports/individual/ThanhVien1.md`.

---

## 👤 Thành viên 2: Quality & DB Owner (Expectations & Embed)
**Trọng tâm:** Kiểm định chất lượng dữ liệu (Data Quality) và nhúng dữ liệu (Embed) an toàn vào ChromaDB.

### 🛠 Nhiệm vụ Code:
- **[Sprint 2]** Mở file `quality/expectations.py`. Viết thêm **ít nhất 2 expectation mới** (Quy định rõ cái nào chỉ in cảnh báo `warn`, cái nào phải dừng toàn bộ tiến trình `halt`).
- Quản lý logic Embed trong `etl_pipeline.py`: Đảm bảo tính **idempotent**, tức là chạy ETL nhiều lần không bị duplicate vector trong DB. Upsert đúng `chunk_id` và xóa các ID không còn tồn tại trong list cleaned.
- Phối hợp nghiệm thu: Chạy `python etl_pipeline.py run` thành công (exit 0) với dữ liệu sạch, các expectation hoạt động đúng thiết kế.

### 📝 Nhiệm vụ Docs/Report:
- Chỉnh sửa file `docs/pipeline_architecture.md`: Vẽ/mô tả sơ đồ kiến trúc luồng dữ liệu (có thể dùng Mermaid) chỉ rõ ranh giới ingest -> clean -> embed.
- Viết báo cáo cá nhân: `reports/individual/ThanhVien2.md`.

---

## 👤 Thành viên 3: Observability & Ops Lead (Eval, Monitoring & Ops Docs)
**Trọng tâm:** Chạy test Before/After, kiểm tra độ trễ (Freshness check) và xây dựng tài liệu vận hành (Runbook).

### 🛠 Nhiệm vụ Code & Test:
- **[Sprint 3]** Giả lập tiêm dữ liệu lỗi (Inject corruption) bằng lệnh cờ `--no-refund-fix --skip-validate`.
- Chạy `eval_retrieval.py` 2 lần: 
  - Lần 1 trên dữ liệu bẩn -> Lưu `artifacts/eval/after_inject_bad.csv`
  - Lần 2 trên dữ liệu sạch -> Chuẩn hóa lưu `artifacts/eval/before_after_eval.csv`
- **[Sprint 4]** Chạy cấu hình kiểm tra Freshness thông qua lệnh `etl_pipeline.py freshness --manifest ...` để đảm bảo hệ thống check độ trễ hoạt động.
- Cuối giờ: Chạy `python grading_run.py` để sinh file JSONL chấm điểm cuối cùng.

### 📝 Nhiệm vụ Docs/Report:
- Chỉnh sửa file `docs/quality_report_template.md` (đổi thành `quality_report.md`): Điền số liệu chứng minh Retrieval bị tệ đi khi có data bẩn và tốt hơn khi data sạch.
- Chỉnh sửa file `docs/runbook.md`: Cập nhật đủ 5 mục Symptom -> Prevention, giải thích lý do PASS/WARN/FAIL cho freshness run.
- Viết báo cáo cá nhân: `reports/individual/ThanhVien3.md`.

---

## 🤝 Nhiệm vụ CHUNG (Cả nhóm cùng làm cuối ngày)

1. **Group Report (`reports/group_report.md`):** 
   - Điền chung bảng `metric_impact` để chứng minh các Rule (Thành viên 1) và Expectation (Thành viên 2) thực sự có tác động (không bị trivial - vô tác dụng).
   - Điền peer review cho 3 câu hỏi của phần E (nếu có yêu cầu).
2. **Review chéo:** Đảm bảo `artifacts/eval/grading_run.jsonl` có đủ 3 line `gq_d10_...` hợp lệ.
3. **Commit code:** Đẩy code lên nhánh chính trước **18:00** (Pipeline code, rules, yaml, csv, JSONL, các file `.md` trong `docs/`). Các file report cá nhân thường có thể nộp muộn hơn tùy luật của Giảng viên.