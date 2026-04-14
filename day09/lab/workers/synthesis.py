"""
workers/synthesis.py — Synthesis Worker
Sprint 2: Tổng hợp câu trả lời từ retrieved_chunks và policy_result.

Input (từ AgentState):
    - task: câu hỏi
    - retrieved_chunks: evidence từ retrieval_worker
    - policy_result: kết quả từ policy_tool_worker

Output (vào AgentState):
    - final_answer: câu trả lời cuối với citation
    - sources: danh sách nguồn tài liệu được cite
    - confidence: mức độ tin cậy (0.0 - 1.0)

Gọi độc lập để test:
    python workers/synthesis.py
"""

import os
from dotenv import load_dotenv

# Load biến môi trường từ .env
load_dotenv()

WORKER_NAME = "synthesis_worker"

# AI Lead: Sprint 2 — Grounded synthesis với strict no-hallucinate + HITL trigger
SYSTEM_PROMPT = """Bạn là trợ lý IT Helpdesk nội bộ.

Quy tắc nghiêm ngặt:
1. CHỈ trả lời dựa vào context được cung cấp bên dưới. TUYỆT ĐỐI KHÔNG dùng kiến thức ngoài.
2. Nếu context KHÔNG CÓ thông tin để trả lời → bắt buộc viết:
   "Không tìm thấy thông tin này trong tài liệu nội bộ. Vui lòng liên hệ CS team để xác nhận."
3. Trích dẫn nguồn SAU MỖI thông tin quan trọng theo dạng [tên_file].
   Ví dụ: Ticket P1 có SLA phản hồi 15 phút [sla_p1_2026.txt].
4. Trả lời súc tích, có cấu trúc. Không dài dòng, không thêm thông tin không có trong context.
5. Nếu có exceptions/ngoại lệ → nêu rõ TRƯỚC khi đưa ra kết luận.
6. Kết thúc bằng dòng: Độ tin cậy: [CAO/TRUNG BÌNH/THẤP] — [lý do ngắn gọn]
"""


def _call_llm(messages: list) -> str:
    """
    Gọi LLM để tổng hợp câu trả lời.
    TODO Sprint 2: Implement với OpenAI hoặc Gemini.
    """
    # Option A: OpenAI
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.1,  # Low temperature để grounded
            max_tokens=500,
        )
        return response.choices[0].message.content
    except Exception:
        pass

    # Option B: Gemini
    try:
        import google.generativeai as genai
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        model = genai.GenerativeModel("gemini-1.5-flash")
        combined = "\n".join([m["content"] for m in messages])
        response = model.generate_content(combined)
        return response.text
    except Exception:
        pass

    # Fallback: trả về message báo lỗi (không hallucinate)
    return "[SYNTHESIS ERROR] Không thể gọi LLM. Kiểm tra API key trong .env."


def _build_context(chunks: list, policy_result: dict) -> str:
    """Xây dựng context string từ chunks và policy result."""
    parts = []

    if chunks:
        parts.append("=== TÀI LIỆU THAM KHẢO ===")
        for i, chunk in enumerate(chunks, 1):
            source = chunk.get("source", "unknown")
            text = chunk.get("text", "")
            score = chunk.get("score", 0)
            parts.append(f"[{i}] Nguồn: {source} (relevance: {score:.2f})\n{text}")

    if policy_result and policy_result.get("exceptions_found"):
        parts.append("\n=== POLICY EXCEPTIONS ===")
        for ex in policy_result["exceptions_found"]:
            parts.append(f"- {ex.get('rule', '')}")

    if not parts:
        return "(Không có context)"

    return "\n\n".join(parts)


def _estimate_confidence(chunks: list, answer: str, policy_result: dict) -> float:
    """
    Ước tính confidence dựa vào:
    - Số lượng và quality của chunks (avg cosine similarity)
    - Answer có abstain không
    - Có blocking exceptions không (phức tạp hơn → penalty nhỏ)

    Ngưỡng:
      < 0.4 → HITL triggered (cần human review)
      0.4-0.7 → trả lời nhưng low-confidence
      > 0.7 → high confidence
    """
    if not chunks:
        return 0.1  # Không có evidence → very low

    abstain_signals = [
        "không tìm thấy thông tin",
        "không đủ thông tin",
        "không có trong tài liệu",
        "vui lòng liên hệ",
    ]
    if any(sig in answer.lower() for sig in abstain_signals):
        return 0.25  # Abstain → low nhưng không phải 0 (worker đã hoạt động đúng)

    # Weighted average của chunk relevance scores
    avg_score = sum(c.get("score", 0) for c in chunks) / len(chunks)

    # Penalty nếu có blocking exceptions (policy phức tạp → kém chắc chắn hơn)
    blocking_exceptions = [
        e for e in policy_result.get("exceptions_found", [])
        if not e.get("allows_refund", False)
    ]
    exception_penalty = 0.05 * len(blocking_exceptions)

    # Bonus nếu có policy_version_note (temporal scoping, cần thêm thông tin)
    temporal_penalty = 0.1 if policy_result.get("policy_version_note") else 0

    confidence = min(0.95, avg_score - exception_penalty - temporal_penalty)
    return round(max(0.1, confidence), 2)


def synthesize(task: str, chunks: list, policy_result: dict) -> dict:
    """
    Tổng hợp câu trả lời từ chunks và policy context.

    Returns:
        {"answer": str, "sources": list, "confidence": float}
    """
    context = _build_context(chunks, policy_result)

    # Build messages
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"""Câu hỏi: {task}

{context}

Hãy trả lời câu hỏi dựa vào tài liệu trên."""
        }
    ]

    answer = _call_llm(messages)
    sources = list({c.get("source", "unknown") for c in chunks})
    confidence = _estimate_confidence(chunks, answer, policy_result)

    return {
        "answer": answer,
        "sources": sources,
        "confidence": confidence,
    }


def run(state: dict) -> dict:
    """
    Worker entry point — gọi từ graph.py.
    Ghi thêm hitl_triggered vào state nếu confidence < 0.4.
    """
    task = state.get("task", "")
    chunks = state.get("retrieved_chunks", [])
    policy_result = state.get("policy_result", {})

    state.setdefault("workers_called", [])
    state.setdefault("history", [])
    state.setdefault("hitl_triggered", False)
    state["workers_called"].append(WORKER_NAME)

    HITL_THRESHOLD = 0.4  # Ngưỡng confidence để trigger human review

    worker_io = {
        "worker": WORKER_NAME,
        "input": {
            "task": task,
            "chunks_count": len(chunks),
            "has_policy": bool(policy_result),
        },
        "output": None,
        "error": None,
    }

    try:
        result = synthesize(task, chunks, policy_result)
        state["final_answer"] = result["answer"]
        state["sources"] = result["sources"]
        state["confidence"] = result["confidence"]

        # HITL trigger: nếu confidence thấp → flag cần human review
        if result["confidence"] < HITL_THRESHOLD:
            state["hitl_triggered"] = True
            state["history"].append(
                f"[{WORKER_NAME}] ⚠️ HITL triggered: confidence={result['confidence']} < {HITL_THRESHOLD}"
            )

        worker_io["output"] = {
            "answer_length": len(result["answer"]),
            "sources": result["sources"],
            "confidence": result["confidence"],
            "hitl_triggered": state["hitl_triggered"],
        }
        state["history"].append(
            f"[{WORKER_NAME}] answer generated, confidence={result['confidence']}, "
            f"sources={result['sources']}, hitl={state['hitl_triggered']}"
        )

    except Exception as e:
        worker_io["error"] = {"code": "SYNTHESIS_FAILED", "reason": str(e)}
        state["final_answer"] = f"SYNTHESIS_ERROR: {e}"
        state["confidence"] = 0.0
        state["hitl_triggered"] = True  # Lỗi → luôn trigger HITL
        state["history"].append(f"[{WORKER_NAME}] ERROR: {e}")

    state.setdefault("worker_io_logs", []).append(worker_io)
    return state


# ─────────────────────────────────────────────
# Test độc lập
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 50)
    print("Synthesis Worker — Standalone Test")
    print("=" * 50)

    test_state = {
        "task": "SLA ticket P1 là bao lâu?",
        "retrieved_chunks": [
            {
                "text": "Ticket P1: Phản hồi ban đầu 15 phút kể từ khi ticket được tạo. Xử lý và khắc phục 4 giờ. Escalation: tự động escalate lên Senior Engineer nếu không có phản hồi trong 10 phút.",
                "source": "sla_p1_2026.txt",
                "score": 0.92,
            }
        ],
        "policy_result": {},
    }

    result = run(test_state.copy())
    print(f"\nAnswer:\n{result['final_answer']}")
    print(f"\nSources: {result['sources']}")
    print(f"Confidence: {result['confidence']}")

    print("\n--- Test 2: Exception case ---")
    test_state2 = {
        "task": "Khách hàng Flash Sale yêu cầu hoàn tiền vì lỗi nhà sản xuất.",
        "retrieved_chunks": [
            {
                "text": "Ngoại lệ: Đơn hàng Flash Sale không được hoàn tiền theo Điều 3 chính sách v4.",
                "source": "policy_refund_v4.txt",
                "score": 0.88,
            }
        ],
        "policy_result": {
            "policy_applies": False,
            "exceptions_found": [{"type": "flash_sale_exception", "rule": "Flash Sale không được hoàn tiền."}],
        },
    }
    result2 = run(test_state2.copy())
    print(f"\nAnswer:\n{result2['final_answer']}")
    print(f"Confidence: {result2['confidence']}")

    print("\n✅ synthesis_worker test done.")
