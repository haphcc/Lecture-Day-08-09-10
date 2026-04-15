# Individual Report — Thành viên 3: Observability & Ops Lead

**Tên:** Thành viên 3  
**Ngày nộp:** 15/04/2026  
**Vai trò:** Observability & Ops Lead  
**Word count:** ~650 từ

---

## 1. Phần Phụ trách Cụ thể

### Files & Functions chính:
- **`eval_retrieval.py`** — Script eval before/after retrieval quality bằng keyword matching
  - Function `main()` → query Chroma collection, tính metrics `contains_expected`, `hits_forbidden`, `top1_doc_expected`
  - Output: CSV với 8 cột (question_id, question, top1_doc_id, contains_expected, hits_forbidden, ...)

- **`monitoring/freshness_check.py`** — Module kiểm tra tuổi dữ liệu
  - Function `check_manifest_freshness()` → đọc manifest JSON, so sánh `latest_exported_at` với hiện tại
  - Trả về status (PASS/WARN/FAIL) + detail dict

- **`docs/quality_report.md`** — Quality report tổng hợp
  - Section 1: Tóm tắt số liệu 3 pipeline (clean, inject, recovery)
  - Section 2–4: Before/after retrieval + freshness + corruption inject
  - Section 5–6: Hạn chế & kết luận

- **`docs/runbook.md`** — Incident response guide
  - 6 mục: Symptom, Detection, Diagnosis, Root Cause, Mitigation, Prevention
  - 8 checklist items để test runbook

### Artifacts tạo ra:
- `artifacts/eval/before_after_eval.csv` — Eval dữ liệu sạch (5 rows + header)
- `artifacts/eval/after_inject_strong.csv` — Eval dữ liệu inject (5 rows + header)
- `artifacts/manifests/manifest_inject_strong.json` — Manifest tiêm xấu
- `artifacts/manifests/manifest_sprint3_recovery.json` — Manifest phục hồi

---

## 2. Một Quyết định Kỹ thuật

### Quyết định: Scan toàn bộ top-k chunks cho metric `hits_forbidden`

**Chi tiết:** Trong `eval_retrieval.py`, tính `bad_forb` bằng cách scan tất cả chunks trong top-k (không chỉ top-1):
```python
blob = " ".join(docs).lower()  # Ghép tất cả top-k chunks
forbidden = [x.lower() for x in q.get("must_not_contain", [])]
bad_forb = any(m in blob for m in forbidden) if forbidden else False
```

**Lý do:**
1. **Phát hiện "publish boundary violation":** Có thể top-1 chunk đúng (7 ngày), nhưng top-2/3 chứa chunk stale (14 ngày). Nếu agent context ghép tất cả top-3 chunks, user nhìn thấy cả hai → nhầm lẫn.
2. **Tuân theo tinh thần Observability (Slide Day 10):** Không chỉ check "đầu ra có đúng không", mà còn "context quanh đó có bẩn không".
3. **Production-ready:** Thực tế, RAG systems thường dùng 3–5 chunks làm context; một chunk stale trong top-3 vẫn là lỗi.

**Cơ sở:** Slide Day 10 Phần 3 nhấn mạnh "publish boundary" — ranh giới nào chunk được phép serve, nào bị quarantine (các lớp dữ liệu).

**Kết quả:** 
- Khi inject_strong (có chunk 14 ngày), `hits_forbidden=TRUE` cho `q_refund_window`
- Chứng minh: dữ liệu xấu được phát hiện
- Nếu dùng top-1 only, có thể miss violation (vì semantic embedding có thể rank 14-day chunk top-2)

---

## 3. Sự cố & Anomaly + Fix

### Anomaly phát hiện: Eval inject_strong không tệ như kỳ vọng

**Hiện tượng:** Lần đầu chạy `python eval_retrieval.py --out after_inject_strong.csv`, mong đợi tất cả 4 câu hỏi đều `contains_expected=NO` hoặc có nhiều `hits_forbidden=YES`. Kết quả: chỉ `q_refund_window` fail, 3 câu khác vẫn pass.

**Nguyên nhân:** 
- File `inject_strong` chỉ có chunk 14 ngày từ row 1 (không có "ghi chú lỗi"), nên cleaning rule `refund_no_stale_14d_window` **không quarantine được**
- Chunk 14 ngày được embed vào Chroma
- Nhưng cleaning rule `hr_leave_no_stale_10d_annual` đủ mạnh → loại bỏ chunk HR 10d vào quarantine
- Nên `q_leave_version` vẫn pass (chỉ chunk 12d được embed)

**Fix thực hiện:**
1. Thêm comment vào `after_inject_strong.csv`: "Note: chunk 14d không bị quarantine trong inject_strong (không có lỗi migration ghi chú) → simulate real-world case của 'good-looking bad data'"
2. Cập nhật quality_report.md phần "After Inject": giải thích tại sao `q_leave_version` vẫn pass (rule mạnh)
3. Nhận xét trong report: "Điều này chứng minh rule `hr_leave_no_stale_10d_annual` hiệu quả; nhưng rule refund cần thêm pattern matching (không chỉ ghi chú)" → có thể là merit improvement

**Bài học:** Anomaly không phải bug, mà là kỳ vọng sai. Testing giúp tinh chỉnh rule hiệu quả hơn.

---

## 4. Before/After Evidence

### Data Points từ CSV Eval

**Before Inject (sprint3_clean):**
```
q_refund_window:      contains_expected=YES, hits_forbidden=NO ✓
q_p1_sla:             contains_expected=YES, hits_forbidden=NO ✓
q_lockout:            contains_expected=YES, hits_forbidden=NO ✓
q_leave_version:      contains_expected=YES, hits_forbidden=NO, top1_doc_expected=YES ✓✓
```

**After Inject (inject_strong):**
```
q_refund_window:      contains_expected=NO,  hits_forbidden=YES ✗
q_p1_sla:             contains_expected=YES, hits_forbidden=NO ✓
q_lockout:            contains_expected=YES, hits_forbidden=NO ✓
q_leave_version:      contains_expected=YES, hits_forbidden=NO, top1_doc_expected=YES ✓✓
```

**Chỉ tiêu quan trọng nhất:** `q_refund_window` chuyển từ PASS → FAIL khi inject chunk 14 ngày
- Delta: `contains_expected` YES → NO (−1 point)
- Delta: `hits_forbidden` NO → YES (+1 alert)

### Freshness Check
- **Status:** FAIL (mong đợi, dữ liệu cũ 5 ngày)
- **Giải thích:** Trong runbook + quality_report

---

## 5. Cải tiến 2 giờ cuối (nếu còn thời gian)

### Thực hiện được:
✅ Viết quality_report.md đầy đủ 6 section  
✅ Viết runbook.md với 6 scenario + SLA table + checklist  
✅ Comment code etl_pipeline.py thêm UTF-8 fix  
✅ Tạo eval artifacts before/after (2 CSV files)

### Không kịp/ngoài scope:
- Mở rộng eval thêm LLM-judge (cần setup OpenAI API)
- Great Expectations migration (hiện dùng function-based expectations tạm được)
- Freshness 2-boundary (ingest + publish watermark) — require thêm logging

### Gợi ý next sprint:
- Thêm `metrics/` folder để track quarantine_records, expectation_fail_rate qua các run
- Implement alert: nếu freshness FAIL → send Slack message
- Add `test_eval_grading.py` để automation grading_run.py validation

---

## 6. Kết luận

Vai trò Observability & Ops Lead hoàn thành:
- ✅ Chạy eval before/after (2 file CSV)
- ✅ Inject corruption (inject_strong scenario)
- ✅ Freshness check (FAIL status + giải thích)
- ✅ Viết quality_report + runbook bắt buộc
- ⏳ Grading sẽ chạy sau 17:00

**Khoảng tự đánh giá cá nhân:** 30–35/40 điểm (chưa có bonus, chưa chạy grading)

---

**Signed:** Thành viên 3  
**Date:** 15/04/2026 ~ 17:15 UTC

