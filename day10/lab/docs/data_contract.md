# Data contract — Lab Day 10

> Bắt đầu từ `contracts/data_contract.yaml` — mở rộng và đồng bộ file này.

---

## 1. Nguồn dữ liệu (source map)

| Nguồn | Phương thức ingest | Failure mode chính | Metric / alert |
|-------|-------------------|-------------------|----------------|
| `data/docs/policy_refund_v4.txt` | Export CSV → clean → embed | Lệch version hoàn tiền 14 ngày thay vì 7 ngày, làm retrieval trả lời sai | `quarantine_records`, expectation `refund_no_stale_14d_window`, kiểm tra top-k có còn chunk stale không |
| `data/docs/hr_leave_policy.txt` | Export CSV → clean → embed | Version HR 2025 còn lẫn vào snapshot 2026, gây xung đột số ngày phép | `quarantine_records`, expectation `hr_leave_no_stale_10d_annual`, freshness log theo `latest_exported_at` |
| `data/docs/sla_p1_2026.txt` | Export CSV → clean → embed | Sai ngày hiệu lực hoặc exported_at không parse được | `cleaned_records`, `quarantine_records`, `effective_date_iso_yyyy_mm_dd` |

---

## 2. Schema cleaned

| Cột | Kiểu | Bắt buộc | Ghi chú |
|-----|------|----------|---------|
| chunk_id | string | Có | ID ổn định sau clean, dùng để upsert idempotent vào Chroma |
| doc_id | string | Có | Khóa logic tài liệu nguồn, phải nằm trong allowlist contract |
| chunk_text | string | Có | Text đã clean, không còn markup rác, chuẩn hoá refund window nếu áp dụng |
| effective_date | date | Có | Ngày hiệu lực chuẩn ISO `YYYY-MM-DD` |
| exported_at | datetime | Có | Thời điểm export nguồn, dùng làm boundary freshness |

---

## 3. Quy tắc quarantine vs drop

Record bị flag vào `artifacts/quarantine/` cùng lý do cụ thể trong cột `reason`. Pipeline **không drop im lặng**: mọi dòng bị quarantine đều được giữ để review, đối chiếu và tạo metric impact.

Quy trình merge lại:
- Data Engineer kiểm tra lý do quarantine.
- Nếu là lỗi nguồn thật, cập nhật raw export hoặc rule clean tương ứng.
- Nếu là false positive, chỉ định rõ exception trong contract và ghi lại trong report nhóm trước khi cho phép publish lại.

---

## 4. Phiên bản & canonical

Source of truth cho policy refund là `data/docs/policy_refund_v4.txt`. Mọi chunk nào còn mang dấu hiệu `14 ngày làm việc` hoặc ghi chú migration cũ phải bị sửa/quarantine trước khi embed.
