"""
rag_answer.py — Sprint 2 + Sprint 3: Retrieval & Grounded Answer
================================================================
Sprint 2 (60 phút): Baseline RAG
  - Dense retrieval từ ChromaDB (collection: helpdesk_policy)
  - Grounded answer function với prompt ép citation
  - Trả lời được ít nhất 3 câu hỏi mẫu, output có source

Sprint 3 (60 phút): Tuning — Variant: Rerank (Cross-Encoder)
  - Dense search rộng (top-10) → Cross-Encoder rerank → lấy top-3
  - Cross-Encoder model: cross-encoder/ms-marco-MiniLM-L-6-v2
  - Tạo bảng so sánh baseline vs variant

Definition of Done Sprint 2:
  ✓ rag_answer("SLA ticket P1?") trả về câu trả lời có citation [1]
  ✓ rag_answer("Câu hỏi không có trong docs") trả về abstain
  ✓ Output có sources field không rỗng

Definition of Done Sprint 3:
  ✓ rerank() chạy được với CrossEncoder
  ✓ compare_retrieval_strategies() in bảng baseline vs rerank
  ✓ Giải thích được tại sao chọn rerank
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv(override=True)

# =============================================================================
# CẤU HÌNH
# =============================================================================

# Đường dẫn ChromaDB — lấy từ index.py
CHROMA_DB_DIR = Path(__file__).parent / "chroma_db"

# Tên collection lấy từ index.py
COLLECTION_NAME = "rag_lab"

TOP_K_SEARCH = 10    # Số chunk lấy từ vector store trước rerank (search rộng)
TOP_K_SELECT = 3     # Số chunk gửi vào prompt sau rerank/select (top-3 sweet spot)

# LLM provider + model (đọc từ .env)
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini").strip().lower()
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

# Cache Cross-Encoder model để tránh load lại mỗi lần gọi
_CROSS_ENCODER_MODEL = None


def _load_cross_encoder_model():
    """
    Load the cross-encoder once.

    Strategy:
      1. Try local cache first for offline runs.
      2. If not cached, try downloading once.
      3. Return None only if both attempts fail.
    """
    from sentence_transformers import CrossEncoder

    model_name = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    try:
        return CrossEncoder(model_name, local_files_only=True)
    except Exception:
        pass

    try:
        return CrossEncoder(model_name)
    except Exception as e:
        print(f"[rerank] Không load được model '{model_name}' cả local lẫn online: {e}")
        return None


# =============================================================================
# EMBEDDING — dùng chung hàm từ index.py (local sentence-transformers)
# =============================================================================

def _get_query_embedding(query: str) -> List[float]:
    """
    Embed query bằng cùng model đã dùng khi index (local sentence-transformers).
    Import từ index.py để đảm bảo nhất quán.
    """
    try:
        from index import get_embedding
        return get_embedding(query)
    except ImportError:
        raise RuntimeError(
            "Không import được get_embedding từ index.py. "
            "Hãy chắc chắn index.py nằm cùng thư mục với rag_answer.py."
        )


# =============================================================================
# RETRIEVAL — DENSE (Vector Search)
# =============================================================================

def retrieve_dense(query: str, top_k: int = TOP_K_SEARCH) -> List[Dict[str, Any]]:
    """
    Dense retrieval: tìm kiếm theo embedding similarity trong ChromaDB.

    Args:
        query: Câu hỏi của người dùng
        top_k: Số chunk tối đa trả về

    Returns:
        List các dict, mỗi dict là:
          - "content": nội dung chunk
          - "metadata": {"source": ..., "section": ..., "effective_date": ...}
          - "score": cosine similarity score (0.0 - 1.0)
    """
    import chromadb

    # Kết nối ChromaDB
    client = chromadb.PersistentClient(path=str(CHROMA_DB_DIR))

    try:
        collection = client.get_collection(COLLECTION_NAME)
    except Exception:
        raise RuntimeError(
            f"Không tìm thấy collection '{COLLECTION_NAME}' trong ChromaDB tại {CHROMA_DB_DIR}.\n"
            "Hãy chạy index.py trước để build index."
        )

    # Embed query bằng cùng model đã dùng khi index (local)
    query_embedding = _get_query_embedding(query)

    # Query ChromaDB
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    # Chuyển về format thống nhất
    # ChromaDB cosine distance: distance = 1 - similarity → score = 1 - distance
    chunks = []
    docs = results["documents"][0]
    metas = results["metadatas"][0]
    distances = results["distances"][0]

    for doc_text, meta, distance in zip(docs, metas, distances):
        score = 1.0 - distance  # cosine similarity
        chunks.append({
            "content": doc_text,
            "metadata": {
                "source": meta.get("source", "unknown"),
                "section": meta.get("section", ""),
                "effective_date": meta.get("effective_date", "unknown"),
                "department": meta.get("department", "unknown"),
                "access": meta.get("access", "internal"),
            },
            "score": round(score, 4),
        })

    return chunks


# =============================================================================
# RETRIEVAL — SPARSE / BM25 (Sprint 3 — không chọn variant này)
# =============================================================================

def retrieve_sparse(query: str, top_k: int = TOP_K_SEARCH) -> List[Dict[str, Any]]:
    """
    Sparse retrieval: BM25 keyword search.
    Sprint 3 variant của nhóm là Rerank, không phải Hybrid.
    Hàm này giữ nguyên placeholder để không phá interface.
    """
    print("[retrieve_sparse] Không implement — Sprint 3 variant là Rerank.")
    return []


# =============================================================================
# RETRIEVAL — HYBRID (fallback về dense)
# =============================================================================

def retrieve_hybrid(
    query: str,
    top_k: int = TOP_K_SEARCH,
    dense_weight: float = 0.6,
    sparse_weight: float = 0.4,
) -> List[Dict[str, Any]]:
    """
    Hybrid retrieval — Sprint 3 variant của nhóm là Rerank, không phải Hybrid.
    Fallback về dense để không phá interface.
    """
    print("[retrieve_hybrid] Fallback về dense (variant đã chọn là Rerank).")
    return retrieve_dense(query, top_k)


# =============================================================================
# RERANK — Cross-Encoder (Sprint 3 Variant)
# Funnel: Dense top-10 → Cross-Encoder rerank → lấy top-3
# =============================================================================

def rerank(
    query: str,
    candidates: List[Dict[str, Any]],
    top_k: int = TOP_K_SELECT,
) -> List[Dict[str, Any]]:
    """
    Rerank các candidate chunks bằng Cross-Encoder.

    Cross-Encoder chấm lại từng cặp (query, chunk_text) và chọn ra top_k
    chunk thực sự relevant nhất — lọc noise tốt hơn cosine similarity đơn thuần.

    Model dùng: cross-encoder/ms-marco-MiniLM-L-6-v2
    (nhỏ gọn, chạy local, không cần API key)

    Sprint 3 — Lý do chọn Rerank thay vì Hybrid:
      - Corpus helpdesk có cả câu tự nhiên và keyword (SLA, P1, ERR-403)
      - Dense search bắt được context ngữ nghĩa tốt
      - Rerank giúp lọc top-3 chính xác hơn từ top-10 dense
      - Đặc biệt hiệu quả cho câu gq06 (cross-doc multi-hop, 12 điểm)

    Args:
        query: Câu hỏi gốc
        candidates: List chunks từ dense search (top-10)
        top_k: Số chunk giữ lại sau rerank

    Returns:
        Top-k chunks được rerank, vẫn giữ format {"content", "metadata", "score"}
    """
    global _CROSS_ENCODER_MODEL

    if not candidates:
        return []

    try:
        from sentence_transformers import CrossEncoder
    except ImportError:
        print("[rerank] sentence-transformers chưa cài. pip install sentence-transformers")
        return candidates[:top_k]

    # Load model một lần duy nhất (cache)
    if _CROSS_ENCODER_MODEL is None:
        print("[rerank] Đang load Cross-Encoder model lần đầu...")
        _CROSS_ENCODER_MODEL = _load_cross_encoder_model()
        if _CROSS_ENCODER_MODEL is None:
            print("[rerank] Fallback: dùng dense top-k.")
            return candidates[:top_k]

    # Tạo pairs (query, chunk_text) để chấm
    pairs = [[query, chunk["content"]] for chunk in candidates]

    # Chấm điểm relevance
    try:
        scores = _CROSS_ENCODER_MODEL.predict(pairs)
    except Exception as e:
        print(f"[rerank] Predict lỗi ({e}). Fallback: dùng dense top-k.")
        return candidates[:top_k]

    # Sort theo score giảm dần và lấy top_k
    ranked = sorted(
        zip(candidates, scores),
        key=lambda x: x[1],
        reverse=True,
    )

    # Trả về top-k, thêm rerank_score vào metadata để debug
    result = []
    for chunk, rerank_score in ranked[:top_k]:
        enriched = dict(chunk)
        enriched["rerank_score"] = round(float(rerank_score), 4)
        result.append(enriched)

    return result


# =============================================================================
# QUERY TRANSFORMATION (Sprint 3 — không chọn variant này)
# =============================================================================

def transform_query(query: str, strategy: str = "expansion") -> List[str]:
    """
    Query transformation — nhóm chọn Rerank làm Sprint 3 variant.
    Trả về query gốc để không phá interface.
    """
    return [query]


# =============================================================================
# GENERATION — BUILD CONTEXT BLOCK
# =============================================================================

def build_context_block(chunks: List[Dict[str, Any]]) -> str:
    """
    Đóng gói danh sách chunks thành context block để đưa vào prompt.

    Mỗi chunk có số thứ tự [1], [2], ... để model dễ trích dẫn.
    Format: [số] source | section | effective_date | score=...
    """
    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        meta = chunk.get("metadata", {})
        source = meta.get("source", "unknown")
        section = meta.get("section", "")
        effective_date = meta.get("effective_date", "")
        department = meta.get("department", "")
        access = meta.get("access", "")
        score = chunk.get("score", 0)

        # Header với đầy đủ metadata
        header_parts = [f"[{i}] {source}"]
        if section:
            header_parts.append(section)
        if department and department != "unknown":
            header_parts.append(f"dept: {department}")
        if effective_date and effective_date != "unknown":
            header_parts.append(f"effective: {effective_date}")
        if access and access != "internal":
            header_parts.append(f"access: {access}")
        if score > 0:
            header_parts.append(f"score={score:.3f}")

        header = " | ".join(header_parts)
        content = chunk.get("content", "")

        context_parts.append(f"{header}\n{content}")

    return "\n\n".join(context_parts)


# =============================================================================
# GENERATION — SYSTEM PROMPT + GROUNDED USER PROMPT
# =============================================================================

SYSTEM_PROMPT = """You are an internal helpdesk assistant for CS and IT support.
Your job is to answer questions strictly based on the provided policy documents.

Rules you MUST follow:
1. EVIDENCE ONLY: Answer only using information from the retrieved context below. Do not use your own knowledge.
2. ABSTAIN: If the context does not contain enough information to answer the question, respond with: "Thông tin này không có trong tài liệu được cung cấp."
3. CITATION: Always cite the source using its bracket number, e.g. [1], [2]. Every factual claim must have a citation.
4. NO HALLUCINATION: Never invent numbers, names, dates, or procedures not found in the context. This is the most critical rule.
5. LANGUAGE: Respond in the same language as the question (Vietnamese or English).
6. BREVITY: Keep your answer short, clear, and factual. No unnecessary padding."""


def build_grounded_prompt(query: str, context_block: str) -> str:
    """
    Xây dựng user prompt: Context + Question.
    System rules được tách riêng trong SYSTEM_PROMPT để gửi qua API đúng cách.
    """
    prompt = f"""Context:
{context_block}

Question: {query}

Answer (cite sources like [1], abstain if not in context):"""
    return prompt


# =============================================================================
# GENERATION — CALL LLM (OpenAI hoặc Gemini)
# =============================================================================

def call_llm(system_prompt: str, user_prompt: str) -> str:
    """
    Gọi LLM theo LLM_PROVIDER trong .env.

    Hỗ trợ:
      - openai: Chat Completions API
      - gemini: Google Generative AI SDK

    temperature=0 để output ổn định, dễ đánh giá.
    """
    provider = LLM_PROVIDER

    if provider == "openai":
        from openai import OpenAI

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("Thiếu OPENAI_API_KEY trong file .env.")

        model_name = LLM_MODEL
        client = OpenAI(api_key=api_key)

        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.0,
                max_tokens=512,
            )
            content = response.choices[0].message.content or ""
            return content.strip()
        except Exception as e:
            return f"[ERROR] Lỗi gọi OpenAI: {e}"

    if provider == "gemini":
        import google.generativeai as genai
        from google.api_core import exceptions

        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError("Thiếu GOOGLE_API_KEY trong file .env.")

        genai.configure(api_key=api_key)

        model_name = GEMINI_MODEL
        if not model_name.startswith("models/"):
            model_name = f"models/{model_name}"

        try:
            model = genai.GenerativeModel(
                model_name=model_name,
                system_instruction=system_prompt,
            )

            response = model.generate_content(
                user_prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.0,
                    max_output_tokens=512,
                ),
            )
            return (response.text or "").strip()

        except exceptions.NotFound as e:
            return f"[ERROR] Model '{model_name}' không tìm thấy (404). Hãy kiểm tra lại GEMINI_MODEL trong .env hoặc API Key có quyền truy cập model này không. Chi tiết: {e}"
        except Exception as e:
            return f"[ERROR] Lỗi gọi Gemini: {e}"

    raise RuntimeError("LLM_PROVIDER không hợp lệ. Hãy dùng 'openai' hoặc 'gemini' trong .env.")


# =============================================================================
# PIPELINE CHÍNH — rag_answer()
# =============================================================================

def rag_answer(
    query: str,
    retrieval_mode: str = "dense",
    top_k_search: int = TOP_K_SEARCH,
    top_k_select: int = TOP_K_SELECT,
    use_rerank: bool = False,
    verbose: bool = False,
) -> Dict[str, Any]:
    """
    Pipeline RAG hoàn chỉnh: query → retrieve → (rerank) → generate.

    Args:
        query: Câu hỏi
        retrieval_mode: "dense" | "sparse" | "hybrid"
        top_k_search: Số chunk lấy từ vector store (search rộng, default 10)
        top_k_select: Số chunk đưa vào prompt (sau rerank/select, default 3)
        use_rerank: Có dùng Cross-Encoder rerank không (Sprint 3)
        verbose: In thêm thông tin debug

    Returns:
        Dict với:
          - "query": query gốc
          - "answer": câu trả lời grounded có citation
          - "sources": list source names đã dùng
          - "chunks_used": list chunks đưa vào prompt
          - "config": cấu hình pipeline đã dùng
    """
    config = {
        "retrieval_mode": retrieval_mode,
        "top_k_search": top_k_search,
        "top_k_select": top_k_select,
        "use_rerank": use_rerank,
    }

    # --- Bước 1: Retrieve ---
    if retrieval_mode == "dense":
        candidates = retrieve_dense(query, top_k=top_k_search)
    elif retrieval_mode == "sparse":
        candidates = retrieve_sparse(query, top_k=top_k_search)
    elif retrieval_mode == "hybrid":
        candidates = retrieve_hybrid(query, top_k=top_k_search)
    else:
        raise ValueError(f"retrieval_mode không hợp lệ: '{retrieval_mode}'. Chọn: dense | sparse | hybrid")

    if verbose:
        print(f"\n[RAG] Query: {query}")
        print(f"[RAG] Retrieved {len(candidates)} candidates (mode={retrieval_mode})")
        for i, c in enumerate(candidates[:5]):
            print(f"  [{i+1}] score={c.get('score', 0):.3f} | {c['metadata'].get('source', '?')} | {c['metadata'].get('section', '')}")

    # --- Bước 2: Rerank (Sprint 3 variant) ---
    if use_rerank:
        candidates = rerank(query, candidates, top_k=top_k_select)
        if verbose:
            print(f"[RAG] After Cross-Encoder rerank: {len(candidates)} chunks")
            for i, c in enumerate(candidates):
                print(f"  [{i+1}] rerank_score={c.get('rerank_score', 'N/A')} | {c['metadata'].get('source', '?')}")
    else:
        candidates = candidates[:top_k_select]

    if verbose:
        print(f"[RAG] Chunks sent to LLM: {len(candidates)}")

    # --- Bước 3: Build context và prompt ---
    context_block = build_context_block(candidates)
    user_prompt = build_grounded_prompt(query, context_block)

    if verbose:
        print(f"\n[RAG] Context block preview:\n{context_block[:400]}...\n")

    # --- Bước 4: Generate với Gemini ---
    answer = call_llm(SYSTEM_PROMPT, user_prompt)

    # --- Bước 5: Extract sources ---
    sources = list({
        c["metadata"].get("source", "unknown")
        for c in candidates
    })

    return {
        "query": query,
        "answer": answer,
        "sources": sources,
        "chunks_used": candidates,
        "config": config,
    }


# =============================================================================
# SPRINT 3: SO SÁNH BASELINE VS VARIANT (Dense vs Dense + Rerank)
# =============================================================================

def compare_retrieval_strategies(query: str) -> None:
    """
    So sánh baseline (dense only) vs variant (dense + rerank).

    Chạy hàm này để thấy sự khác biệt và justify lý do chọn Rerank.
    A/B Rule: chỉ thay đổi MỘT biến (use_rerank=True/False).
    """
    print(f"\n{'='*65}")
    print(f"Query: {query}")
    print(f"{'='*65}")

    variants = [
        ("Baseline — Dense only",        {"retrieval_mode": "dense", "use_rerank": False}),
        ("Variant — Dense + Rerank",      {"retrieval_mode": "dense", "use_rerank": True}),
    ]

    results_table = []

    for label, kwargs in variants:
        print(f"\n--- {label} ---")
        try:
            result = rag_answer(query, verbose=False, **kwargs)
            answer_preview = result["answer"][:200].replace("\n", " ")
            sources_str = ", ".join(result["sources"])
            n_chunks = len(result["chunks_used"])

            print(f"  Answer : {answer_preview}{'...' if len(result['answer']) > 200 else ''}")
            print(f"  Sources: {sources_str}")
            print(f"  Chunks : {n_chunks}")

            results_table.append({
                "variant": label,
                "answer_len": len(result["answer"]),
                "sources": sources_str,
                "chunks": n_chunks,
            })

        except NotImplementedError as e:
            print(f"  Chưa implement: {e}")
        except Exception as e:
            print(f"  Lỗi: {e}")

    # In bảng so sánh ngắn gọn
    if len(results_table) == 2:
        print(f"\n{'='*65}")
        print("BẢNG SO SÁNH")
        print(f"{'Variant':<35} {'Sources':<40} {'Chunks'}")
        print("-" * 85)
        for row in results_table:
            print(f"{row['variant']:<35} {row['sources']:<40} {row['chunks']}")
        print(f"{'='*65}")


# =============================================================================
# MAIN — Demo và Test
# =============================================================================

if __name__ == "__main__":
    print("=" * 65)
    print("Sprint 2 + 3: RAG Answer Pipeline — Gemini + Local Embedding")
    print(f"Collection: {COLLECTION_NAME} | DB: {CHROMA_DB_DIR}")
    print("=" * 65)

    # ---- Sprint 2: Test Baseline (Dense, không rerank) ----
    print("\n" + "=" * 65)
    print("SPRINT 2: Baseline Dense Retrieval")
    print("=" * 65)

    test_queries = [
        "SLA xử lý ticket P1 là bao lâu?",
        "Khách hàng có thể yêu cầu hoàn tiền trong bao nhiêu ngày?",
        "Ai phải phê duyệt để cấp quyền Level 3?",
        "ERR-403-AUTH là lỗi gì?",   # Không có trong docs → kiểm tra abstain
    ]

    for query in test_queries:
        print(f"\n[Query] {query}")
        try:
            result = rag_answer(query, retrieval_mode="dense", use_rerank=False, verbose=True)
            print(f"[Answer] {result['answer']}")
            print(f"[Sources] {result['sources']}")
        except Exception as e:
            print(f"[ERROR] {e}")

    # ---- Sprint 3: So sánh Dense vs Dense + Rerank ----
    print("\n\n" + "=" * 65)
    print("SPRINT 3: So sánh Baseline vs Rerank Variant")
    print("=" * 65)

    sprint3_queries = [
        "Ai phải phê duyệt để cấp quyền Level 3?",      # Multi-section → rerank giúp nhiều
        "P1 lúc 2am thì cấp quyền tạm thời thế nào?",   # Cross-doc → rerank giúp nhiều
    ]

    for query in sprint3_queries:
        compare_retrieval_strategies(query)
