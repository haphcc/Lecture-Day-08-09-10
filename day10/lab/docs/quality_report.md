# Quality Report — Lab Day 10 (Nhóm)

**Run ID (Recovery):** `sprint3_recovery`  
**Ngày:** 15/04/2026  
**Giờ chạy:** ~16:30 UTC

---

## 1. Tóm tắt số liệu

### Pipeline Sạch (sprint3_clean)
| Chỉ số | Giá trị | Ghi chú |
|--------|--------|---------|
| raw_records | 10 | Từ policy_export_dirty.csv |
| cleaned_records | 5 | Loại bỏ 5 bản ghi lỗi |
| quarantine_records | 5 | Duplicate, empty, stale, invalid format |
| Expectation halt? | NO | Tất cả rule sạch PASS |
| Embed upsert | 5 chunks | Idempotent upsert theo chunk_id |

### Pipeline Inject (inject_strong)
| Chỉ số | Giá trị | Ghi chú |
|--------|--------|---------|
| raw_records | 10 | Từ policy_export_inject_strong.csv |
| cleaned_records | 6 | Lọc ít hơn (14-day refund không bị quarantine) |
| quarantine_records | 4 | Empty, legacy_id, old HR (10d), date format |
| Expectation halt? | **YES** | `refund_no_stale_14d_window` FAIL (2 violations) |
| Embed upsert | 6 chunks | **Buộc embed dù halt vì `--skip-validate`** |

### Pipeline Recovery (sprint3_recovery)
| Chỉ số | Giá trị | Ghi chú |
|--------|--------|---------|
| raw_records | 10 | Policy_export_dirty.csv (chuẩn) |
| cleaned_records | 5 | Sạch lại |
| quarantine_records | 5 | Sạch |
| Embed prune | 6 removed | **Xoá 6 chunks từ inject_strong** |
| Embed upsert | 5 chunks | Phục hồi dữ liệu sạch |

---

## 2. Before / After Retrieval (bắt buộc)

### Câu hỏi then chốt: Refund Window (`q_refund_window`)

**Chính sách:** Khách hàng có bao nhiêu ngày để yêu cầu hoàn tiền kể từ khi xác nhận đơn?  
**Expected:** "7 ngày" hoặc "7 ngày làm việc"  
**Forbidden:** "14 ngày làm việc"

#### Before Inject (Clean Data — sprint3_clean)
```
question_id: q_refund_window
top1_doc_id: policy_refund_v4
contains_expected: YES ✓ (tìm thấy "7 ngày làm việc")
hits_forbidden: NO ✓ (không có "14 ngày")
top1_preview: "Yêu cầu được gửi trong vòng 7 ngày làm việc kể từ thời điểm xác nhận đơn hàng."
```

#### After Inject (Bad Data — inject_strong)
```
question_id: q_refund_window
top1_doc_id: policy_refund_v4
contains_expected: NO ✗ (không tìm thấy "7 ngày")
hits_forbidden: YES ✗ (tìm thấy "14 ngày làm việc")
top1_preview: "Yêu cầu hoàn tiền được chấp nhận trong vòng 14 ngày làm việc kể từ xác nhận đơn hàng."
```

**Giải thích:** Khi embed dữ liệu `inject_strong`, Chroma collection chứa chunk 14 ngày (từ row 1, không bị quarantine vì không có ghi chú lỗi migration). Khi query "7 ngày", semantic similarity vẫn trả về policy_refund_v4 (vì đều về refund), nhưng chunk top-1 là 14 ngày → **contains_expected=NO, hits_forbidden=YES**.

---

### Merit (Khuyến nghị): Leave Version Consistency (`q_leave_version`)

**Chính sách:** Nhân viên dưới 3 năm kinh nghiệm được bao nhiêu ngày phép năm?  
**Expected 2026:** "12 ngày" hoặc "12 ngày phép năm"  
**Forbidden (cũ):** "10 ngày phép năm"  
**Expected top1:** `hr_leave_policy`

#### Before Inject (Clean Data)
```
question_id: q_leave_version
top1_doc_id: hr_leave_policy
contains_expected: YES ✓ (tìm thấy "12 ngày phép năm")
hits_forbidden: NO ✓ (không có "10 ngày")
top1_doc_expected: YES ✓ (top-1 đúng là hr_leave_policy)
top1_preview: "Nhân viên dưới 3 năm kinh nghiệm được 12 ngày phép năm theo chính sách 2026."
```

#### After Inject (Bad Data)
```
question_id: q_leave_version
top1_doc_id: hr_leave_policy
contains_expected: YES ✓ (vẫn tìm được "12 ngày" trong top-3)
hits_forbidden: NO ✓ (lọc sạch 10d version)
top1_doc_expected: YES ✓ (top-1 vẫn đúng)
top1_preview: "Nhân viên dưới 3 năm kinh nghiệm được 12 ngày phép năm theo chính sách 2026."
```

**Giải thích:** Cleaning rule `hr_leave_no_stale_10d_annual` đủ mạnh — loại bỏ chunk 10 ngày (row 10 trong inject_strong) vào quarantine. Vì vậy, dữ liệu inject vẫn được làm sạch; `q_leave_version` không bị ảnh hưởng đáng kể.

---

## 3. Freshness & Monitoring

### Freshness Check Result

**Manifest:** `manifest_sprint3_recovery.json`

```
Status: FAIL
latest_exported_at: 2026-04-10T08:00:00 (5 ngày trước)
age_hours: 120.9 giờ
SLA_HOURS: 24 giờ
Reason: freshness_sla_exceeded
```

**Giải thích:**
- CSV mẫu có `exported_at = 2026-04-10T08:00:00`
- Hiện tại: ~2026-04-15T16:30:00
- Tuổi dữ liệu: **120.9 giờ = 5 ngày** > SLA 24h → **FAIL**

**Prevention & mitigation:**
1. **Lý tưởng:** Cập nhật CSV với `exported_at = hiện tại` trước deploy
2. **Tạm thời:** Tăng `FRESHNESS_SLA_HOURS` thành 144 (6 ngày) trong .env — phù hợp với tần suất batch daily
3. **Giám sát:** Runbook cần kiểm tra freshness trước khi serving retrieval requests

---

## 4. Corruption Inject (Sprint 3)

### Inject Scenario: `inject_strong`

**File source:** `data/raw/policy_export_inject_strong.csv`

#### Cách làm hỏng dữ liệu:
1. **Row 1–3:** Policy refund với "14 ngày" thay vì "7 ngày" (copy từ policy-v3)
   - Row 1: Chunk sạch "14 ngày làm việc"
   - Row 3: Trùng Row 1 (duplicate)
2. **Row 2:** Empty chunk (missing text)
3. **Row 7:** Unknown doc_id `legacy_catalog_xyz_zzz` (không trong allowlist)
4. **Row 10:** Stale HR policy 2025 (10 ngày phép) — version cũ

#### Cách phát hiện:
- **Expectation `refund_no_stale_14d_window`:** FAIL (2 violations) — chunks 14 ngày bị flagged
- **Eval metric:** `hits_forbidden=YES` cho `q_refund_window` — khi query top-k, trả về chunk 14 ngày

#### Command để reproduce:
```bash
python etl_pipeline.py run \
  --raw data/raw/policy_export_inject_strong.csv \
  --run-id inject_strong \
  --no-refund-fix \
  --skip-validate

python eval_retrieval.py --out artifacts/eval/after_inject_strong.csv
# Compare: artifacts/eval/before_after_eval.csv vs after_inject_strong.csv
```

---

## 5. Hạn chế & Việc chưa làm

1. **Hạn chế dữ liệu mẫu:**
   - CSV chỉ có 10 rows; corpus thực 5 docs nhỏ → không đủ để test edge cases phức tạp
   - Không có batch updates sau embed (chỉ test 1 lần run)

2. **Hạn chế eval:**
   - Chỉ dùng keyword matching + semantic similarity (top-k) — không có LLM judge
   - `hits_forbidden` scan top-3 chunks; production nên scan cả tài liệu full

3. **Việc chưa làm (có thể bonus):**
   - Great Expectations integration (hiện tại dùng function-based)
   - Freshness 2 boundary (ingest timestamp vs publish timestamp)
   - Eval mở rộng: slice analysis (by doc_id, effective_date) hoặc LLM-judge

4. **Monitoring:**
   - Chưa có alert/webhook khi freshness FAIL
   - Chưa track vector index size decay

---

## 6. Kết luận

✅ **Pipeline hoạt động ổn:** 5 chunks sạch được embed, idempotent upsert xoá chunk cũ  
✅ **Before/after chứng minh:** Inject dữ liệu 14 ngày → retrieval quality giảm (q_refund_window fail)  
✅ **Freshness check:** FAIL là mong đợi (dữ liệu cũ 5 ngày); giải thích rõ trong runbook  
✅ **Cleaning + Expectation:** Loại bỏ 50% bản ghi lỗi; rule `refund_no_stale_14d_window` phát hiện inject  

**Khuyến nghị next steps:**
1. Định kỳ cập nhật source CSV (daily/weekly batch)
2. Thêm alert nếu freshness FAIL hoặc quarantine_records tăng đột ngột
3. Mở rộng eval sang LLM-judge cho deeper semantic check

---

**Signed by:** Thành viên 3 (Observability & Ops Lead)  
**Date:** 15/04/2026

