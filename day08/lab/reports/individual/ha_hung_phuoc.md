# Báo Cáo Cá Nhân — Lab Day 08: RAG Pipeline

**Họ và tên:** Hà Hưng Phước 
**Vai trò trong nhóm:** Retrieval Owner / Data & Indexing  
**Ngày nộp:** 2026-04-13  
**Độ dài yêu cầu:** 500–800 từ

---

## 1. Tôi đã làm gì trong lab này?

Trong lab này, tôi phụ trách Sprint 1 và tập trung gần như toàn bộ vào file [index.py](../../index.py). Việc đầu tiên tôi làm là hoàn thiện luồng tiền xử lý tài liệu: đọc các file trong `data/docs/`, chuẩn hóa dòng xuống hàng, tách header metadata và giữ lại nội dung chính để phục vụ chunking. Tôi cũng chỉnh lại cách parse metadata để mỗi chunk có thể mang theo ít nhất các trường quan trọng như `source`, `section`, `department`, `effective_date`, `access`. Đây là phần nền tảng vì nếu metadata sai thì phần retrieval và citation ở Sprint 2 sẽ lệch ngay.

Phần thứ hai tôi làm là thiết kế chunking theo cấu trúc tự nhiên thay vì cắt cứng theo ký tự. Tôi cho hệ thống ưu tiên split theo heading `=== ... ===`, sau đó mới tách tiếp theo paragraph và có overlap để giảm mất ngữ cảnh. Sau cùng, tôi implement `get_embedding()` và `build_index()` để đẩy dữ liệu vào ChromaDB collection `rag_lab`. Khi chạy script, hệ thống index được 5 tài liệu thành 29 chunks và `list_chunks()` cho thấy metadata đã đi đúng. Công việc của tôi là “mở đường” để Huyền có dữ liệu retrieval và để Hoài có cơ sở viết scorecard, tuning log và report.

---

## 2. Điều tôi hiểu rõ hơn sau lab này

Lab này giúp tôi hiểu rõ hơn rằng chunking không phải chỉ là kỹ thuật chia văn bản cho nhỏ hơn. Nó là một quyết định ảnh hưởng trực tiếp đến khả năng retrieve đúng evidence. Nếu chunk quá lớn, retriever dễ kéo theo nhiều nhiễu; nếu chunk quá nhỏ, câu trả lời có thể bị đứt mạch và mất điều kiện quan trọng. Overlap cũng không phải là chi tiết phụ. Với các tài liệu kiểu policy, một điều khoản thường phụ thuộc vào câu ngay trước hoặc sau nó, nên overlap giúp giữ ngữ cảnh để mô hình sau đó không bị “mất đoạn”.

Tôi cũng hiểu rõ hơn vai trò của metadata. Trước khi làm lab, tôi nghĩ metadata chủ yếu để ghi chú. Sau khi làm thực tế, tôi thấy metadata là hợp đồng giữa các thành viên trong nhóm: `source` phục vụ citation, `section` giúp đọc lại theo ngữ cảnh, `effective_date` rất quan trọng cho câu hỏi về phiên bản chính sách, còn `department` và `access` hỗ trợ lọc và phân tích. Nói cách khác, indexing không chỉ là “lưu dữ liệu”, mà là chuẩn hóa dữ liệu để toàn bộ pipeline có thể dùng ổn định.

---

## 3. Điều tôi ngạc nhiên hoặc gặp khó khăn

Khó khăn lớn nhất của tôi là làm cho parser vừa đủ đơn giản để chạy ổn, vừa đủ linh hoạt để đọc được nhiều định dạng header khác nhau trong 5 tài liệu. Ban đầu tôi dự đoán chỉ cần tách theo dấu `===` là đủ, nhưng thực tế một số file mở đầu bằng heading tiếng Việt, một số file lại có phần ghi chú hoặc tên tài liệu in hoa trước khi vào section. Nếu không xử lý kỹ, chunk đầu tiên sẽ bị lẫn header hoặc mất metadata. Tôi cũng gặp tình huống một số source trong file gốc không khớp hoàn toàn với tên file, nên nếu chỉ dựa vào tên file để làm `source` thì citation sẽ không phản ánh đúng nguồn gốc tài liệu.

Điều tôi ngạc nhiên nhất là chỉ cần chunking và metadata tốt lên một chút thì phần retrieval về sau đã dễ hơn rất nhiều. Khi chạy kiểm tra, collection `rag_lab` có 29 chunks và mọi chunk đều có `effective_date`. Điều đó cho tôi thấy ở bài RAG, chất lượng indexing quyết định một phần rất lớn kết quả cuối, không phải chỉ prompt hay LLM.

---

## 4. Phân tích một câu hỏi trong scorecard

**Câu hỏi:** “Approval Matrix để cấp quyền hệ thống là tài liệu nào?”

Câu này thú vị vì nó kiểm tra khả năng nhận ra alias/tên cũ của tài liệu. Trong bộ dữ liệu, tài liệu hiện tại là `access_control_sop.txt`, nhưng trong nội dung có ghi chú rằng nó trước đây có tên “Approval Matrix for System Access”. Với baseline dense retrieval, nếu query chỉ bám vào cụm “Approval Matrix”, hệ thống vẫn có thể tìm ra đúng tài liệu nhờ nội dung ghi chú này, nhưng không phải lúc nào cũng chắc chắn vì dense search phụ thuộc vào độ gần ngữ nghĩa của embedding. Nếu chunk bị cắt không tốt hoặc metadata source không rõ, retrieval có thể kéo nhầm sang tài liệu access khác hoặc chỉ trả về một chunk chung chung.

Theo thiết kế của nhóm, variant rerank ở Sprint 3 không sửa lỗi indexing trực tiếp nhưng có thể cải thiện việc chọn đúng chunk trong tập ứng viên top-10. Nói cách khác, rerank giúp lọc noise ở tầng retrieval, còn vấn đề gốc vẫn nằm ở việc index phải giữ được phần ghi chú alias và section liên quan. Vì vậy, nếu baseline đã bỏ sót alias thì variant có thể cứu được một phần, nhưng nếu indexing thiếu thông tin thì rerank không thể bù hoàn toàn. Từ góc nhìn của tôi, câu hỏi này cho thấy indexing tốt phải giữ được cả nội dung chính lẫn chi tiết phụ như ghi chú đổi tên tài liệu.

---

## 5. Nếu có thêm thời gian, tôi sẽ làm gì?

Nếu có thêm thời gian, tôi muốn cải thiện chunking theo paragraph một cách thông minh hơn để tránh cắt các điều khoản nhiều gạch đầu dòng thành những đoạn quá rời rạc. Tôi cũng muốn chuẩn hóa `source` để vừa nhất quán cho retrieval, vừa khớp với tên tài liệu trong scorecard và log grading. Cuối cùng, tôi sẽ thử thêm một bước kiểm tra tự động xem chunk nào thiếu metadata hoặc bị chia quá vụn, vì đó là lỗi dễ làm giảm chất lượng retrieval mà rất khó nhìn thấy bằng mắt thường.