"""The Campus Customs agent team.

Five PydanticAI agents -- Boss, Inventory, Accounting, Facilities, Customer
Service -- all running the same model (gpt-6-luna via Portkey). They share one
tool layer: the MCP server, loaded straight from `.mcp.json`, so every shop fact
and action goes through MCP with no second, bypassing tool layer.

Connectivity is full: every agent carries a `delegate` tool and can hand a
sub-task to any other agent. Each agent-loop stop (top-level or delegated) is
appended to output/audit_trail.json.

Nothing here touches the network at import time. Agents are built lazily on the
first call to `get_agents()`, which needs PORTKEY_API_KEY.
"""

from __future__ import annotations

import asyncio
import json
import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from pydantic_ai import Agent, RunContext
from pydantic_ai.exceptions import UsageLimitExceeded
from pydantic_ai.mcp import MCPToolset, StdioTransport
from pydantic_ai.usage import UsageLimits

from .audit import append_audit, record_run
from .models import AgentDecision, AuditEntry
from .settings import (
    AGENT_TOOL_RETRIES,
    HW5_ROOT,
    MAX_DELEGATIONS_PER_RUN,
    MAX_DELEGATION_DEPTH,
    MAX_REQUESTS_PER_RUN,
    MCP_CONFIG_PATH,
    MCP_INIT_TIMEOUT,
    MODEL_NAME,
    build_model,
)

PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"
AGENT_NAMES = ["boss", "inventory", "accounting", "facilities", "customer_service"]


@dataclass
class RunBudget:
    """Mutable, shared across one board run to cap delegations and total requests."""
    delegations_left: int
    max_requests: int
    requests_used: int = 0


@dataclass
class ShopDeps:
    """Context carried through a board run and its delegations."""
    run_id: str
    shop_date: Optional[str] = None
    depth: int = 0
    chain: tuple[str, ...] = ()          # agents already in this delegation path
    budget: Optional[RunBudget] = None   # shared delegation + request cap for the run


async def _run_and_record(agent: Agent, name: str, task: str, deps: "ShopDeps",
                          delegated_from: Optional[str]):
    """Run one agent and audit its OWN usage.

    Each agent run uses its OWN usage object (we do NOT share one across the
    team), so `result.usage` is exactly this agent-loop's own token/request
    delta -- no bracketing, which would be wrong because pydantic-ai runs an
    agent's tool calls (including delegations) concurrently. The global ceiling
    is kept separately via `budget`: each run is limited to the requests still
    remaining in the whole-run budget, and we add what it used afterward.
    """
    budget = deps.budget
    remaining = max(1, budget.max_requests - budget.requests_used) if budget else MAX_REQUESTS_PER_RUN
    result = await agent.run(
        task, deps=deps, usage_limits=UsageLimits(request_limit=remaining),
    )
    if budget is not None:
        budget.requests_used += getattr(result.usage, "requests", 0) or 0
    record_run(run_id=deps.run_id, agent=name, task=task, result=result,
               shop_date=deps.shop_date, delegated_from=delegated_from)
    return result


def _load_prompt(name: str) -> str:
    return (PROMPTS_DIR / f"{name}.md").read_text(encoding="utf-8")


def _build_mcp_toolsets() -> list:
    """Build MCP toolsets from .mcp.json with a generous init timeout.

    Mirrors pydantic-ai's `load_mcp_toolsets` but sets a longer `init_timeout`
    (the FastMCP server cold-starts slowly on Windows) and `keep_alive=True` so
    the server process starts once and is reused across every agent and
    delegation instead of cold-starting each time. `.mcp.json` stays the single
    source of truth for the server command.
    """
    cfg = json.loads(MCP_CONFIG_PATH.read_text(encoding="utf-8"))
    toolsets = []
    for name, server in cfg["mcpServers"].items():
        command = server["command"]
        if not os.path.isabs(command):
            # Resolve relative to the project root so the server spawns no matter
            # the parent's cwd (e.g. uvicorn launched from backend/).
            command = str((HW5_ROOT / command).resolve())
        transport = StdioTransport(
            command=command,
            args=list(server.get("args") or []),
            cwd=str(HW5_ROOT),
            keep_alive=True,
        )
        toolset = MCPToolset(transport, id=name, init_timeout=MCP_INIT_TIMEOUT,
                             read_timeout=MCP_INIT_TIMEOUT).prefixed(name)
        toolsets.append(toolset)
    return toolsets


# Filled by get_agents(); the delegate tools resolve targets through it so any
# agent can reach any other (full connectivity).
REGISTRY: dict[str, Agent] = {}


def _make_delegate(source: str):
    """Build the `delegate` tool for one agent, tagging audits with its name."""

    async def delegate(ctx: RunContext[ShopDeps], to_agent: str, task: str) -> str:
        """Delegate a sub-task to another Campus Customs agent and return its summary.

        `to_agent` must be one of: boss, inventory, accounting, facilities,
        customer_service. Use this only when the work genuinely belongs to
        another specialist (e.g. Inventory asking Accounting to clear a blocking
        invoice). Do NOT delegate back to an agent that is already handling this
        chain, and prefer answering from your own tools when you can.
        """
        target_name = to_agent.strip().lower()
        if target_name not in REGISTRY:
            return f"unknown agent '{to_agent}'. choose one of: {', '.join(REGISTRY)}"
        if target_name == source:
            return f"refused: {source} cannot delegate to itself"
        # Break cycles: full connectivity means A->B->A is possible; forbid it.
        if target_name in ctx.deps.chain:
            return (f"refused: {target_name} is already in this delegation chain "
                    f"({' -> '.join(ctx.deps.chain)}); answer from your own tools instead")
        if ctx.deps.depth >= MAX_DELEGATION_DEPTH:
            return "refused: max delegation depth reached (keeping token use in check)"
        budget = ctx.deps.budget
        if budget is not None and budget.delegations_left <= 0:
            return "refused: delegation budget for this run is used up; wrap up with your own tools"
        if budget is not None and budget.requests_used >= budget.max_requests:
            return "refused: run request budget is used up; wrap up with your own tools"
        if budget is not None:
            budget.delegations_left -= 1

        child = ShopDeps(
            run_id=ctx.deps.run_id, shop_date=ctx.deps.shop_date,
            depth=ctx.deps.depth + 1, chain=ctx.deps.chain + (target_name,), budget=budget,
        )
        try:
            result = await _run_and_record(
                REGISTRY[target_name], target_name, task, child, delegated_from=source)
        except UsageLimitExceeded:
            return "stopped: the run request budget was reached; returning control"
        return result.output.summary

    return delegate


def get_agents() -> dict[str, Agent]:
    """Build (once) and return the five agents, fully wired for delegation."""
    if REGISTRY:
        return REGISTRY

    model = build_model()
    toolsets = _build_mcp_toolsets()  # shared MCP tool layer (single server, kept alive)

    for name in AGENT_NAMES:
        REGISTRY[name] = Agent(
            model,
            name=name,
            deps_type=ShopDeps,
            output_type=AgentDecision,
            instructions=_load_prompt(name),
            toolsets=toolsets,
            retries=AGENT_TOOL_RETRIES,
        )
    # Full connectivity: give every agent a delegate tool over all the others.
    for name, agent in REGISTRY.items():
        agent.tool(_make_delegate(name))
    return REGISTRY


async def _fetch_shop_date() -> Optional[str]:
    """Read desk.date_today through the MCP server (not a bypass) for audit metadata."""
    from fastmcp import Client

    cfg = json.loads(MCP_CONFIG_PATH.read_text(encoding="utf-8"))
    server = cfg["mcpServers"]["campus-customs"]
    command = server["command"]
    if not os.path.isabs(command):
        command = str((HW5_ROOT / command).resolve())
    # cwd must be the project root so the (relative) server script arg resolves.
    transport = StdioTransport(command=command, args=list(server.get("args") or []), cwd=str(HW5_ROOT))
    try:
        async with Client(transport) as client:
            res = await client.call_tool("get_desk_date", {})
            data = res.data
            return data.get("date_today") if isinstance(data, dict) else None
    except Exception:
        return None


async def run_agent(name: str, task: str) -> AgentDecision:
    """Run a single named agent on a task and audit the loop stop."""
    agents = get_agents()
    if name not in agents:
        raise ValueError(f"unknown agent '{name}'")
    run_id = uuid.uuid4().hex[:12]
    shop_date = await _fetch_shop_date()
    deps = ShopDeps(run_id=run_id, shop_date=shop_date, depth=0, chain=(name,),
                    budget=RunBudget(delegations_left=MAX_DELEGATIONS_PER_RUN,
                                     max_requests=MAX_REQUESTS_PER_RUN))
    try:
        result = await _run_and_record(agents[name], name, task, deps, delegated_from=None)
    except UsageLimitExceeded as e:
        # Budget guardrail tripped: stop cleanly with a partial result + audit,
        # rather than crashing the whole run.
        decision = AgentDecision(
            summary=f"Run stopped early: {e}. Some tickets may be unresolved; "
                    f"re-run or raise CAMPUS_MAX_REQUESTS if needed.",
            needs_human_approval=True, resolved=False,
        )
        append_audit(AuditEntry(
            run_id=run_id, ts=datetime.now(timezone.utc).isoformat(), shop_date=shop_date,
            agent=name, task=task, model=MODEL_NAME, output_summary=decision.summary,
            needs_human_approval=True, resolved=False,
        ))
        return decision
    # _run_and_record already appended the audit entry with this agent's own usage.
    return result.output


async def resolve_board(task: Optional[str] = None) -> AgentDecision:
    """Entry point: hand the whole open board to the Boss to triage and resolve."""
    prompt = task or (
        "Triage every OPEN ticket on the board and resolve each one within the "
        "shop rules. Delegate to the right specialist agents. Never move money "
        "without human approval, and never spend into a negative balance."
    )
    return await run_agent("boss", prompt)


if __name__ == "__main__":
    # Manual smoke run (requires PORTKEY_API_KEY). Builds nothing without it.
    decision = asyncio.run(resolve_board())
    print(decision.model_dump_json(indent=2))
