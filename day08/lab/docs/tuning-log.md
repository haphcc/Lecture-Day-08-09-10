# Tuning Log — RAG Pipeline (Day 08 Lab)

> Template: Ghi lại mỗi thay đổi và kết quả quan sát được.
> A/B Rule: Chỉ đổi MỘT biến mỗi lần.

---

## Baseline (Sprint 2)

**Ngày:** 2026-04-13  
**Config:**
```
retrieval_mode = "dense"
chunk_size = 400 tokens (approx)
overlap = 80 tokens (approx)
top_k_search = 10
top_k_select = 3
use_rerank = False
llm_model = gpt-4o-mini
```

**Scorecard Baseline:**
| Metric | Average Score |
|--------|--------------|
| Faithfulness | 5.00 /5 |
| Answer Relevance | 4.17 /5 |
| Context Recall | 5.00 /5 |
| Completeness | 3.17 /5 |

**Câu hỏi yếu nhất (điểm thấp):**
- q09 (Insufficient Context): completeness thấp vì expected answer có gợi ý xử lý, trong khi system prompt ưu tiên abstain an toàn.
- q07 (Approval Matrix alias): relevance/completeness thấp do query alias (tên cũ) và answer thiên về abstain ngắn.
- q10 (VIP refund): completeness thấp vì policy không có flow VIP riêng, model trả lời an toàn nhưng thiếu một số điểm so với expected text dài.

**Giả thuyết nguyên nhân (Error Tree):**
- [x] Indexing: Chunking cắt giữa điều khoản (đã giảm nhờ heading + overlap)
- [ ] Indexing: Metadata thiếu effective_date
- [x] Retrieval: Dense bỏ lỡ exact keyword / alias
- [ ] Retrieval: Top-k quá ít → thiếu evidence
- [x] Generation: Prompt không đủ grounding (ưu tiên abstain mạnh làm giảm completeness)
- [ ] Generation: Context quá dài → lost in the middle

---

## Variant 1 (Sprint 3)

**Ngày:** 2026-04-13  
**Biến thay đổi:** Bật rerank bằng cross-encoder (`use_rerank = True`)  
**Lý do chọn biến này:**
Baseline đã có context recall cao nhưng completeness còn thấp. Nhóm muốn giữ nguyên index/chunking và chỉ thêm bước rerank để tối ưu thứ tự chunk trước khi generate.
Mục tiêu: tăng completeness và relevance mà không phá grounding.

**Config thay đổi:**
```
retrieval_mode = "dense"
use_rerank = True
# Các tham số còn lại giữ nguyên như baseline
```

**Scorecard Variant 1:**
| Metric | Baseline | Variant 1 | Delta |
|--------|----------|-----------|-------|
| Faithfulness | 5.00/5 | 4.83/5 | -0.17 |
| Answer Relevance | 4.17/5 | 4.08/5 | -0.09 |
| Context Recall | 5.00/5 | 5.00/5 | +0.00 |
| Completeness | 3.17/5 | 3.33/5 | +0.16 |

**Nhận xét:**
Variant 1 cải thiện rõ ở q01 và q04 (tổng điểm tăng), chủ yếu nhờ completeness tốt hơn sau rerank.
Tuy nhiên có câu giảm nhẹ như q08 và q12 (faithfulness/relevance giảm), cho thấy rerank không luôn tốt hơn dense gốc ở mọi query.
Nhìn tổng thể, rerank cải thiện độ đầy đủ thông tin nhưng đánh đổi nhẹ độ ổn định của faithfulness/relevance.

**Kết luận:**
Variant 1 chưa vượt baseline một cách toàn diện.
Bằng chứng: Completeness tăng (+0.16) nhưng Faithfulness và Relevance giảm nhẹ (-0.17 và -0.09), Context Recall giữ nguyên 5.00.
Vì mục tiêu hệ thống ưu tiên grounded answer ổn định, baseline vẫn là cấu hình an toàn hơn để chốt bài; variant dùng như minh chứng tuning có trade-off.

---

## Variant 2 (nếu có thời gian)

**Biến thay đổi:** Chưa thực hiện (giữ phạm vi lab trong 1 biến tune)  
**Config:**
```
# Không chạy Variant 2 để tuân thủ thời gian và A/B rule
```

**Scorecard Variant 2:**
| Metric | Baseline | Variant 1 | Variant 2 | Best |
|--------|----------|-----------|-----------|------|
| Faithfulness | 5.00 | 4.83 | N/A | Baseline |
| Answer Relevance | 4.17 | 4.08 | N/A | Baseline |
| Context Recall | 5.00 | 5.00 | N/A | Tie |
| Completeness | 3.17 | 3.33 | N/A | Variant 1 |

---

## Tóm tắt học được

1. **Lỗi phổ biến nhất trong pipeline này là gì?**
   > Lỗi external dependency (quota API/khả dụng model) và mismatch cấu hình giữa indexing-retrieval-generation làm pipeline fail hoặc điểm nhiễu.

2. **Biến nào có tác động lớn nhất tới chất lượng?**
   > Bước rerank tác động rõ nhất tới completeness (có cải thiện), nhưng cũng tạo trade-off ở faithfulness/relevance.

3. **Nếu có thêm 1 giờ, nhóm sẽ thử gì tiếp theo?**
   > Thử prompt refinement cho case alias/insufficient-context (q07, q09, q10), kết hợp rule-based source boosting theo keyword và đánh giá lại với cùng bộ test 12 câu.
