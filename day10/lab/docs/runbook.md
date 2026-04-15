# Runbook — Lab Day 10 Data Pipeline (Incident Response)

---

## 1. Symptom: Retrieval trả về policy sai (14 ngày thay vì 7 ngày)

**User observation:**
- Agent trả lời: "Khách hàng được hoàn tiền trong **14 ngày làm việc**"
- Expected: "7 ngày làm việc"

**Impact:** Chính sách bị trả lời sai → khách phàn nàn, trust giảm

---

## 2. Detection

**Metrics chỉ ra problem:**
- `expectation[refund_no_stale_14d_window]` → **FAIL** (nếu data chứa chunk 14 ngày)
- `eval_retrieval.py` → `hits_forbidden=YES` cho `q_refund_window`
- Agent logs: "top-1 chunk chứa '14 ngày'" (trong trace context)

**Kiểm tra nhanh:**
```bash
# 1. Check freshness
python etl_pipeline.py freshness --manifest artifacts/manifests/manifest_*.json
# Result: PASS/WARN/FAIL + age_hours

# 2. Check eval
python eval_retrieval.py --out /tmp/quick_eval.csv
# Xem q_refund_window: contains_expected, hits_forbidden

# 3. Check quarantine
head -3 artifacts/quarantine/quarantine_*.csv | grep refund
```

---

## 3. Diagnosis

| Bước | Việc làm | Kết quả mong đợi |
|------|----------|------------------|
| 1 | Mở `manifest_*.json` cuối cùng → xem `run_id, cleaned_records, quarantine_records` | quarantine_records ≥ 1 (chunk 14d bị catch) |
| 2 | Mở `quarantine_*.csv` → tìm "14 ngày" | Có 1–2 dòng có reason = `stale_migration_note` hoặc `refund_no_stale_14d` |
| 3 | Mở `artifacts/cleaned/cleaned_*.csv` → kiểm tra chunk refund | Chỉ "7 ngày", không "14 ngày" |
| 4 | Check Chroma collection: `python eval_retrieval.py --top-k 10` | Top-10 không chứa "14 ngày" chunk |
| 5 | Nếu eval vẫn fail → check `run_id` trong metadata | Có chunk stale (run_id cũ) từ lần chạy trước? |

---

## 4. Root Cause Analysis

### Case A: Pipeline halt nhưng embed đã chạy (--skip-validate)
```
expectation[refund_no_stale_14d_window] FAIL
WARN: expectation failed but --skip-validate → tiếp tục embed
embed_upsert count=6 (gồm chunk 14 ngày xấu)
```
**Nguyên nhân:** Ai đó chạy `--skip-validate` để demo Sprint 3, sau đó quên rerun chuẩn  
**Fix:** `python etl_pipeline.py run --run-id recovery` (không flag, chạy clean bth)

### Case B: Freshness FAIL (data cũ)
```
freshness_check=FAIL age_hours=120.9 (5 ngày)
SLA_HOURS=24
```
**Nguyên nhân:** CSV source không được cập nhật từ DB trong 5 ngày  
**Fix:** 
- Cập nhật `FRESHNESS_SLA_HOURS` trong `.env` → 144 (6 ngày) nếu batch thực tế là daily
- Hoặc: Cập nhật CSV exported_at timestamp từ DB real-time

### Case C: Vector index stale (chứa data cũ)
```
embed_prune_removed=0 (không xoá chunk cũ!)
previous collection có chunk_id_old từ run_id=2026-04-10T08-00Z
```
**Nguyên nhân:** Embed upsert không chạy prune → vector cũ vẫn in-memory  
**Fix:** Đảm bảo `cmd_embed_internal()` chạy `col.delete(ids=drop)` trước upsert

---

## 5. Mitigation

**Nếu already in production (customer affected):**

1. **Immediate:**
   - Tạm show banner: "Policy data đang update, vui lòng refresh sau 5 phút"
   - Hoặc: Rollback Chroma collection → restore từ backup (nếu có)

2. **Rerun clean:**
   ```bash
   # SSH vào production server
   cd /app/lab
   python etl_pipeline.py run --run-id fix_refund_$(date +%s)
   # Monitor: check manifest → cleaned_records, quarantine_records
   ```

3. **Verify after:**
   ```bash
   python eval_retrieval.py --out /tmp/after_fix.csv
   # Check: q_refund_window contains_expected=YES, hits_forbidden=NO
   ```

4. **Notify:** GV + team = "Data pipeline issue fixed at 17:45 UTC" (incident duration 15 min)

---

## 6. Prevention & Guardrails

### Short-term (hiện tại lab):
1. **Expectation suite:**
   - ✅ `refund_no_stale_14d_window` — catch chunk 14 ngày
   - ✅ `hr_leave_no_stale_10d_annual` — catch chunk cũ HR
   - → Halt if fail (không cho --skip-validate ngoài demo)

2. **Freshness monitoring:**
   - ✅ `freshness_check` in pipeline log
   - → Alert (email / Slack) nếu FAIL (tỳ deployment)

3. **Eval baseline:**
   - ✅ Run `eval_retrieval.py` post-deploy để validate retrieval quality
   - Store baseline metrics (q_refund_window contains_expected MUST = YES)

### Medium-term (Day 11+):
1. **CI/CD Gate:** 
   - Pipeline MUST have `expectation PASS` trước merge code
   - Eval MUST have `hits_forbidden=NO` cho critical questions (q_refund_window, q_leave_version)

2. **Data ownership:**
   - Owner = Thành viên 1 (Data Engineer)
   - Review quarantine_records hàng ngày (SLA: nếu > baseline + 20% → alert)

3. **Vector versioning:**
   - Tag Chroma snapshots với run_id
   - Keep 2–3 versions để quick rollback

4. **Runbook drill:** 
   - Team thực tập "scenario: policy data inject error" 1 lần/tháng
   - Response time target: < 10 min từ symptom → fix

---

## 7. SLA & Owner

| Metric | Target | Owner | Alert |
|--------|--------|-------|-------|
| Freshness | ≤ 24h | Data Engineer | Email if > 24h |
| Expectation Pass | 100% | Quality Engineer | Block deploy if fail |
| Eval q_refund hits_forbidden | NO | Ops Lead | Slack if YES |
| MTTR (Mean Time To Recover) | < 15 min | On-call | Auto-escalate @ 10 min |

---

## 8. Runbook Testing Checklist

- [ ] Lab chạy `--skip-validate` intentionally → verify FAIL detected
- [ ] Lab chạy recovery (`sprint3_recovery`) → verify prune works, eval PASS
- [ ] Lab check freshness FAIL → verify log message clear
- [ ] Team can run all 6 sections (symptom, detection, diagnosis, mitigation, prevention, sla) trong < 10 min

---

**Last updated:** 15/04/2026  
**Owner:** Thành viên 3 (Observability & Ops Lead)  
**Review schedule:** Quarterly

