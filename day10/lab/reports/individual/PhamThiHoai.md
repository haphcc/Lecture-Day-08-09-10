# Báo Cáo Cá Nhân - Lab Day 10: Data Pipeline & Observability

**Họ và tên:** Phạm Thị Hoài 
**Vai trò:** Quality & DB Owner (Expectation + Embed Idempotency)  
**Ngày nộp:** 2026-04-15

## 1. Tôi phụ trách phần nào?

Trong bài Lab Day 10, tôi phụ trách 2 hạng mục chính: kiểm soát chất lượng dữ liệu bằng expectation và xác minh cơ chế embed idempotent cho ChromaDB. Ở phần quality, tôi bổ sung hai expectation mới trong `quality/expectations.py` gồm:

- `refund_doc_present` (mức `halt`): dừng pipeline khi mất toàn bộ dữ liệu refund policy.
- `exported_at_within_48h` (mức `warn`): cảnh báo snapshot dữ liệu quá cũ nhưng không chặn pipeline.

Ở phần tài liệu kỹ thuật, tôi cập nhật `docs/pipeline_architecture.md` bằng sơ đồ Mermaid và mô tả rõ ranh giới ingest -> clean -> validate -> embed, đồng thời ghi rõ cơ chế prune id cũ trước khi upsert.

Về phối hợp nhóm, tôi nhận output cleaned từ thành viên 1 để chạy expectation suite và cung cấp tín hiệu kiểm định (PASS/FAIL theo severity) cho thành viên 3 viết quality report và runbook vận hành.

## 2. Một quyết định kỹ thuật

Quyết định kỹ thuật quan trọng nhất của tôi là tách rõ expectation theo hai mức `halt` và `warn` thay vì gom chung. Lý do là mức độ rủi ro khác nhau:

- Với lỗi làm sai nghiệp vụ retrieval (ví dụ mất dữ liệu refund hoặc còn nội dung stale 14 ngày), pipeline phải `halt` để ngăn publish dữ liệu sai.
- Với lỗi thiên về vận hành (dữ liệu cũ hơn ngưỡng freshness), pipeline chỉ `warn` để đội vận hành theo dõi, tránh chặn toàn bộ luồng demo/test.

Tôi cũng rà soát logic embed trong `etl_pipeline.py` để bảo đảm idempotent. Cụ thể, hệ thống upsert theo `chunk_id` và prune các id không còn thuộc cleaned snapshot hiện tại. Cơ chế này giúp rerun không tạo vector trùng và tránh giữ lại vector stale gây nhiễu top-k retrieval.

## 3. Một lỗi/anomaly đã xử lý

Anomaly tôi chủ động tạo để kiểm thử là stale refund window. Tôi chạy kịch bản inject mạnh bằng raw file riêng (`data/raw/policy_export_inject_strong.csv`) với cờ `--no-refund-fix --skip-validate`. Kết quả log cho thấy:

- `expectation[refund_no_stale_14d_window] FAIL (halt) :: violations=2`
- `expectation[refund_doc_present] OK (halt) :: refund_rows=2`

Điều này chứng minh expectation halt có tác dụng phát hiện sai lệch nghiệp vụ. Sau đó tôi chạy lại pipeline chuẩn (`run_id=sprint2-clean-v2`) để khôi phục trạng thái sạch, expectation `refund_no_stale_14d_window` chuyển về `OK`, và dữ liệu embed quay lại đúng baseline.

## 4. Bằng chứng trước/sau

### Trước khi fix (inject mạnh)
- Run: `inject-strong`
- Log: `refund_no_stale_14d_window` FAIL (halt)
- Eval file `artifacts/eval/after_inject_strong.csv`:
	- `q_refund_window`: `contains_expected=no`, `hits_forbidden=yes`
	- Top-1 preview trả về nội dung `14 ngày làm việc`

### Sau khi chạy lại clean
- Run: `sprint2-clean-v2`
- Log: `refund_no_stale_14d_window` OK (halt)
- Eval file `artifacts/eval/before_after_eval_v2.csv`:
	- `q_refund_window`: `contains_expected=yes`, `hits_forbidden=no`
	- Top-1 preview quay lại nội dung `7 ngày làm việc`

Ngoài ra, log embed thể hiện rõ hành vi idempotent theo snapshot:
- Inject mạnh: `embed_prune_removed=5`, `embed_upsert count=6`
- Clean lại: `embed_prune_removed=6`, `embed_upsert count=5`

## 5. Cải tiến tiếp theo

Nếu có thêm 2 giờ, tôi sẽ đưa ngưỡng freshness của expectation `exported_at_within_48h` vào cấu hình contract/env để tùy biến theo môi trường (dev/staging/prod), đồng thời bổ sung unit test cho mapping severity (`warn`/`halt`) để tránh lệch giữa thiết kế và hành vi runtime.
