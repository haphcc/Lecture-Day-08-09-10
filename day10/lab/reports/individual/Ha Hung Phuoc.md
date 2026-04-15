# Báo Cáo Cá Nhân — Lab Day 10: Data Pipeline & Observability

**Họ và tên:** Ha Hung Phuoc
**Vai trò:** Ingestion / Cleaning / Quarantine  
**Ngày nộp:** 2026-04-15  
**Run ID:** `sprint1`

## 1. Tôi phụ trách phần nào?

Tôi phụ trách tầng ingest/clean trong file [transform/cleaning_rules.py](../../transform/cleaning_rules.py), đồng thời cập nhật source map ở [docs/data_contract.md](../../docs/data_contract.md) và owner/SLA trong [contracts/data_contract.yaml](../../contracts/data_contract.yaml). Mục tiêu của tôi là làm cho export raw từ `data/raw/policy_export_dirty.csv` đi qua pipeline theo cách có kiểm soát: dòng bẩn phải đi vào quarantine, dòng sạch phải ra cleaned CSV, và log phải phản ánh đúng `raw_records`, `cleaned_records`, `quarantine_records`.

Tôi chạy pipeline bằng `python etl_pipeline.py run --run-id sprint1` và kiểm tra trực tiếp các artifact sinh ra ở `artifacts/cleaned/cleaned_sprint1.csv`, `artifacts/quarantine/quarantine_sprint1.csv`, và `artifacts/manifests/manifest_sprint1.json`.

## 2. Một quyết định kỹ thuật

Tôi chọn xử lý các bản ghi nghi stale/migration bằng quarantine thay vì auto-fix im lặng. Cụ thể, tôi thêm rule bắt `stale_migration_note` cho dòng có ghi chú kiểu “bản sync cũ policy-v3 — lỗi migration”. Lý do là những dấu hiệu này không chỉ là lỗi format; nó là tín hiệu nguồn dữ liệu đang trộn version cũ vào snapshot mới. Nếu tôi tự sửa text rồi cho đi tiếp, pipeline sẽ che mất sự cố nguồn và làm sai lineage. Với dữ liệu Day 10, việc giữ ranh giới sạch giữa clean và quarantine quan trọng hơn việc “cứ làm cho qua”.

Tôi cũng chuẩn hoá `chunk_text` trước khi dedupe/embed để loại markup/control chars rác và normalize `exported_at` sang ISO hợp lệ. Cách này giữ idempotency và giảm rủi ro vector store nhận dữ liệu nhiễu.

## 3. Một lỗi hoặc anomaly đã xử lý

Anomaly rõ nhất là dòng raw `chunk_id=3` trong `policy_export_dirty.csv`: nội dung hoàn tiền ghi 14 ngày làm việc nhưng kèm ghi chú migration cũ. Sau khi thêm rule mới, dòng này bị đẩy vào quarantine với reason `stale_migration_note`. Kết quả run thật là `raw_records=10`, `cleaned_records=5`, `quarantine_records=5`.

Các reason khác trong `artifacts/quarantine/quarantine_sprint1.csv` là `duplicate_chunk_text` (dòng 2), `missing_effective_date` (dòng 5), `stale_hr_policy_effective_date` (dòng 7), và `unknown_doc_id` (dòng 9). Điều này cho thấy pipeline không chỉ lọc theo một lỗi duy nhất mà xử lý được nhiều failure mode khác nhau.

## 4. Bằng chứng trước / sau

Trước clean, raw export có 10 dòng. Sau clean, tôi còn 5 dòng và 5 dòng bị quarantine. Cụ thể, cleaned CSV chỉ còn các bản ghi canonical: refund 7 ngày, SLA P1, FAQ khóa tài khoản, HR 12 ngày phép năm 2026, và FAQ đổi mật khẩu.

Log thật từ run:

```text
run_id=sprint1
raw_records=10
cleaned_records=5
quarantine_records=5
expectation[refund_no_stale_14d_window] OK (halt) :: violations=0
freshness_check=FAIL {"latest_exported_at": "2026-04-10T08:00:00", "age_hours": 119.199, "sla_hours": 24.0, "reason": "freshness_sla_exceeded"}
```

Điểm quan trọng là freshness FAIL ở đây là đúng kỳ vọng vì snapshot mẫu quá cũ so với SLA 24 giờ. Nó chứng minh boundary publish/freshness có tác dụng thật, không phải log trang trí.

## 5. Cải tiến tiếp theo

Nếu có thêm 2 giờ, tôi sẽ thêm summary log theo reason cho quarantine, ví dụ đếm riêng `stale_migration_note`, `duplicate_chunk_text`, `unknown_doc_id`. Việc này sẽ giúp bảng `metric_impact` của nhóm dễ điền hơn và giúp reviewer nhìn nhanh được rule nào tạo ra tác động lớn nhất.
