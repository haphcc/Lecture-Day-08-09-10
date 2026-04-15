# Báo Cáo Nhóm — Lab Day 10: Data Pipeline & Data Observability

**Tên nhóm:** Day 10 - Data Pipeline & Observability  
**Thành viên:**
| Tên | Vai trò (Day 10) | Contribution |
|-----|------------------|-------|
| Phước | Data Engineer / Ingestion & Cleaning Owner | etl_pipeline.py, cleaning_rules.py, data_contract |
| Hoài | Quality & Embed Owner | expectations.py, embed idempotency, pipeline_architecture |
| Huyền | Observability & Ops Lead | eval_retrieval.py, freshness_check, quality_report, runbook |

**Ngày nộp:** 15/04/2026  
**Repo:** `https://github.com/haphcc/Lecture-Day-08-09-10.git`  
**Word count:** ~850 từ

---

> **Nộp tại:** `reports/group_report.md`  
> **Deadline commit:** 18:00 UTC (code bắt buộc); report có thể muộn hơn nếu được phép.  
> **Chứng cứ:** run_id (sprint3_clean, inject_strong, sprint3_recovery), before_after_eval.csv, manifests JSON.

---

## 1. Pipeline tổng quan (150–200 từ)

> Nguồn raw là gì (CSV mẫu / export thật)? Chuỗi lệnh chạy end-to-end? `run_id` lấy ở đâu trong log?

**Tóm tắt luồng:**

Pipeline Day 10 xử lý export CSV từ 5 tài liệu chính (refund policy, IT helpdesk, HR leave, SLA P1, legacy catalog) chứa ~10 chunks raw với các lỗi điển hình (duplicate, stale date, sai format, policy cũ, empty chunk, unknown doc_id). 

Luồng xử lý: **ingest → clean → validate → embed → publish (idempotent upsert + prune vector cũ)**.

- **Ingestion:** Load `data/raw/policy_export_dirty.csv` (hoặc `policy_export_inject_strong.csv` cho Sprint 3 demo)
- **Cleaning:** Apply ≥3 rule mới (dedupe, date normalization, doc_id allowlist, refund window fix 14→7 ngày, stale HR/migration detect)
- **Validation:** Expectation suite halt (5 rule Critical) + warn (1 rule informational)
- **Embed:** Chroma collection `day10_kb`, upsert idempotent chunk_id, prune ID cũ không còn trong cleaned set
- **Publish:** Manifest JSON ghi run_id + metrics (raw/cleaned/quarantine counts) + freshness status

**Lệnh chạy pipeline chuẩn (từ README thực tế):**

```bash
python etl_pipeline.py run --run-id sprint3_recovery
# Output: artifacts/logs/run_sprint3_recovery.log, manifest, cleaned/quarantine CSV, embed upsert
```

**Lệnh inject corruption (Sprint 3):**

```bash
python etl_pipeline.py run --raw data/raw/policy_export_inject_strong.csv \
  --run-id inject_strong --no-refund-fix --skip-validate
# Output: dữ liệu xấu vào Chroma (14 ngày refund), eval sẽ fail để chứng minh
```

---

## 2. Cleaning & expectation (150–200 từ)

> Baseline đã có nhiều rule (allowlist, ngày ISO, HR stale, refund, dedupe…). Nhóm thêm **≥3 rule mới** + **≥2 expectation mới**. Khai báo expectation nào **halt**.

### 2a. Bảng metric_impact (bắt buộc — chống trivial)

| Rule / Expectation (tên) | Trước (baseline) | Sau (sprint3_recovery) | Sau (inject_strong) | Tác động | Chứng cứ |
|---|---|---|---|---|---|
| **rule_fix_refund_14_to_7** (cleaning) | 14 ngày (baseline error) | 7 ngày ✅ | 14 ngày (–no-refund-fix) | Quarantine stale migration chunk | `artifacts/quarantine/quarantine_sprint3_*.csv` |
| **expectation[refund_no_stale_14d_window]** (halt) | PASS (clean data) | PASS ✅ | **FAIL** (2 violations) | Phát hiện chunk 14d | Log `expectation[refund_no_stale_14d_window] FAIL` trong inject_strong |
| **expectation[hr_leave_no_stale_10d_annual]** (halt) | PASS | PASS ✅ | **FAIL** (1 violation) | Loại HR 2025 (10d) | Log `expectation[hr_leave_no_stale_10d_annual] FAIL` |
| **expectation[exported_at_within_48h]** (warn) | FAIL (5 ngày cũ) | FAIL ⚠️ | FAIL ⚠️ | CSV mẫu exported 5 ngày trước (mong đợi) | All manifests: `age_hours=120.9 > SLA 24h` |
| **rule_dedupe_chunk_text** (cleaning) | 2 duplicate chunks | 0 duplicate → quarantine | 1 duplicate (giữ lại sla_p1) | Tăng cleaned quality | `quarantine_sprint3_clean.csv`: row 2 (duplicate) |
| **expectation[no_empty_doc_id]** (halt) | PASS (loại empty chunks) | PASS ✅ | PASS ✅ | Bắt chunk_text rỗng | Log: `empty_doc_id_count=0` |
| **rule_hr_versioning_cutoff_from_config** (cleaning) | cutoff=2026-01-01 → giữ HR `2026-02-01` | `distinction-d-default`: cleaned=5, quarantine=5 | `distinction-d-cutoff` (ENV=2026-03-01): cleaned=4, quarantine=6 | Đổi quyết định clean chỉ bằng config/env, không sửa code hard-code | `manifest_distinction-d-default.json`, `manifest_distinction-d-cutoff.json`, `quarantine_distinction-d-cutoff.csv` |

**Baseline rules (không thay đổi, chỉ ghi chú):**
- `rule_normalize_effective_date`: Chuẩn ISO YYYY-MM-DD
- `rule_quarantine_stale_migration`: Loại chunk có ghi chú lỗi "bản sync cũ policy-v3"
- `rule_allowlist_doc_id`: Loại doc_id lạ (legacy_catalog_xyz_zzz)

**Expectation bắt buộc & mức severity:**
- 5 rules **halt** (dừng pipeline nếu vi phạm, trừ `--skip-validate`)
- 1 rule **warn** (chỉ thông báo, không chặn)

**Ví dụ 1 lần expectation fail + fix:**

Run `inject_strong` với `--no-refund-fix --skip-validate`:
```
expectation[refund_no_stale_14d_window] FAIL (halt) :: violations=2
```
→ Chạy `sprint3_recovery` (không cờ): cleaning rule `fix_refund_14_to_7` sửa chunk, expectation PASS, eval metric `q_refund_window` chuyển từ NO → YES.

---

## 3. Before / after ảnh hưởng retrieval hoặc agent (200–250 từ)

> Bắt buộc: inject corruption (Sprint 3) — mô tả + dẫn `artifacts/eval/…` hoặc log.

**Kịch bản inject:**

Sprint 3 intentional inject: Load `data/raw/policy_export_inject_strong.csv` (có chunk refund 14 ngày, duplicate sla_p1, empty chunk, stale HR 10d) với `--no-refund-fix --skip-validate`. Mục đích: chứng minh pipeline có thể phát hiện dữ liệu xấu thông qua eval metric `hits_forbidden` và expectation FAIL.

**Kết quả định lượng (từ CSV eval + log):**

| Metric / Question | Before (sprint3_clean) | After (inject_strong) | Delta | Interpretation |
|---|---|---|---|---|
| **q_refund_window** | contains_expected=YES, hits_forbidden=NO | contains_expected=NO, hits_forbidden=YES ✗ | −1 retrieval point | Dữ liệu xấu (14d) vượt lên top-1, eval phát hiện "chunk 14 ngày làm việc" ở top-k |
| **q_leave_version** | contains_expected=YES, hits_forbidden=NO, top1_expected=YES | contains_expected=YES, hits_forbidden=NO, top1_expected=YES ✓ | 0 (không bị ảnh hưởng) | Rule HR mạnh → quarantine chunk 10d cũ, chỉ 12d mới được embed |
| **q_p1_sla** | contains_expected=YES, hits_forbidden=NO | contains_expected=YES, hits_forbidden=NO ✓ | 0 | Duplicate sla_p1 bị loại, chunk gốc vẫn là tốt |
| **Overall retrieval quality** | 4/4 PASS (100%) | 3/4 PASS (75%) | −25% | q_refund fail chứng minh obs hoạt động |

**File chứng cứ:**
- `artifacts/eval/before_after_eval.csv` — 4 questions trên dữ liệu sạch
- `artifacts/eval/after_inject_strong.csv` — 4 questions trên dữ liệu xấu (q_refund FAIL)
- Manifest: `artifacts/manifests/manifest_sprint3_recovery.json` (6 chunks loại bỏ cũ), `artifacts/manifests/manifest_inject_strong.json` (embed xấu)

---

## 4. Freshness & monitoring (100–150 từ)

> SLA bạn chọn, ý nghĩa PASS/WARN/FAIL trên manifest mẫu.

**Freshness check result:**

Tất cả manifest từ 3 run (sprint3_clean, inject_strong, sprint3_recovery) đều cho kết quả **FAIL** với SLA_HOURS=24h mặc định:

```
Status: FAIL
latest_exported_at: 2026-04-10T08:00:00 (CSV mẫu)
age_hours: 120.9 (5 ngày)
SLA_HOURS: 24
reason: freshness_sla_exceeded
```

**Giải thích:**
- CSV mẫu có `exported_at = 2026-04-10T08:00:00`, hiện tại ~2026-04-15T16:30:00 → tuổi dữ liệu **5 ngày > 24h SLA**
- Đây là **bình thường** vì dữ liệu mẫu giả định là export cách đây 5 ngày (hôm thứ 2 tuần trước)
- **FAIL không phải lỗi pipeline**, mà chứng minh freshness check hoạt động
- **Production mitigation:** Cập nhật `FRESHNESS_SLA_HOURS=144` (6 ngày) nếu batch daily, hoặc refresh CSV với timestamp hiện tại

**Runbook giải thích:**
File `docs/runbook.md` Mục 3 (Freshness Check FAIL) ghi rõ: nếu tuổi dữ liệu quá cũ, tùy chọn là (a) cập nhật SLA, (b) cập nhật source CSV, (c) tạm show banner cho user.

---

## 5. Liên hệ Day 09 (50–100 từ)

> Dữ liệu sau embed có phục vụ lại multi-agent Day 09 không? Nếu có, mô tả tích hợp; nếu không, giải thích vì sao tách collection.

**Tích hợp:**

Pipeline Day 10 embed dữ liệu sạch vào collection `day10_kb` trong Chroma DB cùng instance với Day 09. **Không ghép trực tiếp** với `day09_kb` collection vì:

1. **Data provenance:** Day 09 dùng corpus static (5 docs text), Day 10 xử lý export CSV (chunks cleaned → embed riêng)
2. **Idempotency:** Day 10 có logic prune vector ID cũ + upsert, giúp tái chạy pipeline an toàn; Day 09 có thể khác quy trình
3. **Observability:** Freshness check + expectation suite của Day 10 cần metric riêng, tránh "bẩn" với Day 09 lineage

**Khả năng mở rộng (Phase 2):**
Nếu agent Day 09 muốn truy vấn dữ liệu policy cleaned từ Day 10, có thể:
- Query cả 2 collection (`day09_kb` + `day10_kb`)
- Merge retrieval results + dedupe (theo doc_id)
- Lựa chọn rank/filter dựa trên metadata (run_id, effective_date)

Hiện tại Day 10 tập trung vào **data layer quality** (pipeline, cleaning, observability), chuẩn bị nền tảng để Day 11 tích hợp agent + orchestration tối ưu.

---

## 6. Rủi ro còn lại & việc chưa làm

### Rủi ro hiện tại:
- **CSV mẫu quá cũ (5 ngày):** Freshness FAIL là mong đợi, nhưng nếu production dùng real export thì cần daily batch hoặc webhook update
- **Embed vector tidak track versioning:** Chỉ dùng upsert + prune, không keep version history. Rollback sẽ mất mát → có thể lưu snapshot manifest cũ để điều tra

### Việc chưa làm (ngoài scope):
- **LLM-judge eval:** Hiện chỉ keyword match. Có thể mở rộng dùng OpenAI API để semantic grading
- **Freshness 2-boundary:** Chỉ check export timestamp, chưa check publish boundary (khi nào vector được serve)
- **Metric dashboard:** Không có UI/script để plot quarantine_records, expectation_fail_rate qua các run
- **Alert integration:** Chưa tích hợp email/Slack khi freshness FAIL hoặc expectation halt

### Next steps (Day 11+):
1. Mở rộng versioning config cho nhiều doc_id hơn (không chỉ HR policy)
2. Freshness 2-boundary (log khi publish xong)
3. Metric aggregation → CSV trend file
4. Agent orchestration (dùng collection day10_kb)

---

## 7. Peer Review — 3 câu hỏi từ Phần E Slide

> Nếu slide có phần E đặt 3 câu hỏi cho nhóm tự đánh giá, ghi câu trả lời ở đây.

**Q1: Pipeline của bạn có **idempotent** không? (có thể chạy 2 lần không bị phình vector?)** 
✅ **Trả lời:** Có. Embed logic dùng `col.upsert(ids=chunk_id, ...)` (không `insert`), nên rerun sẽ overwrite vector cũ. Thêm logic prune: nếu chunk_id không còn trong cleaned set, xoá khỏi collection. Log `embed_prune_removed=6` trong `manifest_sprint3_recovery.json` chứng minh.

**Q2: Sau khi "tiêm lỗi" (inject corruption), bạn phát hiện nó qua cách nào?**
✅ **Trả lời:** 2 cách:
- *Expectation suite:* `expectation[refund_no_stale_14d_window] FAIL` (halt) khi inject data có chunk 14 ngày
- *Eval retrieval:* `hits_forbidden=YES` cho `q_refund_window` (scan top-k chunk tìm keyword "14 ngày làm việc")

**Q3: Freshness check của bạn trả về FAIL. Đó có phải lỗi không?**
✅ **Trả lời:** Không. CSV mẫu `exported_at=2026-04-10`, hiện tại ~2026-04-15 → 5 ngày > 24h SLA → mong đợi. Production: cập nhật SLA hoặc source CSV. Runbook ghi chi tiết mitigation (giải thích trong `docs/runbook.md` Mục 3).

---
