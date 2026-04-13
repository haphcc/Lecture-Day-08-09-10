"""
index.py — Sprint 1: Build RAG Index
====================================
Mục tiêu Sprint 1 (60 phút):
  - Đọc và preprocess tài liệu từ data/docs/
  - Chunk tài liệu theo cấu trúc tự nhiên (heading/section)
  - Gắn metadata: source, section, department, effective_date, access
  - Embed và lưu vào vector store (ChromaDB)

Definition of Done Sprint 1:
  ✓ Script chạy được và index đủ docs
  ✓ Có ít nhất 3 metadata fields hữu ích cho retrieval
  ✓ Có thể kiểm tra chunk bằng list_chunks()
"""

import os
import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

# =============================================================================
# CẤU HÌNH
# =============================================================================

DOCS_DIR = Path(__file__).parent / "data" / "docs"
CHROMA_DB_DIR = Path(__file__).parent / "chroma_db"
COLLECTION_NAME = "rag_lab"
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "text-embedding-3-small")
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "").strip().lower()

# TODO Sprint 1: Điều chỉnh chunk size và overlap theo quyết định của nhóm
# Gợi ý từ slide: chunk 300-500 tokens, overlap 50-80 tokens
CHUNK_SIZE = 400       # tokens (ước lượng bằng số ký tự / 4)
CHUNK_OVERLAP = 80     # tokens overlap giữa các chunk


_OPENAI_CLIENT = None
_LOCAL_EMBEDDING_MODEL = None


# =============================================================================
# STEP 1: PREPROCESS
# Làm sạch text trước khi chunk và embed
# =============================================================================

def preprocess_document(raw_text: str, filepath: str) -> Dict[str, Any]:
    """
    Preprocess một tài liệu: extract metadata từ header và làm sạch nội dung.

    Args:
        raw_text: Toàn bộ nội dung file text
        filepath: Đường dẫn file để làm source mặc định

    Returns:
        Dict chứa:
          - "text": nội dung đã clean
          - "metadata": dict với source, department, effective_date, access

    TODO Sprint 1:
    - Extract metadata từ dòng đầu file (Source, Department, Effective Date, Access)
    - Bỏ các dòng header metadata khỏi nội dung chính
    - Normalize khoảng trắng, xóa ký tự rác

    Gợi ý: dùng regex để parse dòng "Key: Value" ở đầu file.
    """
    lines = raw_text.replace("\r\n", "\n").replace("\r", "\n").strip().split("\n")
    metadata = {
        "source": Path(filepath).name,
        "section": "",
        "department": "unknown",
        "effective_date": "unknown",
        "access": "internal",
    }
    content_lines = []
    header_done = False

    for line in lines:
        if not header_done:
            # TODO: Parse metadata từ các dòng "Key: Value"
            # Ví dụ: "Source: policy/refund-v4.pdf" → metadata["source"] = "policy/refund-v4.pdf"
            if line.startswith("Source:"):
                metadata["source"] = line.replace("Source:", "").strip()
            elif line.startswith("Department:"):
                metadata["department"] = line.replace("Department:", "").strip()
            elif line.startswith("Effective Date:"):
                metadata["effective_date"] = line.replace("Effective Date:", "").strip()
            elif line.startswith("Access:"):
                metadata["access"] = line.replace("Access:", "").strip()
            elif line.startswith("==="):
                # Gặp section heading đầu tiên → kết thúc header
                header_done = True
                content_lines.append(line)
            elif line.strip() == "" or line.isupper():
                # Dòng tên tài liệu (toàn chữ hoa) hoặc dòng trống
                continue
        else:
            content_lines.append(line.rstrip())

    cleaned_text = "\n".join(content_lines)

    # TODO: Thêm bước normalize text nếu cần
    # Gợi ý: bỏ ký tự đặc biệt thừa, chuẩn hóa dấu câu
    cleaned_text = re.sub(r"[ \t]+\n", "\n", cleaned_text)
    cleaned_text = re.sub(r"\n{3,}", "\n\n", cleaned_text)  # max 2 dòng trống liên tiếp
    cleaned_text = cleaned_text.strip()

    return {
        "text": cleaned_text,
        "metadata": metadata,
    }


# =============================================================================
# STEP 2: CHUNK
# Chia tài liệu thành các đoạn nhỏ theo cấu trúc tự nhiên
# =============================================================================

def chunk_document(doc: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Chunk một tài liệu đã preprocess thành danh sách các chunk nhỏ.

    Args:
        doc: Dict với "text" và "metadata" (output của preprocess_document)

    Returns:
        List các Dict, mỗi dict là một chunk với:
          - "text": nội dung chunk
          - "metadata": metadata gốc + "section" của chunk đó

    TODO Sprint 1:
    1. Split theo heading "=== Section ... ===" hoặc "=== Phần ... ===" trước
    2. Nếu section quá dài (> CHUNK_SIZE * 4 ký tự), split tiếp theo paragraph
    3. Thêm overlap: lấy đoạn cuối của chunk trước vào đầu chunk tiếp theo
    4. Mỗi chunk PHẢI giữ metadata đầy đủ từ tài liệu gốc

    Gợi ý: Ưu tiên cắt tại ranh giới tự nhiên (section, paragraph)
    thay vì cắt theo token count cứng.
    """
    text = doc["text"].strip()
    base_metadata = doc["metadata"].copy()
    chunks = []

    heading_pattern = re.compile(r"^===\s*(.*?)\s*===\s*$")
    current_section = "General"
    current_lines: List[str] = []

    def flush_section(section_name: str, section_lines: List[str]) -> None:
        section_text = "\n".join(section_lines).strip()
        if section_text:
            section_chunks = _split_by_size(
                section_text,
                base_metadata=base_metadata,
                section=section_name,
            )
            chunks.extend(section_chunks)

    for line in text.splitlines():
        match = heading_pattern.match(line.strip())
        if match:
            flush_section(current_section, current_lines)
            current_section = match.group(1).strip() or "General"
            current_lines = []
            continue
        current_lines.append(line)

    flush_section(current_section, current_lines)

    return chunks


def _split_by_size(
    text: str,
    base_metadata: Dict,
    section: str,
    chunk_chars: int = CHUNK_SIZE * 4,
    overlap_chars: int = CHUNK_OVERLAP * 4,
) -> List[Dict[str, Any]]:
    """
    Helper: Split text dài thành chunks với overlap.

    TODO Sprint 1:
    Hiện tại dùng split đơn giản theo ký tự.
    Cải thiện: split theo paragraph (\n\n) trước, rồi mới ghép đến khi đủ size.
    """
    if len(text) <= chunk_chars:
        return [{
            "text": text.strip(),
            "metadata": {**base_metadata, "section": section},
        }]

    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
    if not paragraphs:
        paragraphs = [text.strip()]

    raw_chunks: List[str] = []
    current_chunk = ""

    for paragraph in paragraphs:
        if not current_chunk:
            current_chunk = paragraph
            continue

        candidate = f"{current_chunk}\n\n{paragraph}"
        if len(candidate) <= chunk_chars:
            current_chunk = candidate
            continue

        raw_chunks.append(current_chunk.strip())
        current_chunk = paragraph

        if len(current_chunk) > chunk_chars:
            raw_chunks.extend(_split_long_text(current_chunk, chunk_chars, overlap_chars))
            current_chunk = ""

    if current_chunk.strip():
        raw_chunks.append(current_chunk.strip())

    chunks = []
    for chunk_text in raw_chunks:
        if not chunk_text:
            continue
        if len(chunk_text) > chunk_chars:
            chunks.extend(_split_long_text(chunk_text, chunk_chars, overlap_chars))
        else:
            chunks.append(chunk_text)

    return [
        {
            "text": chunk_text,
            "metadata": {**base_metadata, "section": section},
        }
        for chunk_text in chunks
        if chunk_text.strip()
    ]


def _split_long_text(text: str, chunk_chars: int, overlap_chars: int) -> List[str]:
    """
    Helper: cắt một đoạn quá dài bằng cửa sổ ký tự có overlap.
    """
    pieces: List[str] = []
    start = 0
    text = text.strip()

    while start < len(text):
        end = min(start + chunk_chars, len(text))

        if end < len(text):
            boundary_candidates = [
                text.rfind("\n\n", start, end),
                text.rfind(". ", start, end),
                text.rfind("\n", start, end),
            ]
            boundary = max(boundary_candidates)
            if boundary > start + max(120, chunk_chars // 2):
                if text[boundary:boundary + 2] == ". ":
                    end = boundary + 2
                else:
                    end = boundary + 1

        piece = text[start:end].strip()
        if piece:
            pieces.append(piece)

        if end >= len(text):
            break

        next_start = end - overlap_chars
        start = max(0, next_start)
        if start >= end:
            start = end

    return pieces


# =============================================================================
# STEP 3: EMBED + STORE
# Embed các chunk và lưu vào ChromaDB
# =============================================================================

def get_embedding(text: str) -> List[float]:
    """
    Tạo embedding vector cho một đoạn text.

    TODO Sprint 1:
    Chọn một trong hai:

    Option A — OpenAI Embeddings (cần OPENAI_API_KEY):
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.embeddings.create(
            input=text,
            model="text-embedding-3-small"
        )
        return response.data[0].embedding

    Option B — Sentence Transformers (chạy local, không cần API key):
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
        return model.encode(text).tolist()
    """
    if not text or not text.strip():
        raise ValueError("Text cho embedding không được rỗng.")

    provider = EMBEDDING_PROVIDER
    if provider not in {"openai", "sentence-transformers"}:
        provider = "openai" if os.getenv("OPENAI_API_KEY") else "sentence-transformers"

    if provider == "openai":
        client = _get_openai_client()
        response = client.embeddings.create(
            input=text,
            model=EMBEDDING_MODEL_NAME,
        )
        return list(response.data[0].embedding)

    model = _get_local_embedding_model()
    embedding = model.encode(text, normalize_embeddings=True)
    return embedding.tolist()


def _get_openai_client():
    global _OPENAI_CLIENT
    if _OPENAI_CLIENT is None:
        from openai import OpenAI

        _OPENAI_CLIENT = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _OPENAI_CLIENT


def _get_local_embedding_model():
    global _LOCAL_EMBEDDING_MODEL
    if _LOCAL_EMBEDDING_MODEL is None:
        from sentence_transformers import SentenceTransformer

        _LOCAL_EMBEDDING_MODEL = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
    return _LOCAL_EMBEDDING_MODEL


def build_index(docs_dir: Path = DOCS_DIR, db_dir: Path = CHROMA_DB_DIR) -> None:
    """
    Pipeline hoàn chỉnh: đọc docs → preprocess → chunk → embed → store.

    TODO Sprint 1:
    1. Cài thư viện: pip install chromadb
    2. Khởi tạo ChromaDB client và collection
    3. Với mỗi file trong docs_dir:
       a. Đọc nội dung
       b. Gọi preprocess_document()
       c. Gọi chunk_document()
       d. Với mỗi chunk: gọi get_embedding() và upsert vào ChromaDB
    4. In số lượng chunk đã index

    Gợi ý khởi tạo ChromaDB:
        import chromadb
        client = chromadb.PersistentClient(path=str(db_dir))
        collection = client.get_or_create_collection(
            name="rag_lab",
            metadata={"hnsw:space": "cosine"}
        )
    """
    import chromadb

    print(f"Đang build index từ: {docs_dir}")
    db_dir.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(db_dir))

    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    total_chunks = 0
    doc_files = list(docs_dir.glob("*.txt"))

    if not doc_files:
        print(f"Không tìm thấy file .txt trong {docs_dir}")
        return

    for filepath in doc_files:
        print(f"  Processing: {filepath.name}")
        raw_text = filepath.read_text(encoding="utf-8")
        doc = preprocess_document(raw_text, str(filepath))
        chunks = chunk_document(doc)
        ids = []
        embeddings = []
        documents = []
        metadatas = []

        for i, chunk in enumerate(chunks):
            chunk_text = chunk["text"].strip()
            if not chunk_text:
                continue

            chunk_id = f"{filepath.stem}_{i}"
            embedding = get_embedding(chunk_text)

            ids.append(chunk_id)
            embeddings.append(embedding)
            documents.append(chunk_text)
            metadatas.append({**chunk["metadata"], "chunk_id": chunk_id})

        if ids:
            collection.upsert(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas,
            )

        print(f"    → {len(ids)} chunks")
        total_chunks += len(ids)

    print(f"\nHoàn thành! Tổng số chunks: {total_chunks}")
    print(f"Collection ChromaDB: {COLLECTION_NAME}")


# =============================================================================
# STEP 4: INSPECT / KIỂM TRA
# Dùng để debug và kiểm tra chất lượng index
# =============================================================================

def list_chunks(db_dir: Path = CHROMA_DB_DIR, n: int = 5) -> None:
    """
    In ra n chunk đầu tiên trong ChromaDB để kiểm tra chất lượng index.

    TODO Sprint 1:
    Implement sau khi hoàn thành build_index().
    Kiểm tra:
    - Chunk có giữ đủ metadata không? (source, section, effective_date)
    - Chunk có bị cắt giữa điều khoản không?
    - Metadata effective_date có đúng không?
    """
    try:
        import chromadb
        client = chromadb.PersistentClient(path=str(db_dir))
        collection = client.get_collection(COLLECTION_NAME)
        results = collection.get(limit=n, include=["documents", "metadatas"])

        print(f"\n=== Top {n} chunks trong index ===\n")
        for i, (doc, meta) in enumerate(zip(results["documents"], results["metadatas"])):
            print(f"[Chunk {i+1}]")
            print(f"  Source: {meta.get('source', 'N/A')}")
            print(f"  Section: {meta.get('section', 'N/A')}")
            print(f"  Effective Date: {meta.get('effective_date', 'N/A')}")
            print(f"  Text preview: {doc[:120]}...")
            print()
    except Exception as e:
        print(f"Lỗi khi đọc index: {e}")
        print("Hãy chạy build_index() trước.")


def inspect_metadata_coverage(db_dir: Path = CHROMA_DB_DIR) -> None:
    """
    Kiểm tra phân phối metadata trong toàn bộ index.

    Checklist Sprint 1:
    - Mọi chunk đều có source?
    - Có bao nhiêu chunk từ mỗi department?
    - Chunk nào thiếu effective_date?

    TODO: Implement sau khi build_index() hoàn thành.
    """
    try:
        import chromadb
        client = chromadb.PersistentClient(path=str(db_dir))
        collection = client.get_collection(COLLECTION_NAME)
        results = collection.get(include=["metadatas"])

        print(f"\nTổng chunks: {len(results['metadatas'])}")

        # TODO: Phân tích metadata
        # Đếm theo department, kiểm tra effective_date missing, v.v.
        departments = {}
        missing_date = 0
        for meta in results["metadatas"]:
            dept = meta.get("department", "unknown")
            departments[dept] = departments.get(dept, 0) + 1
            if meta.get("effective_date") in ("unknown", "", None):
                missing_date += 1

        print("Phân bố theo department:")
        for dept, count in departments.items():
            print(f"  {dept}: {count} chunks")
        print(f"Chunks thiếu effective_date: {missing_date}")

    except Exception as e:
        print(f"Lỗi: {e}. Hãy chạy build_index() trước.")


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Sprint 1: Build RAG Index")
    print("=" * 60)

    # Bước 1: Kiểm tra docs
    doc_files = list(DOCS_DIR.glob("*.txt"))
    print(f"\nTìm thấy {len(doc_files)} tài liệu:")
    for f in doc_files:
        print(f"  - {f.name}")

    # Bước 2: Test preprocess và chunking (không cần API key)
    print("\n--- Test preprocess + chunking ---")
    for filepath in doc_files[:1]:  # Test với 1 file đầu
        raw = filepath.read_text(encoding="utf-8")
        doc = preprocess_document(raw, str(filepath))
        chunks = chunk_document(doc)
        print(f"\nFile: {filepath.name}")
        print(f"  Metadata: {doc['metadata']}")
        print(f"  Số chunks: {len(chunks)}")
        for i, chunk in enumerate(chunks[:3]):
            print(f"\n  [Chunk {i+1}] Section: {chunk['metadata']['section']}")
            print(f"  Text: {chunk['text'][:150]}...")

    # Bước 3: Build index (yêu cầu implement get_embedding)
    print("\n--- Build Full Index ---")
    try:
        build_index()
    except Exception as e:
        print(f"Không build được index: {e}")
        print("Hãy kiểm tra OPENAI_API_KEY hoặc cài sentence-transformers trong .venv.")

    # Bước 4: Kiểm tra index
    try:
        list_chunks()
        inspect_metadata_coverage()
    except Exception as e:
        print(f"Không kiểm tra được index: {e}")

    print("\nSprint 1 setup hoàn thành!")
    print("Việc cần làm:")
    print("  1. Kiểm tra collection rag_lab đã được tạo trong chroma_db")
    print("  2. Xem list_chunks() để xác nhận metadata source/section/effective_date")
    print("  3. Nếu chunking chưa tốt: điều chỉnh CHUNK_SIZE, CHUNK_OVERLAP")
