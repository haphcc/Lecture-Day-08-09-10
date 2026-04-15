# Báo Cáo Nhóm — Lab Day 10: Data Pipeline & Data Observability

**Tên nhóm:** ___________  
**Thành viên:**
| Tên | Vai trò (Day 10) | Email |
|-----|------------------|-------|
| ___ | Ingestion / Raw Owner | ___ |
| ___ | Cleaning & Quality Owner | ___ |
| ___ | Embed & Idempotency Owner | ___ |
| ___ | Monitoring / Docs Owner | ___ |

**Ngày nộp:** ___________  
**Repo:** ___________  
**Độ dài khuyến nghị:** 600–1000 từ

---

> **Nộp tại:** `reports/group_report.md`  
> **Deadline commit:** xem `SCORING.md` (code/trace sớm; report có thể muộn hơn nếu được phép).  
> Phải có **run_id**, **đường dẫn artifact**, và **bằng chứng before/after** (CSV eval hoặc screenshot).

---

## 1. Pipeline tổng quan (150–200 từ)

> Nguồn raw là gì (CSV mẫu / export thật)? Chuỗi lệnh chạy end-to-end? `run_id` lấy ở đâu trong log?

**Tóm tắt luồng:**

_________________

**Lệnh chạy một dòng (copy từ README thực tế của nhóm):**

_________________

---

## 2. Cleaning & expectation (150–200 từ)

> Baseline đã có nhiều rule (allowlist, ngày ISO, HR stale, refund, dedupe…). Nhóm thêm **≥3 rule mới** + **≥2 expectation mới**. Khai báo expectation nào **halt**.

### 2a. Bảng metric_impact (bắt buộc — chống trivial)

| Rule / Expectation mới (tên ngắn) | Trước (số liệu) | Sau / khi inject (số liệu) | Chứng cứ (log / CSV / commit) |
|-----------------------------------|------------------|-----------------------------|-------------------------------|
| refund_doc_present (halt) | `refund_rows=0` (mô phỏng lỗi mất dữ liệu refund) | `refund_rows>=1` sau khi restore cleaned snapshot | Log `expectation[refund_doc_present]` trong run sprint2 |
| exported_at_within_48h (warn) | `stale_exported_at_rows>0` trên snapshot cũ | `stale_exported_at_rows=0` khi dùng export mới hơn | Log `expectation[exported_at_within_48h]` + manifest timestamp |
| refund_no_stale_14d_window (halt) | `violations>0` khi inject `--no-refund-fix --skip-validate` | `violations=0` ở run chuẩn | So sánh log inject-bad vs sprint2 |

**Rule chính (baseline + mở rộng):**

- Các rule clean loại bỏ stale chunk, dedupe và chuẩn hóa date/exported_at trước khi validate.
- Expectation halt được đặt cho các vi phạm gây sai nghiệp vụ retrieval (mất doc refund, còn 14 ngày làm việc, doc_id rỗng).
- Expectation warn dùng cho rủi ro vận hành (snapshot quá cũ) để không chặn pipeline demo nhưng vẫn phát tín hiệu chất lượng.

**Ví dụ 1 lần expectation fail (nếu có) và cách xử lý:**

Run inject-bad với `--no-refund-fix --skip-validate` tạo `expectation[refund_no_stale_14d_window] FAIL (halt)` trong log. Cách xử lý: chạy lại pipeline chuẩn không cờ inject để rule clean sửa về `7 ngày làm việc`, expectation chuyển PASS.

---

## 3. Before / after ảnh hưởng retrieval hoặc agent (200–250 từ)

> Bắt buộc: inject corruption (Sprint 3) — mô tả + dẫn `artifacts/eval/…` hoặc log.

**Kịch bản inject:**

_________________

**Kết quả định lượng (từ CSV / bảng):**

_________________

---

## 4. Freshness & monitoring (100–150 từ)

> SLA bạn chọn, ý nghĩa PASS/WARN/FAIL trên manifest mẫu.

_________________

---

## 5. Liên hệ Day 09 (50–100 từ)

> Dữ liệu sau embed có phục vụ lại multi-agent Day 09 không? Nếu có, mô tả tích hợp; nếu không, giải thích vì sao tách collection.

_________________

---

## 6. Rủi ro còn lại & việc chưa làm

- …
