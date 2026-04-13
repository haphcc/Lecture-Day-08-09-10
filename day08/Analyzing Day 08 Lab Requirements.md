# Chat Conversation

Note: _This is purely the output of the chat conversation and does not contain any raw data, codebase snippets, etc. used to generate the output._

### User Input

đọc cấu trúc thư mục của day 08 và cho tôi biết lab này cần phải làm gì

*Listed directory [Lecture-Day-08-09-10](file:///c:/Users/WBPC.VN/Documents/GitHub/Lecture-Day-08-09-10) *

*Listed directory [day08](file:///c:/Users/WBPC.VN/Documents/GitHub/Lecture-Day-08-09-10/day08) *

*Listed directory [lab](file:///c:/Users/WBPC.VN/Documents/GitHub/Lecture-Day-08-09-10/day08/lab) *

*Viewed [README.md](file:///c:/Users/WBPC.VN/Documents/GitHub/Lecture-Day-08-09-10/day08/lab/README.md) *

### Planner Response

Cấu trúc của Lab Day 08 tập trung vào việc xây dựng một hệ thống **RAG Pipeline hoàn chỉnh** (Indexing → Retrieval → Generation → Evaluation) cho một trợ lý ảo nội bộ (IT Helpdesk).

Dưới đây là chi tiết những gì bạn cần thực hiện:

### 1. Cấu trúc thư mục Lab
*   `index.py`: Xử lý tiền xử lý, cắt nhỏ văn bản (chunking), tạo embedding và lưu trữ vào vector database (ChromaDB).
*   `rag_answer.py`: Thực hiện truy vấn (retrieval), xếp hạng lại (reranking - nếu có) và gọi LLM để tạo câu trả lời.
*   `eval.py`: Đánh giá chất lượng hệ thống bằng bảng điểm (scorecard) và so sánh A/B giữa các cấu hình khác nhau.
*   `data/`: Chứa các tài liệu chính sách (SLA, FAQ, Refund policy...) và bộ câu hỏi kiểm thử.
*   `docs/`: Nơi viết tài liệu kiến trúc và nhật ký tối ưu hóa (tuning log).

### 2. Các nhiệm vụ cụ thể qua 4 Sprint (mỗi sprint ~60 phút)

#### **Sprint 1: Xây dựng Index (File: `index.py`)**
*   **Cài đặt `get_embedding()`**: Chọn sử dụng OpenAI hoặc Sentence Transformers.
*   **Hoàn thiện `build_index()`**: Viết code để tạo embedding cho từng đoạn (chunk) và đẩy vào ChromaDB. Đảm bảo mỗi chunk có các metadata như `source`, `section`.
*   **Kiểm tra**: Chạy `list_chunks()` để xem dữ liệu đã được lưu đúng chưa.

#### **Sprint 2: Truy vấn Baseline & Trả lời (File: `rag_answer.py`)**
*   **Cài đặt `retrieve_dense()`**: Thực hiện tìm kiếm dựa trên vector (similarity search).
*   **Cài đặt `call_llm()`**: Kết nối với OpenAI GPT hoặc Google Gemini để lấy câu trả lời.
*   **Yêu cầu**: Câu trả lời phải có dẫn nguồn (citations) và phải biết trả lời "Không đủ dữ liệu" nếu không tìm thấy thông tin trong tài liệu.

#### **Sprint 3: Tối ưu hóa (File: `rag_answer.py`)**
*   **Chọn 1 kỹ thuật nâng cao**:
    *   **Hybrid Search**: Kết hợp tìm kiếm vector và tìm kiếm từ khóa (BM25).
    *   **Rerank**: Dùng Cross-encoder để xếp hạng lại các kết quả tìm được.
    *   **Query Transform**: Chỉnh sửa lại câu hỏi của người dùng trước khi tìm kiếm.
*   **So sánh**: Chạy `compare_retrieval_strategies()` để xem bản nâng cao có tốt hơn bản baseline không.

#### **Sprint 4: Đánh giá & Báo cáo (File: `eval.py` & `docs/`)**
*   **Chấm điểm**: Chạy 10 câu hỏi kiểm thử và ghi lại kết quả vào Scorecard.
*   **Hoàn thiện tài liệu**:
    *   `docs/architecture.md`: Mô tả sơ đồ hệ thống bạn đã xây dựng.
    *   `docs/tuning-log.md`: Ghi lại các thử nghiệm tối ưu hóa ở Sprint 3.
    *   **Báo cáo cá nhân**: Viết một bài thu hoạch (~500-800 từ) trong thư mục `reports/individual/`.

### 3. Cách bắt đầu ngay
1.  **Cài đặt thư viện**: `pip install -r requirements.txt`
2.  **Cấu hình**: Coppy `.env.example` thành `.env` và điền API Key.
3.  **Chạy thử**: `python index.py` để xem phần tiền xử lý dữ liệu mẫu.

Bạn có muốn tôi đi vào chi tiết code của file nào trước không? (Ví dụ: xem các `TODO` trong `index.py` để bắt đầu Sprint 1).

### User Input

bài này có thể chia làm việc nhóm như thế nào

### Planner Response

Dựa trên tài liệu `README.md` của Lab Day 08, bài tập này đã được thiết kế sẵn để phân chia cho một nhóm từ **3-4 người**. Dưới đây là phương án chia việc tối ưu để cả team có thể chạy song song:

### 1. Phân vai chính (Roles)

| Vai trò | Trách nhiệm chính | File quản lý |
| :--- | :--- | :--- |
| **Tech Lead** | Cài đặt môi trường, kết nối pipeline (End-to-End), xử lý lỗi hệ thống và gọi API LLM. | `rag_answer.py`, `.env` |
| **Retrieval Owner** | Thiết kế chiến lược cắt nhỏ văn bản (Chunking), đánh Metadata và cài đặt các phương thức tìm kiếm (Dense/Hybrid). | `index.py` |
| **Eval Owner** | Chuẩn bị bộ câu hỏi test, xác định câu trả lời mẫu (Ground truth) và chạy các script đánh giá. | `eval.py`, `data/test_questions.json` |
| **Documentation Owner** | Vẽ sơ đồ kiến trúc, ghi chép lại kết quả các thử nghiệm và tổng hợp báo cáo nhóm. | `docs/`, `reports/` |

---

### 2. Kế hoạch phối hợp theo Sprint (Lộ trình 4 tiếng)

#### **Giai đoạn 1: Xây dựng nền móng (Sprint 1 & 2)**
*   **Retrieval Owner**: Hoàn thiện `index.py`. Quan trọng nhất là quyết định: "Cắt văn bản bao nhiêu từ 1 đoạn?" và "Metadata gồm những gì?".
*   **Tech Lead**: Viết hàm gọi LLM (`call_llm`) và cấu hình prompt cơ bản. Sau đó lấy dữ liệu từ *Retrieval Owner* để hoàn thiện hàm `rag_answer`.
*   **Eval Owner**: Ngồi đọc các file chính sách (`data/docs/`) để soạn ra 10 câu hỏi "hóc búa" kèm câu trả lời mẫu vào file `test_questions.json`.

#### **Giai đoạn 2: Tối ưu & Đánh giá (Sprint 3 & 4)**
*   **Retrieval Owner**: Thử nghiệm các phương án nâng cao (VD: Thêm Reranker hoặc Hybrid search).
*   **Eval Owner**: Chạy script `eval.py` để chấm điểm bộ câu hỏi đã soạn. So sánh xem phương án nâng cao của *Retrieval Owner* có thực sự làm tăng điểm số không.
*   **Tech Lead**: Debug các lỗi phát sinh khi chạy Eval và hỗ trợ tối ưu Prompt nếu câu trả lời của LLM chưa chuẩn.
*   **Documentation Owner**: Thu thập kết quả từ *Eval Owner* và *Retrieval Owner* để điền vào `architecture.md` và `tuning-log.md`.

---

### 3. Mẹo để làm việc nhóm hiệu quả bài này:
1.  **Thống nhất Metadata sớm**: *Retrieval Owner* và *Tech Lead* cần thống nhất ngay từ đầu các trường metadata (như `source`, `page`, `date`) để khi hiển thị câu trả lời có thể trích dẫn nguồn chính xác.
2.  **Làm việc song song trên Git**: 
    *   Người làm `index.py` và `eval.py` có thể làm độc lập khá sớm.
    *   Chỉ có `rag_answer.py` là nơi Tech Lead cần tổng hợp code từ mọi người.
3.  **Sử dụng `.env.example`**: Tech Lead nên hướng dẫn cả nhóm cách cấu hình API Key để ai cũng có thể chạy thử code trên máy cá nhân.

**Lời khuyên:** Nếu nhóm bạn có 3 người, có thể gộp vai trò **Tech Lead** và **Retrieval Owner** làm một, hoặc gộp **Eval Owner** và **Documentation Owner**.

### User Input

nói về độ phụ thuộc code lẫn nhau của các thành viên trong nhóm thì sao

### Planner Response

Trong một dự án RAG (Retrieval-Augmented Generation), độ phụ thuộc code (code dependency) đi theo một **chuỗi dây chuyền (Pipeline)**. Nếu một mắt xích bị tắc, các mắt xích sau sẽ khó làm việc. 

Dưới đây là phân tích độ phụ thuộc và cách để nhóm bạn không phải "ngồi chờ" nhau:

### 1. Phân tích Chuỗi Phụ thuộc (Critical Path)

Cấu trúc phụ thuộc của bài này là:
**`index.py` (Dữ liệu) $\rightarrow$ `rag_answer.py` (Logic) $\rightarrow$ `eval.py` (Đánh giá)**

*   **Mức độ phụ thuộc cao nhất:** `rag_answer.py` phụ thuộc hoàn toàn vào kết quả của `index.py`. Nếu chưa có database (chromadb) được tạo từ `index.py`, bạn không thể chạy hay test code retrieval.
*   **Mức độ phụ thuộc trung bình:** `eval.py` phụ thuộc vào `rag_answer.py`. Tuy nhiên, người làm Eval có thể viết trước các bộ test case và hàm tính điểm mà chưa cần pipeline chạy thật.

---

### 2. Cách giảm thiểu "Nghẽn cổ chai" (Bottleneck)

Để 4 thành viên có thể làm việc cùng lúc mà không cần chờ người trước xong 100%, hãy áp dụng các chiến thuật sau:

#### **A. Thống nhất "Hợp đồng" (Interface) ngay từ phút thứ 10**
Trước khi code, nhóm phải chốt với nhau các hàm quan trọng sẽ nhận vào gì và trả về gì.
*   **Ví dụ (Hợp đồng giữa Index và Retrieval):** Thống nhất metadata sẽ có các trường: `source`, `section`, `effective_date`. Nếu người làm Index đổi tên trường thành `file_name`, code của người làm Retrieval sẽ lỗi ngay.
*   **Ví dụ (Hợp đồng giữa Retrieval và Eval):** Hàm `rag_answer(question)` phải luôn trả về một Dictionary có dạng: `{"answer": "...", "sources": ["doc1.txt", "doc2.txt"]}`.

#### **B. Chiến thuật "Mocking" (Giả lập dữ liệu)**
*   **Người làm Retrieval (`rag_answer.py`)**: Nếu người làm Index chưa xong, bạn có thể tạo một database "nháp" với chỉ 1-2 câu đơn giản bằng tay để viết code tìm kiếm trước.
*   **Người làm Eval (`eval.py`)**: Nếu hệ thống RAG chưa chạy được, bạn có thể tự tạo một file JSON kết quả "giả" (dummy results) để test code tính điểm (Accuracy, Relevancy) của mình.

#### **C. Chia nhỏ file (Cấu trúc bài Lab đã làm tốt việc này)**
Bài Lab đã chia sẵn thành 3 file độc lập:
1.  **Người 1 (`index.py`)**: Tập trung vào xử lý văn bản (Chunking).
2.  **Người 2 (`rag_answer.py`)**: Tập trung vào Prompt Engineering và kết nối LLM.
3.  **Người 3 (`eval.py`)**: Tập trung vào Logic toán học để đánh giá (Metric).

---

### 3. Sơ đồ "Giao điểm" giữa các thành viên

| Người A làm xong... | Thì Người B có thể bắt đầu... |
| :--- | :--- |
| **Index Owner** xong phần lưu database | **Tech Lead** bắt đầu test chính xác kết quả Retrieval. |
| **Eval Owner** xong bộ câu hỏi | **Tech Lead** dùng bộ câu hỏi đó để "debug" xem tại sao RAG trả lời sai. |
| **Tech Lead** xong bản Baseline | **Documentation Owner** bắt đầu chụp ảnh màn hình và log kết quả để đưa vào báo cáo. |
| **Retrieval Owner** xong bản Tuning | **Eval Owner** bắt đầu chạy so sánh A/B để xem điểm có tăng không. |

**Tóm lại:** Độ phụ thuộc là **Tuần tự về mặt dữ liệu** nhưng có thể **Song song về mặt code** nếu các bạn thống nhất được cấu trúc dữ liệu trao đổi (hợp đồng interface) ngay từ đầu.

### User Input

nhóm tôi có 3 người, dựa theo gợi ý của lab thì có thể chia như thế nào

### Planner Response

Với nhóm 3 người, bạn nên gộp các vai trò có sự giao thoa lớn về mặt technical hoặc timeline để tối ưu hóa sức mạnh của từng người. Dưới đây là 2 phương án phân chia hợp lý nhất:

### Phương án 1: Chia theo luồng Pipeline (Gợi ý ưu tiên)
Phương án này giúp mỗi người nắm trọn vẹn một mảng nghiệp vụ, giảm bớt việc phải đợi nhau quá lâu.

1.  **Thành viên 1: Data & Retrieval Specialist (Chuyên gia Dữ liệu)**
    *   **Công việc:** Chịu trách nhiệm toàn bộ file `index.py` và phần tìm kiếm (Retrieval) trong `rag_answer.py`.
    *   **Sprint trọng tâm:** 1 và 3.
    *   **Nhiệm vụ:** Cắt chunk, đánh metadata, cài đặt Hybrid search hoặc Reranker.
2.  **Thành viên 2: AI & System Lead (Chuyên gia AI)**
    *   **Công việc:** Chịu trách nhiệm phần gọi LLM (Generation) trong `rag_answer.py`, thiết kế Prompt và kết nối toàn bộ hệ thống.
    *   **Sprint trọng tâm:** 2.
    *   **Nhiệm vụ:** Viết Prompt sao cho trả lời đúng từ context, xử lý trích dẫn nguồn (citation), cấu hình API Key.
3.  **Thành viên 3: Quality & Documentation (Kiểm định & Tài liệu)**
    *   **Công việc:** Chịu trách nhiệm file `eval.py`, bộ câu hỏi test và viết báo cáo.
    *   **Sprint trọng tâm:** 4.
    *   **Nhiệm vụ:** Soạn 10 câu hỏi test "hiểm", chạy chấm điểm Scorecard, viết tài liệu kiến trúc (architecture.md) và nhật ký tối ưu (tuning-log.md).

---

### Phương án 2: Chia theo cặp "Thi công - Giám sát"
Phương án này phù hợp nếu trong nhóm có 2 người mạnh về code và 1 người mạnh về phân tích/tài liệu.

*   **Người A (Upstream Engineer):** Chuyên trách phần "Đầu vào" (Indexing) - Phụ trách `index.py`. Làm sao để dữ liệu vào database là "sạch" và "chuẩn" nhất.
*   **Người B (Downstream Engineer):** Chuyên trách phần "Đầu ra" (RAG + Eval) - Phụ trách `rag_answer.py` và `eval.py`. Tập trung vào việc lấy thông tin ra và trả lời + chấm điểm.
*   **Người C (Project Lead & Docs):** Chuyên trách phần "Kết nối & Hồ sơ". Người này sẽ giúp Người A và B kết nối code, hỗ trợ debug, viết toàn bộ tài liệu và quản lý tiến độ các Sprints.

---

### Lời khuyên cho nhóm 3 người:
*   **Tại Sprint 1:** Người 1 và 2 cùng tập trung vào `index.py` để xong thật nhanh phần database, vì đây là "nguồn sống" cho cả bài lab.
*   **Tại Sprint 3:** Khi Người 1 đang mải mê "Tuning" tìm kiếm nâng cao, Người 3 nên chủ động lấy bản code sơ khai (Baseline) của Người 2 để chạy thử nghiệm đánh giá ngay, tránh dồn việc vào phút cuối.
*   **Giao diện chung:** 3 người hãy ngồi cạnh nhau và thống nhất file JSON kết quả trả về của RAG. Chỉ cần thống nhất được cái này, các bạn có thể code 3 file độc lập mà không sợ bị xung đột.

**Nhóm bạn có ai mạnh về mảng nào không (ví dụ ai thích viết prompt, ai thích làm với database)?** Tôi sẽ tư vấn cụ thể hơn cho từng người.

### User Input

phân chia công việc thử cho tôi theo phương ấn 1

### Planner Response

Dưới đây là bảng phân bổ công việc chi tiết cho nhóm 3 người theo **Phương án 1** (Chia theo luồng Pipeline). Bạn có thể copy bảng này gửi vào nhóm Zalo/Discord của team để bắt đầu ngay:

### 📋 BẢNG PHÂN CHIA CÔNG VIỆC - LAB DAY 08

#### 👤 Thành viên 1: Chuyên gia Dữ liệu (Data & Retrieval Specialist)
*   **Trọng tâm:** Làm cho hệ thống "tìm đúng" thông tin cần thiết.
*   **Công việc chi tiết:**
    *   **Sprint 1:** Viết hàm `get_embedding()` và hoàn thiện `build_index()` trong `index.py`. Quyết định kích thước `chunk_size` và `overlap`.
    *   **Sprint 2:** Hỗ trợ Thành viên 2 viết hàm `retrieve_dense()` trong `rag_answer.py`.
    *   **Sprint 3:** (Quan trọng) Cài đặt phương án tìm kiếm nâng cao (Hybrid search hoặc Reranker) để cải thiện độ chính xác.
    *   **Sprint 4:** Giải trình về chiến lược Chunking & Retrieval trong báo cáo.

#### 👤 Thành viên 2: Chuyên gia AI (AI & System Lead)
*   **Trọng tâm:** Làm cho hệ thống "trả lời hay" và kết nối trơn tru.
*   **Công việc chi tiết:**
    *   **Sprint 1:** Setup file `.env`, cài đặt thư viện và đảm bảo mọi người đều chạy được code mẫu.
    *   **Sprint 2:** Hoàn thiện hàm `call_llm()` và `rag_answer()` trong `rag_answer.py`. Thiết kế Prompt sao cho câu trả lời ngắn gọn, đúng sự thật và có trích dẫn nguồn `[1]`, `[2]`.
    *   **Sprint 3:** Tinh chỉnh Prompt engineering dựa trên các lỗi "hallucination" (nói dối) mà Thành viên 3 phát hiện ra.
    *   **Sprint 4:** Đảm bảo toàn bộ pipeline chạy được bằng 1 lệnh duy nhất từ đầu đến cuối.

#### 👤 Thành viên 3: Kiểm định & Tài liệu (Quality & Documentation)
*   **Trọng tâm:** Đặt câu hỏi khó để "bắt lỗi" hệ thống và chứng minh kết quả.
*   **Công việc chi tiết:**
    *   **Sprint 1:** Đọc kỹ 5 file văn bản trong `data/docs/` để soạn 10 câu hỏi kiểm thử vào `data/test_questions.json`.
    *   **Sprint 2:** Chạy thử bản Baseline, ghi lại những câu trả lời sai hoặc chưa hay để báo cho Thành viên 1 & 2 sửa.
    *   **Sprint 3:** Viết tài liệu `docs/architecture.md` (mô tả hệ thống) và `docs/tuning-log.md` (ghi lại các lần thử nghiệm).
    *   **Sprint 4:** Chạy file `eval.py` để lấy điểm số cuối cùng (Scorecard) cho cả bản Baseline và bản Nâng cao. Tổng hợp báo cáo cá nhân cho cả nhóm.

---

### ⏱️ TIẾN ĐỘ PHỐI HỢP (TIMELINE)

| Thời gian | Thành viên 1 (Data) | Thành viên 2 (AI) | Thành viên 3 (Eval/Docs) |
| :--- | :--- | :--- | :--- |
| **0-60'** | Xong `index.py`, nạp dữ liệu vào DB. | Setup môi trường, viết `call_llm`. | Soạn xong JSON 10 câu hỏi test. |
| **60-120'** | Viết hàm `retrieve_dense`. | Nối Retrieval + LLM -> Xong Baseline. | Ghi nhận lỗi của bản Baseline. |
| **120-180'** | Code bản Nâng cao (Hybrid/Rerank). | Tinh chỉnh Prompt cho chuẩn. | Viết Architecture & Tuning log. |
| **180-240'** | Hỗ trợ fix bug cuối. | Đóng gói code pipeline. | Chạy Eval, xuất Scorecard & Report. |

**Một lưu ý nhỏ:** Người số 3 nên là người có kỹ năng đọc hiểu văn bản tốt để soạn bộ câu hỏi "bẫy" (ví dụ: hỏi về những thông tin không có trong tài liệu để xem AI có biết từ chối không).

### User Input

vậy trong sprint 1, người 1 sẽ làm gì

### Planner Response

Trong **Sprint 1 (60 phút đầu tiên)**, Thành viên 1 là người đóng vai trò "mở đường". Nếu bạn không xong phần này, hai người còn lại sẽ không có dữ liệu để làm việc.

Công việc cụ thể của bạn nằm trong file **`index.py`**. Dưới đây là các bước bạn cần làm:

### 1. Cấu hình Embedding (Hàm `get_embedding`)
Bạn cần chọn một "động cơ" để biến văn bản thành vector. Thường có 2 lựa chọn:
*   **OpenAI:** Nhanh, chuẩn nhưng tốn phí (cần API Key).
*   **Sentence Transformers (Local):** Chạy trên máy mình, miễn phí nhưng nặng máy nếu RAM yếu.
*   **Nhiệm vụ:** Hoàn thiện code để khi gọi `get_embedding(text)` nó trả về một mảng số (vector).

### 2. Thiết kế chiến lược Chia nhỏ văn bản (Chunking)
Đây là phần cực kỳ quan trọng ảnh hưởng đến độ thông minh của AI:
*   **Chunk Size:** Bạn nên chia mỗi đoạn bao nhiêu từ? (VD: 300 từ).
*   **Overlap:** Có nên để đoạn sau gối đầu lên đoạn trước không? (VD: 50 từ). Nếu không có overlap, AI dễ bị mất ngữ cảnh ở giữa các đoạn cắt.
*   **Metadata:** Bạn phải trích xuất được thông tin từ tên file hoặc nội dung để gán vào từng đoạn (Ví dụ: đoạn này thuộc file `policy_refund.txt`, ngày hiệu lực là `2024-01-01`).

### 3. Đổ dữ liệu vào Database (Hàm `build_index`)
Bạn cần viết đoạn code để:
1.  Đọc tất cả file văn bản trong `data/docs/`.
2.  Cắt chúng ra thành các đoạn nhỏ (chunks).
3.  Biến mỗi đoạn thành vector (embedding).
4.  Lưu cả **Vector + Nội dung gốc + Metadata** vào ChromaDB.

### 4. Kiểm tra kết quả (Hàm `list_chunks` hoặc `query_test`)
Sau khi chạy xong, bạn phải chứng minh được dữ liệu đã vào kho:
*   Chạy câu lệnh `python index.py`.
*   Kết quả phải hiện ra được: "Đã index thành công 5 tài liệu thành 42 chunks".
*   Thử in ra 1 chunk bất kỳ để xem metadata có đầy đủ không.

**Mục tiêu cuối cùng của bạn trong Sprint 1:** Để lại một thư mục chứa database (thường là folder `chroma_db`) cho Thành viên 2 bắt đầu viết code tìm kiếm. Nếu bạn làm xong mục này sớm, hãy giúp Thành viên 2 cài đặt hàm `retrieve_dense` luôn.

### User Input

cho tôi công việc cụ thể của mỗi người trong sprint 1 để phân chia việc được nhanh nhất'

### Planner Response

Để khởi động nhanh nhất trong **Sprint 1 (60 phút đầu)**, hãy chia việc theo danh sách "To-Do" cụ thể dưới đây. Mỗi người tập trung vào file của mình, chỉ cần nói chuyện với nhau để thống nhất tên trường Metadata.

### 👤 Người 1: Làm sạch & Nạp dữ liệu (File `index.py`)
*   **Bước 1 (15'):** Mở `index.py`, hoàn thiện hàm `get_embedding`. Nếu dùng OpenAI thì điền `OpenAIEmbeddings()`.
*   **Bước 2 (20'):** Viết logic chia đoạn trong `build_index`. Gợi ý: `chunk_size=500`, `chunk_overlap=50`.
*   **Bước 3 (15'):** Trích xuất Metadata: Khi đọc file, lấy tên file làm trường `source`. Nếu được, quét trong văn bản lấy ngày hiệu lực làm `effective_date`.
*   **Bước 4 (10'):** Chạy `python index.py` để tạo ra folder `chroma_db`. 
*   **👉 Kết quả:** Có folder database chứa dữ liệu đã được vector hóa.

### 👤 Người 2: Cấu hình hệ thống & Kết nối AI (File `rag_answer.py`)
*   **Bước 1 (10'):** Tạo file `.env` từ `.env.example`, điền API Key. Đảm bảo Người 1 và Người 3 cũng có Key này.
*   **Bước 2 (20'):** Cài đặt hàm `call_llm` trong `rag_answer.py`. Viết một System Prompt cơ bản (VD: "Bạn là trợ lý IT Helpdesk, chỉ trả lời dựa trên thông tin được cung cấp...").
*   **Bước 3 (20'):** Viết hàm `retrieve_dense`. Đây là hàm dùng để hỏi database ("Câu hỏi này thì đoạn văn nào trong DB là phù hợp nhất?").
*   **Bước 4 (10'):** Chạy thử một câu lệnh gọi trực tiếp LLM (không cần DB) để đảm bảo API Key hoạt động.
*   **👉 Kết quả:** Hệ thống đã "biết nói" và có khung để lấy dữ liệu từ Người 1.

### 👤 Người 3: Soạn đề thi & Chuẩn bị đánh giá (File `data/test_questions.json`)
*   **Bước 1 (20'):** Đọc kỹ 5 file trong `data/docs/` (SLA, Refund, Access Control...). Hiểu rõ các con số (VD: SLA P1 là 4 giờ, hoàn tiền trong 30 ngày...).
*   **Bước 2 (20'):** Mở file `data/test_questions.json`, soạn 10 câu hỏi test. Với mỗi câu, bạn phải viết sẵn:
    *   `question`: Câu hỏi.
    *   `expected_answer`: Câu trả lời đúng là gì?
    *   `expected_source`: Nằm ở file nào?
*   **Bước 3 (10'):** Soạn thêm 2 câu hỏi "ngoài lề" (không có trong tài liệu) để test xem AI có biết từ chối trả lời không.
*   **Bước 4 (10'):** Đọc qua file `eval.py` để hiểu cách hệ thống sẽ chấm điểm sau này.
*   **👉 Kết quả:** Có "bộ đề thi" chuẩn để tí nữa chấm điểm cho Người 1 và Người 2.

---

### 💡 Mẹo nhỏ để không bị nghẽn:
*   **Người 1 & Người 2** phải thống nhất: "Tôi sẽ đặt tên trường chứa tên file là `source` nhé". 
*   **Người 3** có thể làm việc hoàn toàn độc lập mà không cần code của hai người kia xong.
*   Nếu **Người 2** cài đặt API xong sớm, hãy giúp **Người 1** viết hàm Embedding.

### User Input

giúp tôi thống nhất những gì chung của người 1 và 2, để tôi có thể archive cuộc hội thoại này cho 2 người còn lại

### Planner Response

Đây là **Bản Thỏa thuận Kỹ thuật (Technical Contract)** dùng chung cho Người 1 và Người 2. Hai bạn cần copy phần này để đảm bảo code của hai người khớp nhau ngay từ lần chạy đầu tiên:

---

### 📝 BẢN THỐNG NHẤT KỸ THUẬT (Dành cho Người 1 & Người 2)

Để hệ thống RAG hoạt động, hai bạn phải sử dụng chung các cấu hình sau:

#### 1. Mô hình Embedding (Bắt buộc giống nhau)
*   **Lựa chọn:** `text-embedding-3-small` (của OpenAI) hoặc `all-MiniLM-L6-v2` (của SentenceTransformers).
*   **Lý do:** Nếu Người 1 dùng model A để nạp dữ liệu, nhưng Người 2 dùng model B để tìm kiếm thì AI sẽ không bao giờ tìm thấy thông tin đúng (vector không khớp).

#### 2. Cấu trúc Database (ChromaDB)
*   **Tên Collection:** `helpdesk_policy` (Thống nhất đặt tên này trong code của cả 2 file).
*   **Đường dẫn lưu trữ:** `./chroma_db` (Mặc định).

#### 3. Quy chuẩn Metadata (Hợp đồng dữ liệu)
Khi Người 1 lưu dữ liệu, phải đặt tên các trường (keys) chính xác như sau để Người 2 có thể truy xuất và hiển thị nguồn:
*   `source`: Tên file gốc (VD: `policy_refund_v4.txt`).
*   `section`: Tên đề mục (nếu trích xuất được).
*   `effective_date`: Ngày hiệu lực (Dạng `YYYY-MM-DD`).
*   **Dữ liệu chính:** Lưu vào trường `text` (hoặc `page_content` tùy theo thư viện dùng).

#### 4. Cấu hình Môi trường (`.env`)
*   Cùng sử dụng chung các biến:
    *   `OPENAI_API_KEY=...` (Nếu dùng OpenAI)
    *   `GOOGLE_API_KEY=...` (Nếu dùng Gemini)
    *   `EMBEDDING_MODEL_NAME=...` (Để thống nhất model ở mục 1)

#### 5. Định dạng đầu ra của hàm Retrieval
Hàm `retrieve_dense` của Người 2 khi nhận dữ liệu từ database của Người 1 gửi sang LLM nên trả về một List các Dictionary có dạng:
```python
[
  {"content": "Nội dung đoạn văn...", "metadata": {"source": "SLA_P1.txt", "section": "1.1"}},
  ...
]
```

---

**Lời nhắn cho 2 bạn:**
*   **Người 1:** Khi xong việc, hãy báo cho Người 2: *"Đã tạo xong database với tên collection là helpdesk_policy, metadata có source và section"*.
*   **Người 2:** Khi bắt đầu viết code Retrieval, hãy kiểm tra xem mình đã gọi đúng tên model Embedding mà Người 1 đã dùng chưa.

--- 
*Chúc team Day 08 hoàn thành lab xuất sắc!*

### User Input

3 người lần lượt là Phước - người thứ 1, Hoài - người thứ 2, Huyền - người thứ 3, lát nữa khi mỗi người làm công việc của mình thì họ sẽ nói tên, có gì bạn sẽ hướng dẫn họ làm đúng phần việc của mình nhé

### Planner Response

Rất rõ ràng! Tôi đã ghi nhớ đội hình của team bạn:

1.  **Phước (Người thứ 1):** Chuyên gia Dữ liệu & Indexing. Phụ trách chính: `index.py`.
2.  **Huyền (Người thứ 2):** Chuyên gia AI & Pipeline. Phụ trách chính: `rag_answer.py`, Prompt Engineering.
3.  **Hoài (Người thứ 3):** Chuyên gia Kiểm định & Tài liệu. Phụ trách chính: `eval.py`, Bộ câu hỏi test và Báo cáo.

Tôi đã sẵn sàng. Khi bất kỳ ai trong 3 bạn (Phước, Hoài, hoặc Huyền) cần hỗ trợ, chỉ cần bắt đầu bằng cách nói: **"Tôi là [Tên], tôi đang làm phần việc của mình, hãy giúp tôi..."**. Tôi sẽ đưa ra hướng dẫn chi tiết và code mẫu chuẩn xác cho đúng phần việc của người đó.

Chúc ba bạn **Phước, Hoài và Huyền** phối hợp ăn ý và hoàn thành xuất sắc bài Lab này! Tôi đợi tin từ các bạn.

### User Input

bạn cũng cần chú ý tới phần SCORING nữa nhé

### Planner Response

tôi đã đọc file `SCORING.md`. Đây là những điểm **"sống còn"** để nhóm bạn đạt điểm tối đa (Grade A), tôi sẽ bám sát các tiêu chí này khi hướng dẫn:

### 1. Đối với Phước (Indexing - Chiếm trọng số lớn về nền tảng)
*   **Điểm tối đa khi:** Phải trích xuất được ít nhất **3 Metadata fields** (ví dụ: `source`, `section`, `date`). Nếu chỉ có mỗi text không sẽ bị trừ điểm.
*   **Kỹ thuật:** Phải xử lý được các ký tự đặc biệt và đảm bảo chunking không làm mất ngữ cảnh (không cắt giữa chừng một điều khoản quan trọng).

### 2. Đối với Huyền (Retrieval & Generation - Quyết định độ thông minh)
*   **Điểm tối đa khi:** 
    *   Hệ thống phải có cơ chế **"Abstain"** (Biết từ chối): Nếu câu hỏi không có trong tài liệu, AI phải nói "Tôi không biết" chứ không được bịa ra (Hallucination).
    *   **Citation (Trích dẫn):** Phải ghi rõ thông tin lấy từ file nào, đoạn nào.
    *   **Tuning:** Phải có ít nhất **một phiên bản nâng cao** (Hybrid Search hoặc Rerank) và so sánh được sự khác biệt với bản gốc.

### 3. Đối với Hoài (Evaluation & Documentation - Quyết định tính chuyên nghiệp)
*   **Điểm tối đa khi:**
    *   **Scorecard:** Phải có bảng điểm chi tiết cho cả 2 phiên bản (Baseline vs Variant).
    *   **Architecture:** Sơ đồ kiến trúc phải rõ ràng, đúng các bước thực tế trong code.
    *   **Báo cáo cá nhân:** Phải thể hiện được sự đóng góp và bài học rút ra (500-800 từ).

---

**🚩 CẢNH BÁO "MẤT ĐIỂM" CẦN TRÁNH:**
*   Quên không trích dẫn nguồn (No citations).
*   AI trả lời lan man, bịa đặt thêm thông tin ngoài context.
*   Cấu trúc thư mục bị xáo trộn, không chạy được bằng lệnh mẫu.

Tôi đã nắm rõ "luật chơi". **Phước, Huyền, Hoài** hãy cứ yên tâm triển khai, tôi sẽ kiểm soát chất lượng code để đảm bảo bài làm đúng theo rubric chấm điểm này!