"""
Expectation suite đơn giản (không bắt buộc Great Expectations).

Sinh viên có thể thay bằng GE / pydantic / custom — miễn là có halt có kiểm soát.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple


@dataclass
class ExpectationResult:
    name: str
    passed: bool
    severity: str  # "warn" | "halt"
    detail: str


def run_expectations(cleaned_rows: List[Dict[str, Any]]) -> Tuple[List[ExpectationResult], bool]:
    """
    Trả về (results, should_halt).

    should_halt = True nếu có bất kỳ expectation severity halt nào fail.
    """
    results: List[ExpectationResult] = []
    now_utc = datetime.now(timezone.utc)

    # E1: có ít nhất 1 dòng sau clean
    ok = len(cleaned_rows) >= 1
    results.append(
        ExpectationResult(
            "min_one_row",
            ok,
            "halt",
            f"cleaned_rows={len(cleaned_rows)}",
        )
    )

    # E2: không doc_id rỗng
    bad_doc = [r for r in cleaned_rows if not (r.get("doc_id") or "").strip()]
    ok2 = len(bad_doc) == 0
    results.append(
        ExpectationResult(
            "no_empty_doc_id",
            ok2,
            "halt",
            f"empty_doc_id_count={len(bad_doc)}",
        )
    )

    # E3: policy refund không được chứa cửa sổ sai 14 ngày (sau khi đã fix)
    bad_refund = [
        r
        for r in cleaned_rows
        if r.get("doc_id") == "policy_refund_v4"
        and "14 ngày làm việc" in (r.get("chunk_text") or "")
    ]
    ok3 = len(bad_refund) == 0
    results.append(
        ExpectationResult(
            "refund_no_stale_14d_window",
            ok3,
            "halt",
            f"violations={len(bad_refund)}",
        )
    )

    # E4: chunk_text đủ dài
    short = [r for r in cleaned_rows if len((r.get("chunk_text") or "")) < 8]
    ok4 = len(short) == 0
    results.append(
        ExpectationResult(
            "chunk_min_length_8",
            ok4,
            "warn",
            f"short_chunks={len(short)}",
        )
    )

    # E5: effective_date đúng định dạng ISO sau clean (phát hiện parser lỏng)
    iso_bad = [
        r
        for r in cleaned_rows
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", (r.get("effective_date") or "").strip())
    ]
    ok5 = len(iso_bad) == 0
    results.append(
        ExpectationResult(
            "effective_date_iso_yyyy_mm_dd",
            ok5,
            "halt",
            f"non_iso_rows={len(iso_bad)}",
        )
    )

    # E6: không còn marker phép năm cũ 10 ngày trên doc HR (conflict version sau clean)
    bad_hr_annual = [
        r
        for r in cleaned_rows
        if r.get("doc_id") == "hr_leave_policy"
        and "10 ngày phép năm" in (r.get("chunk_text") or "")
    ]
    ok6 = len(bad_hr_annual) == 0
    results.append(
        ExpectationResult(
            "hr_leave_no_stale_10d_annual",
            ok6,
            "halt",
            f"violations={len(bad_hr_annual)}",
        )
    )

    # E7 (halt): cần giữ lại knowledge tối quan trọng cho policy_refund_v4
    # Nếu mất toàn bộ chunk refund thì pipeline phải dừng vì retrieval sẽ lệch nghiệp vụ.
    refund_rows = [r for r in cleaned_rows if r.get("doc_id") == "policy_refund_v4"]
    ok7 = len(refund_rows) >= 1
    results.append(
        ExpectationResult(
            "refund_doc_present",
            ok7,
            "halt",
            f"refund_rows={len(refund_rows)}",
        )
    )

    # E8 (warn): cảnh báo snapshot dữ liệu quá cũ theo exported_at (không dừng pipeline).
    stale_rows = 0
    max_age_hours = 0.0
    for row in cleaned_rows:
        raw_ts = (row.get("exported_at") or "").strip()
        if not raw_ts:
            stale_rows += 1
            continue
        try:
            parsed = datetime.fromisoformat(raw_ts.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            age_hours = (now_utc - parsed.astimezone(timezone.utc)).total_seconds() / 3600
            if age_hours > max_age_hours:
                max_age_hours = age_hours
            if age_hours > 48:
                stale_rows += 1
        except ValueError:
            stale_rows += 1
    ok8 = stale_rows == 0
    results.append(
        ExpectationResult(
            "exported_at_within_48h",
            ok8,
            "warn",
            f"stale_exported_at_rows={stale_rows}; max_age_hours={max_age_hours:.1f}",
        )
    )

    halt = any(not r.passed and r.severity == "halt" for r in results)
    return results, halt
