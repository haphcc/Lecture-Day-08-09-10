# Báo Cáo Cá Nhân — Lab Day 08: RAG Pipeline

**Họ và tên:** Phạm Thị Hoài 
**Vai trò trong nhóm:**  Eval Owner / Documentation Owner  
**Ngày nộp:** 13/04/2026 
**Độ dài yêu cầu:** 500–800 từ

---

## 1. Tôi đã làm gì trong lab này? (100-150 từ)

> Mô tả cụ thể phần bạn đóng góp vào pipeline:
> - Sprint nào bạn chủ yếu làm?
> - Cụ thể bạn implement hoặc quyết định điều gì?
> - Công việc của bạn kết nối với phần của người khác như thế nào?

Trong lab này, tôi tập trung chính ở Sprint 4 với vai trò Eval Owner và đồng thời hỗ trợ Documentation Owner. Tôi phụ trách chạy scorecard baseline/variant, theo dõi chất lượng theo 4 metric (Faithfulness, Relevance, Context Recall, Completeness), và phân tích chênh lệch A/B để đưa ra nhận xét có số liệu. Khi pipeline không ra điểm ổn định, tôi tham gia debug theo error tree: kiểm tra index có rỗng hay không, kiểm tra mismatch embedding dimension (384 vs 1536), xác nhận biến môi trường và provider, rồi chuyển luồng generation sang OpenAI để chạy ổn định hơn. Tôi cũng bổ sung thêm 2 test case mới (q11, q12) dựa trên tài liệu thật để đánh giá rộng hơn. Công việc của tôi nối trực tiếp giữa phần index/retrieval của kỹ thuật và phần báo cáo kết quả cuối cùng của nhóm.

---

## 2. Điều tôi hiểu rõ hơn sau lab này (100-150 từ)

> Chọn 1-2 concept từ bài học mà bạn thực sự hiểu rõ hơn sau khi làm lab.
> Ví dụ: chunking, hybrid retrieval, grounded prompt, evaluation loop.
> Giải thích bằng ngôn ngữ của bạn — không copy từ slide.

Sau lab, tôi hiểu rõ hơn rằng evaluation không chỉ là “chấm điểm câu trả lời”, mà là một vòng lặp kiểm định toàn bộ pipeline RAG. Ví dụ, Context Recall cao chưa chắc answer đã đầy đủ; retrieval có thể đúng nguồn nhưng generation vẫn trả lời thiếu ý quan trọng. Tôi cũng hiểu rõ vai trò của grounded prompt: prompt càng siết chặt “chỉ trả lời theo context”, hệ thống càng an toàn về hallucination, nhưng có thể làm Completeness giảm trong các câu thiếu ngữ cảnh hoặc có alias. Một điểm quan trọng khác là A/B Rule thực sự hữu ích khi tune: chỉ đổi 1 biến (bật rerank) thì mới đọc được tác động thật lên các metric. Nhờ đó, thay vì tranh luận cảm tính “có vẻ tốt hơn”, nhóm có thể kết luận dựa trên delta cụ thể giữa baseline và variant.

---

## 3. Điều tôi ngạc nhiên hoặc gặp khó khăn (100-150 từ)

> Điều gì xảy ra không đúng kỳ vọng?
> Lỗi nào mất nhiều thời gian debug nhất?
> Giả thuyết ban đầu của bạn là gì và thực tế ra sao?

Khó khăn lớn nhất của tôi không phải ở logic chấm điểm, mà ở tính ổn định môi trường khi chạy thực tế. Ban đầu tôi nghĩ điểm thấp do prompt hoặc retrieval, nhưng thực tế có nhiều lỗi nền: collection Chroma từng rỗng, có lúc embedding dùng sai provider nên lệch chiều vector, và có giai đoạn bị quota/credential khiến model trả lỗi thay vì answer. Một lỗi tốn thời gian khác là console/encoding trên Windows làm output nhiễu khi in tiếng Việt, khiến việc đọc log khó hơn. Điều tôi ngạc nhiên là cùng một bộ code, chỉ cần khác cấu hình .env hoặc khác trạng thái tài nguyên mạng/model là chất lượng scorecard thay đổi rất mạnh. Vì vậy, bài học của tôi là phải tách rõ “lỗi chất lượng mô hình” và “lỗi vận hành hệ thống” trước khi kết luận.

---

## 4. Phân tích một câu hỏi trong scorecard (150-200 từ)

> Chọn 1 câu hỏi trong test_questions.json mà nhóm bạn thấy thú vị.
> Phân tích:
> - Baseline trả lời đúng hay sai? Điểm như thế nào?
> - Lỗi nằm ở đâu: indexing / retrieval / generation?
> - Variant có cải thiện không? Tại sao có/không?

**Câu hỏi:** ___________

**Phân tích:**

Tôi chọn câu q07: “Approval Matrix để cấp quyền hệ thống là tài liệu nào?”. Đây là câu thú vị vì có alias (tên cũ) trong khi tài liệu hiện tại dùng tên mới “Access Control SOP”. Ở baseline (dense), hệ thống thường trả lời theo hướng an toàn và điểm thấp ở relevance/completeness, dù faithfulness vẫn cao. Điều này cho thấy lỗi không nằm ở index hoàn toàn, mà nằm ở khả năng nối ngữ nghĩa giữa alias query và câu trả lời mong đợi. Khi chuyển sang variant bật rerank, tôi kỳ vọng thứ tự chunk sẽ tốt hơn để model nhìn thấy dòng ghi chú đổi tên tài liệu sớm hơn. Kết quả thực tế: variant không cải thiện rõ rệt cho q07, tức là rerank không phải “thuốc chữa mọi câu hỏi alias”. Phân tích theo error tree, đây là lỗi giao điểm retrieval + generation: retrieval cần boost tốt hơn cho chunk có tín hiệu alias, còn generation cần template trả lời nhấn mạnh mapping “tên cũ → tên mới” thay vì chỉ abstain ngắn. Trường hợp này giúp tôi hiểu rằng một metric tổng không đủ, phải soi từng câu để xác định đúng tầng lỗi.

---

## 5. Nếu có thêm thời gian, tôi sẽ làm gì? (50-100 từ)

> 1-2 cải tiến cụ thể bạn muốn thử.
> Không phải "làm tốt hơn chung chung" mà phải là:
> "Tôi sẽ thử X vì kết quả eval cho thấy Y."

Nếu có thêm thời gian, tôi sẽ thử hai hướng cụ thể. Thứ nhất, thêm rule-based boosting cho retrieval theo alias dictionary (ví dụ “Approval Matrix” -> “Access Control SOP”) vì q07 cho thấy dense+rerkank vẫn chưa đủ mạnh ở trường hợp đổi tên tài liệu. Thứ hai, tôi sẽ tinh chỉnh prompt theo hướng “abstain có giải thích ngắn + nêu phần chắc chắn từ context” để giữ Faithfulness cao nhưng tăng Completeness ở các câu như q09, q10.

---

*Lưu file này với tên: `reports/individual/[ten_ban].md`*
*Ví dụ: `reports/individual/nguyen_van_a.md`*
