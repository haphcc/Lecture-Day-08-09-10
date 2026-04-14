"""
workers/policy_tool.py — Policy & Tool Worker
Sprint 2+3: Kiểm tra policy dựa vào context, gọi MCP tools khi cần.

Input (từ AgentState):
    - task: câu hỏi
    - retrieved_chunks: context từ retrieval_worker
    - needs_tool: True nếu supervisor quyết định cần tool call

Output (vào AgentState):
    - policy_result: {"policy_applies", "policy_name", "exceptions_found", "source", "rule"}
    - mcp_tools_used: list of tool calls đã thực hiện
    - worker_io_log: log

Gọi độc lập để test:
    python workers/policy_tool.py

# AI Lead: Sprint 2 — Rule-based + LLM hybrid policy analysis
# Quyết định thiết kế: Rule-based chạy trước (nhanh, deterministic) → LLM bổ sung
# phân tích phức tạp (temporal scoping, multi-condition). Lý do hybrid:
# - Flash Sale luôn = không hoàn tiền, không cần LLM xác nhận lại
# - LLM chỉ được gọi khi rule-based không đủ kết luận chắc chắn
"""

import os
import sys
from typing import Optional
import json
from urllib.request import Request, urlopen
from dotenv import load_dotenv

# Huyen - Worker owner

# Load biến môi trường từ .env
load_dotenv()

WORKER_NAME = "policy_tool_worker"


# ─────────────────────────────────────────────
# MCP Client — Sprint 3: Thay bằng real MCP call
# ─────────────────────────────────────────────

def _call_mcp_tool(tool_name: str, tool_input: dict) -> dict:
    """
    Gọi MCP tool.

    Sprint 3 TODO: Implement bằng cách import mcp_server hoặc gọi HTTP.

    Hiện tại: Import trực tiếp từ mcp_server.py (trong-process mock).
    """
    from datetime import datetime

    server_url = os.getenv("MCP_SERVER_URL", "").rstrip("/")

    if server_url:
        try:
            request = Request(
                f"{server_url}/tools/call",
                data=json.dumps({"tool_name": tool_name, "tool_input": tool_input}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urlopen(request, timeout=20) as response:
                payload = json.loads(response.read().decode("utf-8"))
            return {
                "tool": tool_name,
                "input": tool_input,
                "output": payload.get("result"),
                "error": None,
                "transport": "http",
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            print(f"[policy_tool] HTTP MCP call failed: {e}")

    try:
        from mcp_server import dispatch_tool
        result = dispatch_tool(tool_name, tool_input)
        return {
            "tool": tool_name,
            "input": tool_input,
            "output": result,
            "error": None,
            "transport": "in_process",
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        return {
            "tool": tool_name,
            "input": tool_input,
            "output": None,
            "error": {"code": "MCP_CALL_FAILED", "reason": str(e)},
            "transport": "in_process",
            "timestamp": datetime.now().isoformat(),
        }


# ─────────────────────────────────────────────
# LLM Helper — Auto-detect GPT hoặc Gemini
# ─────────────────────────────────────────────

def _call_llm_for_policy(task: str, chunks: list) -> str:
    """
    Gọi LLM để phân tích policy phức tạp.
    Tự động chọn provider dựa trên API key có sẵn trong môi trường:
      - Nếu có OPENAI_API_KEY  → ưu tiên dùng GPT-4o-mini
      - Nếu có GOOGLE_API_KEY → dùng Gemini 1.5 Flash
    Nếu không có key nào → trả về chuỗi rỗng (rule-based vẫn hoạt động)
    """
    context_text = "\n".join([f"[{i+1}] {c.get('text', '')}" for i, c in enumerate(chunks)])
    system_prompt = (
        "Bạn là policy analyst chuyên về chính sách hoàn tiền và cấp quyền nội bộ.\n"
        "Nhiệm vụ: Dựa HOÀN TOÀN vào context được cung cấp, xác định:\n"
        "1. Policy có áp dụng không? (True/False)\n"
        "2. Có exception nào không? (Flash Sale, digital product, đã kích hoạt, lỗi nhà sản xuất, temporal)\n"
        "3. Giải thích ngắn gọn lý do.\n"
        "KHÔNG bịa thông tin không có trong context."
    )
    user_msg = f"Task: {task}\n\nContext:\n{context_text}\n\nPhân tích policy:"

    # Option A: OpenAI GPT
    openai_key = os.getenv("OPENAI_API_KEY", "")
    if openai_key and openai_key.startswith("sk-"):
        try:
            from openai import OpenAI
            client = OpenAI(api_key=openai_key)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_msg},
                ],
                temperature=0.0,
                max_tokens=300,
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"[policy_tool] OpenAI call failed: {e}")

    # Option B: Google Gemini
    google_key = os.getenv("GOOGLE_API_KEY", "")
    if google_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=google_key)
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(f"{system_prompt}\n\n{user_msg}")
            return response.text
        except Exception as e:
            print(f"[policy_tool] Gemini call failed: {e}")

    # Fallback: không có LLM, rule-based đảm nhận
    print("[policy_tool] No LLM available — using rule-based only.")
    return ""


# ─────────────────────────────────────────────
# Policy Analysis Logic
# ─────────────────────────────────────────────

def analyze_policy(task: str, chunks: list) -> dict:
    """
    Phân tích policy dựa trên context chunks.
    Chiến lược Hybrid:
      1. Rule-based: phát hiện exceptions rõ ràng (nhanh, deterministic)
      2. LLM: phân tích cases phức tạp không rule-based nào bắt được

    Exceptions được detect:
    - Flash Sale → không được hoàn tiền (override mọi điều kiện khác)
    - Digital product / license key / subscription → không hoàn tiền
    - Sản phẩm đã kích hoạt → không hoàn tiền
    - Lỗi nhà sản xuất → hoàn tiền TRỪU KHI Flash Sale override
    - Đơn hàng trước 01/02/2026 → policy v3 (không có trong docs → abstain)

    Returns:
        dict with: policy_applies, policy_name, exceptions_found, source,
                   policy_version_note, explanation, llm_analysis
    """
    task_lower = task.lower()
    context_text = " ".join([c.get("text", "") for c in chunks]).lower()

    # ── Bước 1: Rule-based exception detection (chạy trước, nhanh) ──
    exceptions_found = []

    # Exception 1: Flash Sale — override mọi điều kiện hoàn tiền
    is_flash_sale = "flash sale" in task_lower or "flash sale" in context_text
    if is_flash_sale:
        exceptions_found.append({
            "type": "flash_sale_exception",
            "rule": "Đơn hàng Flash Sale không được hoàn tiền (Điều 3, chính sách v4). Override mọi điều kiện khác.",
            "source": "policy_refund_v4.txt",
        })

    # Exception 2: Digital product
    if any(kw in task_lower for kw in ["license key", "license", "subscription", "kỹ thuật số"]):
        exceptions_found.append({
            "type": "digital_product_exception",
            "rule": "Sản phẩm kỹ thuật số (license key, subscription) không được hoàn tiền (Điều 3).",
            "source": "policy_refund_v4.txt",
        })

    # Exception 3: Activated product
    if any(kw in task_lower for kw in ["đã kích hoạt", "đã đăng ký", "đã sử dụng"]):
        exceptions_found.append({
            "type": "activated_exception",
            "rule": "Sản phẩm đã kích hoạt hoặc đăng ký tài khoản không được hoàn tiền (Điều 3).",
            "source": "policy_refund_v4.txt",
        })

    # Exception 4: Manufacturer defect — hoàn tiền được NẾU không có exception khác
    is_manufacturer_defect = any(
        kw in task_lower for kw in ["lỗi nhà sản xuất", "lỗi sản xuất", "manufacturer defect", "lỗi do nhà sản xuất"]
    )
    if is_manufacturer_defect and not is_flash_sale:
        # Lỗi nhà sản xuất + không Flash Sale → ghi nhận nhưng KHÔNG block hoàn tiền
        exceptions_found.append({
            "type": "manufacturer_defect_eligible",
            "rule": "Sản phẩm lỗi nhà sản xuất đủ điều kiện hoàn tiền nếu trong 7 ngày và chưa kích hoạt.",
            "source": "policy_refund_v4.txt",
            "allows_refund": True,  # exception này KHÔNG block hoàn tiền
        })
    elif is_manufacturer_defect and is_flash_sale:
        # Lỗi nhà sản xuất + Flash Sale → Flash Sale override, vẫn không hoàn tiền
        exceptions_found.append({
            "type": "manufacturer_defect_blocked_by_flash_sale",
            "rule": "Dù lỗi nhà sản xuất, đơn Flash Sale vẫn không được hoàn tiền (Flash Sale override).",
            "source": "policy_refund_v4.txt",
            "allows_refund": False,
        })

    # ── Bước 2: Temporal scoping ──
    policy_name = "refund_policy_v4"
    policy_version_note = ""
    temporal_keywords = ["31/01", "30/01", "29/01", "trước 01/02", "trước tháng 2"]
    if any(kw in task_lower for kw in temporal_keywords):
        policy_version_note = (
            "Đơn hàng đặt trước 01/02/2026 áp dụng chính sách v3 "
            "(không có trong tài liệu hiện tại — cần xác nhận với team CS)."
        )

    # ── Bước 3: Xác định policy_applies ──
    # policy_applies = False nếu có BẤT KỲ exception nào KHÔNG có allows_refund=True
    blocking_exceptions = [
        e for e in exceptions_found
        if not e.get("allows_refund", False)
    ]
    policy_applies = len(blocking_exceptions) == 0

    sources = list({c.get("source", "unknown") for c in chunks if c})

    # ── Bước 4: LLM analysis cho cases phức tạp (bổ sung, không override rule-based) ──
    llm_analysis = ""
    # Gọi LLM nếu có chunks và task có vẻ phức tạp (nhiều điều kiện)
    has_complex_conditions = any(
        kw in task_lower
        for kw in ["và", "hoặc", "nếu", "điều kiện", "exception", "ngoại lệ"]
    )
    if chunks and (has_complex_conditions or not exceptions_found):
        llm_analysis = _call_llm_for_policy(task, chunks)

    return {
        "policy_applies": policy_applies,
        "policy_name": policy_name,
        "exceptions_found": exceptions_found,
        "source": sources,
        "policy_version_note": policy_version_note,
        "llm_analysis": llm_analysis,
        "explanation": (
            f"Rule-based: {len(exceptions_found)} exception(s) found. "
            f"Blocking: {len(blocking_exceptions)}. "
            f"LLM supplemented: {'yes' if llm_analysis else 'no'}."
        ),
    }


# ─────────────────────────────────────────────
# Worker Entry Point
# ─────────────────────────────────────────────

def run(state: dict) -> dict:
    """
    Worker entry point — gọi từ graph.py.

    Args:
        state: AgentState dict

    Returns:
        Updated AgentState với policy_result và mcp_tools_used
    """
    task = state.get("task", "")
    chunks = state.get("retrieved_chunks", [])
    needs_tool = state.get("needs_tool", False)

    state.setdefault("workers_called", [])
    state.setdefault("history", [])
    state.setdefault("mcp_tools_used", [])
    state.setdefault("mcp_tool_called", [])
    state.setdefault("mcp_result", [])

    state["workers_called"].append(WORKER_NAME)

    worker_io = {
        "worker": WORKER_NAME,
        "input": {
            "task": task,
            "chunks_count": len(chunks),
            "needs_tool": needs_tool,
        },
        "output": None,
        "error": None,
    }

    try:
        # Step 1: Nếu chưa có chunks, gọi MCP search_kb
        if not chunks and needs_tool:
            mcp_result = _call_mcp_tool("search_kb", {"query": task, "top_k": 3})
            state["mcp_tools_used"].append(mcp_result)
            state["mcp_tool_called"].append("search_kb")
            state["mcp_result"].append(mcp_result)
            state["history"].append(f"[{WORKER_NAME}] called MCP search_kb")

            if mcp_result.get("output") and mcp_result["output"].get("chunks"):
                chunks = mcp_result["output"]["chunks"]
                state["retrieved_chunks"] = chunks

        # Step 2: Phân tích policy
        policy_result = analyze_policy(task, chunks)
        state["policy_result"] = policy_result

        # Step 3: Nếu cần thêm info từ MCP (e.g., ticket status), gọi get_ticket_info
        if needs_tool and any(kw in task.lower() for kw in ["ticket", "p1", "jira"]):
            mcp_result = _call_mcp_tool("get_ticket_info", {"ticket_id": "P1-LATEST"})
            state["mcp_tools_used"].append(mcp_result)
            state["mcp_tool_called"].append("get_ticket_info")
            state["mcp_result"].append(mcp_result)
            state["history"].append(f"[{WORKER_NAME}] called MCP get_ticket_info")

        worker_io["output"] = {
            "policy_applies": policy_result["policy_applies"],
            "exceptions_count": len(policy_result.get("exceptions_found", [])),
            "mcp_calls": len(state["mcp_tools_used"]),
        }
        state["history"].append(
            f"[{WORKER_NAME}] policy_applies={policy_result['policy_applies']}, "
            f"exceptions={len(policy_result.get('exceptions_found', []))}"
        )

    except Exception as e:
        worker_io["error"] = {"code": "POLICY_CHECK_FAILED", "reason": str(e)}
        state["policy_result"] = {"error": str(e)}
        state["history"].append(f"[{WORKER_NAME}] ERROR: {e}")

    state.setdefault("worker_io_logs", []).append(worker_io)
    return state


# ─────────────────────────────────────────────
# Test độc lập
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 50)
    print("Policy Tool Worker — Standalone Test")
    print("=" * 50)

    test_cases = [
        {
            "task": "Khách hàng Flash Sale yêu cầu hoàn tiền vì sản phẩm lỗi — được không?",
            "retrieved_chunks": [
                {"text": "Ngoại lệ: Đơn hàng Flash Sale không được hoàn tiền.", "source": "policy_refund_v4.txt", "score": 0.9}
            ],
        },
        {
            "task": "Khách hàng muốn hoàn tiền license key đã kích hoạt.",
            "retrieved_chunks": [
                {"text": "Sản phẩm kỹ thuật số (license key, subscription) không được hoàn tiền.", "source": "policy_refund_v4.txt", "score": 0.88}
            ],
        },
        {
            "task": "Khách hàng yêu cầu hoàn tiền trong 5 ngày, sản phẩm lỗi, chưa kích hoạt.",
            "retrieved_chunks": [
                {"text": "Yêu cầu trong 7 ngày làm việc, sản phẩm lỗi nhà sản xuất, chưa dùng.", "source": "policy_refund_v4.txt", "score": 0.85}
            ],
        },
    ]

    for tc in test_cases:
        print(f"\n▶ Task: {tc['task'][:70]}...")
        result = run(tc.copy())
        pr = result.get("policy_result", {})
        print(f"  policy_applies: {pr.get('policy_applies')}")
        if pr.get("exceptions_found"):
            for ex in pr["exceptions_found"]:
                print(f"  exception: {ex['type']} — {ex['rule'][:60]}...")
        print(f"  MCP calls: {len(result.get('mcp_tools_used', []))}")

    print("\n✅ policy_tool_worker test done.")
