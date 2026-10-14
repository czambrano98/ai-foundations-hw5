"""Campus Customs backend API (FastAPI).

Serves the React dashboard. Start it from the backend/ folder with:

    uvicorn main:app --reload --port 8000

Routes:
  GET  /tickets                 list the tickets and whether each is open/resolved
  POST /tickets/{id}/run        run the agent team on one ticket
  GET  /events                  recent agent events (what each agent said + tools used)
  POST /approve                 human approves a payment/purchase -> actually moves cash
  GET  /cash                    current checking balance
  POST /reset                   reset the working db to the original values

Everything that touches shop state goes through the ONE MCP server (a persistent
client opened in the app lifespan), so there is no second tool layer that
bypasses it. The agents only *prepare* payments; `/approve` is the only path that
actually changes cash, by calling the guarded pay_invoice / pay_rent tools.
"""

from __future__ import annotations

import asyncio
import json
import os
import shutil
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal, Optional

# Make the `backend` package importable no matter where uvicorn is launched from
# (the start command runs `main:app` from inside backend/).
HW5_ROOT = Path(__file__).resolve().parent.parent
if str(HW5_ROOT) not in sys.path:
    sys.path.insert(0, str(HW5_ROOT))

from fastapi import FastAPI, HTTPException  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from pydantic import BaseModel  # noqa: E402
from fastmcp import Client  # noqa: E402
from fastmcp.client.transports import StdioTransport  # noqa: E402

from backend.agents import run_agent  # noqa: E402

PRISTINE_DB = HW5_ROOT / "data" / "campus_customs.db"
WORKING_DB = HW5_ROOT / "data" / "campus_customs_new.db"
AUDIT_PATH = HW5_ROOT / "output" / "audit_trail.json"
MCP_CONFIG = HW5_ROOT / ".mcp.json"


def _mcp_transport() -> StdioTransport:
    """Build the stdio transport for the campus-customs server from .mcp.json.

    Resolves the (relative) command to an absolute path and pins cwd to the
    project root so it works regardless of where uvicorn is started.
    """
    cfg = json.loads(MCP_CONFIG.read_text(encoding="utf-8"))
    server = cfg["mcpServers"]["campus-customs"]
    command = server["command"]
    if not os.path.isabs(command):
        command = str((HW5_ROOT / command).resolve())
    return StdioTransport(command=command, args=list(server.get("args") or []),
                          cwd=str(HW5_ROOT), keep_alive=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Open one persistent MCP client for the server's lifetime."""
    client = Client(_mcp_transport())
    await client.__aenter__()
    app.state.mcp = client
    app.state.mcp_lock = asyncio.Lock()  # serialize calls over the single stdio pipe
    try:
        yield
    finally:
        await client.__aexit__(None, None, None)


app = FastAPI(title="Campus Customs Backend", lifespan=lifespan)

# The dashboard runs on a different origin in dev; allow it to call us.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


async def mcp_call(tool: str, args: dict) -> dict:
    """Call one MCP tool through the shared client (serialized)."""
    async with app.state.mcp_lock:
        result = await app.state.mcp.call_tool(tool, args)
    return result.data


# --------------------------------------------------------------------------- #
# Routes                                                                       #
# --------------------------------------------------------------------------- #

@app.get("/")
async def root():
    return {"status": "ok", "service": "campus-customs-backend"}


@app.get("/tickets")
async def get_tickets():
    """Return every ticket with a simple open/resolved flag for the board."""
    data = await mcp_call("list_tickets", {})
    tickets = []
    for t in data.get("tickets", []):
        tickets.append({
            "id": t["id"],
            "type": t["type"],
            "subject": t["subject"],
            "requester": t["requester"],
            "status": t["status"],
            "resolved": t["status"] == "resolved",
            "sku": t.get("sku"),
            "size": t.get("size"),
            "qty": t.get("qty"),
            "lease_id": t.get("lease_id"),      # for rent approvals
            "invoice_id": t.get("invoice_id"),  # for invoice approvals
            "notes": t.get("notes"),
        })
    return {"count": len(tickets), "tickets": tickets}


@app.post("/tickets/{ticket_id}/run")
async def run_ticket(ticket_id: int):
    """Run the agent team (Boss triages, then delegates) on one ticket."""
    exists = await mcp_call("get_ticket", {"ticket_id": ticket_id})
    if not exists.get("found"):
        raise HTTPException(status_code=404, detail=f"ticket {ticket_id} not found")
    ticket = exists["ticket"]

    task = (
        f"Resolve open ticket {ticket_id} within the shop rules. Read the ticket, "
        f"delegate to the right specialist agent(s) only, and never move money "
        f"without human approval. Prepare any payment or purchase as a draft for a "
        f"human to approve; do not pay."
    )
    decision = await run_agent("boss", task)

    # Decide the lifecycle DETERMINISTICALLY from pending payables, not just the
    # model's self-reported flag: a ticket with unpaid rent or an open linked
    # invoice awaits human approval; otherwise the run resolves it.
    awaiting = False
    if ticket["type"] == "rent_notice" and ticket.get("lease_id"):
        awaiting = True  # rent still needs a human to approve the payment
    elif ticket["type"] == "customer_order" and ticket.get("invoice_id"):
        open_inv = await mcp_call("list_open_invoices", {})
        awaiting = any(i["id"] == ticket["invoice_id"] for i in open_inv.get("invoices", []))
    new_status = "awaiting_approval" if (awaiting or decision.needs_human_approval) else "resolved"
    await mcp_call("update_ticket", {
        "ticket_id": ticket_id,
        "status": new_status,
        "notes": f"[run complete] {decision.summary[:300]}",
    })
    return {"ticket_id": ticket_id, "decision": decision.model_dump(), "status": new_status}


@app.get("/events")
async def get_events(limit: int = 50):
    """Return recent agent events from the audit trail (newest last)."""
    if not AUDIT_PATH.exists():
        return {"count": 0, "events": []}
    try:
        entries = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    except Exception:
        entries = []
    recent = entries[-limit:] if limit and limit > 0 else entries
    events = []
    for e in recent:
        events.append({
            "ts": e.get("ts"),
            "run_id": e.get("run_id"),
            "agent": e.get("agent"),
            "delegated_from": e.get("delegated_from"),
            "said": e.get("output_summary"),
            "tools_used": [tc.get("tool") for tc in e.get("tool_calls", [])],
            "needs_human_approval": e.get("needs_human_approval", False),
            "resolved": e.get("resolved", False),
            "usage": e.get("usage", {}),
        })
    return {"count": len(events), "events": events}


class ApproveRequest(BaseModel):
    kind: Literal["invoice", "rent", "discount"]
    ref_id: Optional[int] = None  # invoice id (kind=invoice) or lease id (kind=rent); unused for discount
    approved_by: str              # the human who approved it
    ticket_id: Optional[int] = None  # if given, the ticket is marked resolved once approved


@app.post("/approve")
async def approve(req: ApproveRequest):
    """Human approval step.

    For a payment (invoice/rent) this is the ONLY route that moves cash: it calls
    the guarded MCP pay tool, which still refuses without an approver or without
    enough cash. For a discount (a price_override ticket) no cash moves at all --
    the human simply grants the pricing decision and the ticket is resolved.
    """
    if not req.approved_by.strip():
        raise HTTPException(status_code=400, detail="approved_by is required (human approval)")

    if req.kind == "discount":
        # A discount is a judgment call, not a payment: resolve the ticket, keep
        # cash untouched (cash only ever goes OUT this term, never in).
        if req.ticket_id is None:
            raise HTTPException(status_code=400, detail="ticket_id is required to approve a discount")
        await mcp_call("update_ticket", {
            "ticket_id": req.ticket_id,
            "status": "resolved",
            "notes": f"[approved] bulk discount granted by {req.approved_by}",
        })
        cash = await mcp_call("get_cash_balance", {"account": "checking"})
        return {"ok": True, "kind": "discount", "amount": 0,
                "approved_by": req.approved_by, "new_balance": cash.get("balance", 0)}

    if req.ref_id is None:
        raise HTTPException(status_code=400, detail="ref_id is required for a payment")
    if req.kind == "invoice":
        result = await mcp_call("pay_invoice", {"invoice_id": req.ref_id,
                                                "approved_by": req.approved_by})
    else:  # rent
        result = await mcp_call("pay_rent", {"lease_id": req.ref_id,
                                             "approved_by": req.approved_by})

    if not result.get("ok"):
        # Tool refused (no approval / insufficient cash / bad ref) -> 400 with reason.
        raise HTTPException(status_code=400, detail=result.get("error", "payment refused"))

    # Payment went through -> the ticket is now resolved (moves to Done).
    if req.ticket_id is not None:
        await mcp_call("update_ticket", {
            "ticket_id": req.ticket_id,
            "status": "resolved",
            "notes": f"[approved] {req.kind} {req.ref_id} paid by {req.approved_by}",
        })
    return result


@app.get("/cash")
async def get_cash(account: str = "checking"):
    """Return the current cash balance from cash_accounts."""
    data = await mcp_call("get_cash_balance", {"account": account})
    if not data.get("found"):
        raise HTTPException(status_code=404, detail=f"account '{account}' not found")
    return {"account": data["name"], "balance": data["balance"], "as_of": data.get("date")}


@app.post("/reset")
async def reset():
    """Reset the working db to the original values and clear the event log.

    Lets us start a fresh ticket-resolution run. Serialized against MCP calls so
    we never copy the file mid-tool-call.
    """
    async with app.state.mcp_lock:
        shutil.copyfile(PRISTINE_DB, WORKING_DB)
        AUDIT_PATH.write_text("[]\n", encoding="utf-8")
    return {"ok": True, "message": "Working database reset to original values; event log cleared."}
