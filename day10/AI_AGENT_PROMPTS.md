# AI Agent Prompts cho các thành viên - Lab Day 10

Tài liệu này chứa các **Prompt (Câu lệnh hướng dẫn) chuyên sâu** dành cho AI Agent (như GitHub Copilot, ChatGPT, Claude) của từng thành viên. 
Các thành viên chỉ cần copy khối prompt tương ứng của mình, dán vào AI Agent của họ tại máy cá nhân để AI tự động đọc hiểu context và bắt tay vào code chuẩn xác nhất, đảm bảo ghép nối thành công và không giẫm chân lên nhau.

---

## 🤖 1. Prompt dành cho AI của Thành viên 1 (Data Engineer)

**Ngữ cảnh:** Copy toàn bộ nội dung dưới đây và yêu cầu AI thực hiện.

```text
Bạn là một Data Engineer AI chuyên nghiệp. Nhiệm vụ của bạn là hoàn thành phần Ingestion và Cleaning cho Lab Day 10 (Data Pipeline) trong workspace hiện tại. Hãy thực hiện tuần tự các bước sau:

1. Đọc file `day10/lab/README.md`, `day10/lab/SCORING.md` và `day10/lab/data/raw/policy_export_dirty.csv` để hiểu cấu trúc dữ liệu bẩn.
2. Mở file `day10/lab/transform/cleaning_rules.py`. Viết thêm ÍT NHẤT 3 rule làm sạch mới (không tính baseline có sẵn). Các rule này PHẢI thực tế và có tác động đo lường được (không trivial).
   - Gợi ý: Rule 1 chuẩn hóa format số điện thoại/email CSKH. Rule 2 loại bỏ các record có chứa ký tự rác HTML. Rule 3 đánh dấu quarantine các record thiếu trường bắt buộc quan trọng.
   - Thêm docstring rõ ràng cho mỗi rule.
3. Mở file `day10/lab/docs/data_contract.md`. Cập nhật phần Source Map với ít nhất 2 nguồn dữ liệu, điền failure mode và metric tương ứng.
4. Mở file `day10/lab/contracts/data_contract.yaml`. Điền thông tin owner và quy định SLA.
5. Cung cấp cho tôi các lệnh terminal cần chạy để test pipeline (ví dụ: `python etl_pipeline.py run --run-id sprint1`) và giải thích tôi cần xem gì trong log để đảm bảo `raw_records`, `cleaned_records`, `quarantine_records` được ghi nhận đúng.
6. Soạn nội dung phần đóng góp của tôi để tôi điền vào bảng `metric_impact` trong file `reports/group_report.md` và dàn ý cho báo cáo `reports/individual/` của tôi.
```

---

## 🤖 2. Prompt dành cho AI của Thành viên 2 (Quality & DB Owner)

**Ngữ cảnh:** Thành viên 2 copy khối lệnh này sau khi đã Pull code (hoặc nhận file `cleaning_rules.py`) từ Thành viên 1.

```text
Bạn là một Data Quality & VectorDB AI Engineer. Nhiệm vụ của bạn là xây dựng hệ thống Validation (Expectations) và kiểm tra logic Embed cho hệ thống RAG trong Lab Day 10. Hãy làm các thao tác sau:

1. Đọc file quy định `day10/lab/README.md` và xem qua cấu trúc dữ liệu sau khi clean ở Sprint 1.
2. Mở file `day10/lab/quality/expectations.py`. Viết thêm ÍT NHẤT 2 expectation mới.
   - 1 Expectation loại `halt` (dừng toàn bộ pipeline nếu vi phạm nghiêm trọng, ví dụ: tỷ lệ null của cột ID > 0%).
   - 1 Expectation loại `warn` (chỉ in cảnh báo/drop dòng nhưng vẫn cho pipeline chạy tiếp, ví dụ: format ngày tháng không chuẩn ISO).
   - Các expectation này PHẢI bắt được lỗi thực tế hoặc tác động tới log (không trivial).
3. Đọc kiểm tra luồng Embed ChromaDB trong file `day10/lab/etl_pipeline.py` để xác nhận nó đã đảm bảo tính "idempotent" (upsert dựa trên `chunk_id` và prune (xóa) những id cũ dư thừa). Viết giải thích ngắn gọn về cách logic này hoạt động để tôi đưa vào báo cáo cá nhân.
4. Thiết kế sơ đồ kiến trúc luồng dữ liệu bằng Mermaid.js và chèn vào file `day10/lab/docs/pipeline_architecture.md`. Cần thể hiện rõ ranh giới Ingest -> Clean -> Validate -> Embed.
5. Cung cấp lệnh chạy pipeline `python etl_pipeline.py run --run-id sprint2` và chỉ cho tôi cách đọc log để chứng minh Expectation chạy thành công.
6. Soạn nội dung để tôi điền vào `reports/group_report.md` (bảng `metric_impact`) liên quan đến Expectation, và dàn ý báo cáo `reports/individual/`.
```

---

## 🤖 3. Prompt dành cho AI của Thành viên 3 (Observability & Ops Lead)

**Ngữ cảnh:** Đóng vai trò test trước và sau, vận hành hệ thống. AI của TV3 cần làm việc sinh file đánh giá và viết tài liệu vận hành.

```text
Bạn là một AI Data Observability & Ops Lead. Nhiệm vụ của bạn là chạy các chiến dịch kiểm thử (Inject Corruption, Before/After) và hoàn thiện hệ thống tài liệu vận hành cho Lab Day 10. Hãy thực hiện:

1. Viết hướng dẫn chi tiết các lệnh terminal để tôi chạy giả lập dữ liệu lỗi và lưu file đánh giá (Eval). Cụ thể: 
   - Lệnh chạy pipeline bỏ qua bước làm sạch: `python etl_pipeline.py run --run-id inject-bad --no-refund-fix --skip-validate`
   - Lệnh đánh giá: `python eval_retrieval.py --out artifacts/eval/after_inject_bad.csv`
   - Lệnh chạy pipeline bản sạch (điều kiện kiện chuẩn).
   - Lệnh đánh giá lần 2: `python eval_retrieval.py --out artifacts/eval/before_after_eval.csv`
2. Đọc file `artifacts/eval/after_inject_bad.csv` và `artifacts/eval/before_after_eval.csv` (nếu đã có trên máy), sau đó viết báo cáo dán vào `day10/lab/docs/quality_report_template.md` (và đổi tên file thành `quality_report.md`). Báo cáo cần chứng minh rõ bằng số liệu/text là retrieval kém đi thế nào khi có data bẩn.
3. Cấp lệnh chạy kiểm tra Freshness: `python etl_pipeline.py freshness --manifest ...` và giải thích cơ chế check.
4. Mở file `day10/lab/docs/runbook.md`, tự động sinh nội dung cho 5 mục Symptom -> Prevention, bao gồm kịch bản khắc phục khi Freshness check trả về FAIL/WARN.
5. Cấp lệnh chạy sinh file chấm điểm: `python grading_run.py --out artifacts/eval/grading_run.jsonl`.
6. Soạn cho tôi bản nháp báo cáo cá nhân `reports/individual/` tập trung vào "Quyết định kỹ thuật: Freshness boundary" và "Sự cố: Anomaly khi inject dữ liệu bẩn".
```

---
**Lưu ý chung cho cả 3 người khi dùng AI:**
1. AI sẽ sửa trực tiếp vào file. Hãy `git status` và `git diff` để kiểm tra lại những gì AI vừa sửa trước khi commit!
2. Mỗi người commit và đẩy (push) nhánh/code của mình. Người dùng sau kéo (pull) code mới nhất về để tiếp tục thao tác.
3. Khi viết báo cáo cá nhân, **phải thay đổi các mã run_id ảo** mà AI sinh ra bằng **run_id thật sự** hiển thị trên terminal máy tính của chính bạn để lấy trọn vẹn điểm cá nhân.