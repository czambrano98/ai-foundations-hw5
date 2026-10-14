"""Append-only audit trail for agent runs.

Every agent-loop stop (top-level or delegated) appends one AuditEntry to
output/audit_trail.json. The file is a JSON array that GROWS across runs — we
append, we never wipe it — so the whole history is auditable later.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Optional

from .models import AuditEntry, ToolCallRecord
from .settings import AUDIT_PATH, MODEL_NAME


def _extract_tool_calls(result: Any) -> list[ToolCallRecord]:
    """Pull tool-call parts out of a pydantic-ai run result, defensively."""
    calls: list[ToolCallRecord] = []
    try:
        for message in result.all_messages():
            for part in getattr(message, "parts", []):
                if getattr(part, "part_kind", None) == "tool-call":
                    args = getattr(part, "args", None)
                    if isinstance(args, str):
                        try:
                            args = json.loads(args)
                        except Exception:
                            args = {"raw": args}
                    calls.append(ToolCallRecord(tool=getattr(part, "tool_name", "?"),
                                                args=args or {}))
    except Exception:
        pass
    return calls


def _extract_usage(result: Any) -> dict:
    try:
        u = result.usage  # pydantic-ai 2.x: `usage` is a property (RunUsage)
        return {
            "requests": getattr(u, "requests", None),
            "input_tokens": getattr(u, "input_tokens", None),
            "output_tokens": getattr(u, "output_tokens", None),
            "total_tokens": getattr(u, "total_tokens", None),
            "tool_calls": getattr(u, "tool_calls", None),
        }
    except Exception:
        return {}


def append_audit(entry: AuditEntry) -> None:
    """Append one entry to the audit trail JSON array (creating it if needed)."""
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    if AUDIT_PATH.exists():
        try:
            existing = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
            if not isinstance(existing, list):
                existing = [existing]
        except Exception:
            existing = []
    else:
        existing = []
    existing.append(entry.model_dump())
    AUDIT_PATH.write_text(json.dumps(existing, indent=2), encoding="utf-8")


def record_run(
    *,
    run_id: str,
    agent: str,
    task: str,
    result: Any,
    shop_date: Optional[str] = None,
    delegated_from: Optional[str] = None,
    usage: Optional[dict] = None,
) -> AuditEntry:
    """Build an AuditEntry from a finished agent run and append it.

    Pass `usage` to record this agent's OWN token delta (excluding work it
    delegated out); if omitted, falls back to the run's cumulative usage.
    """
    output = getattr(result, "output", None)
    summary = getattr(output, "summary", None) or str(output or "")
    entry = AuditEntry(
        run_id=run_id,
        ts=datetime.now(timezone.utc).isoformat(),
        shop_date=shop_date,
        agent=agent,
        delegated_from=delegated_from,
        task=task,
        model=MODEL_NAME,
        tool_calls=_extract_tool_calls(result),
        output_summary=summary,
        needs_human_approval=bool(getattr(output, "needs_human_approval", False)),
        resolved=bool(getattr(output, "resolved", False)),
        usage=usage if usage is not None else _extract_usage(result),
    )
    append_audit(entry)
    return entry
