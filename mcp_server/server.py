"""Campus Customs MCP server.

A FastMCP server that exposes every shop tool the agent team (Boss, Inventory,
Accounting, Facilities, Customer Service) is allowed to use. All shop facts and
all shop actions go through this one server over the working database, so there
is no second tool layer that bypasses it. Core rules enforced here:

* `desk.date_today` is "today" for the shop -- overdue is measured against it.
* A vendor will not ship new product while it has an open unpaid invoice.
* Every payment requires human approval (an `approved_by` value) and is refused
  if the shop lacks the cash -- the cash balance may never go negative.
* We never email customers or place real vendor orders: the draft_* tools only
  write a draft onto the ticket (the board); they never contact anyone.

Tools never invent data: a missing row returns `found: false` / an error, never
a made-up value.
"""

from __future__ import annotations

import sqlite3
from datetime import date
from pathlib import Path
from typing import Optional

from fastmcp import FastMCP

# The server always talks to the WORKING COPY, never the pristine database.
DB_PATH = Path(__file__).resolve().parent.parent / "data" / "campus_customs_new.db"

mcp = FastMCP("campus-customs")

CHECKING = "checking"  # the shop's single cash account


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _shop_today() -> str:
    """Return desk.date_today -- the shop clock, not the real wall clock."""
    conn = _connect()
    try:
        row = conn.execute("SELECT date_today FROM desk LIMIT 1").fetchone()
        return row["date_today"] if row else date.today().isoformat()
    finally:
        conn.close()


def _add_one_month(iso_date: str) -> str:
    """Advance an ISO date by one calendar month (clamped to month length)."""
    y, m, d = (int(p) for p in iso_date.split("-"))
    m += 1
    if m > 12:
        m = 1
        y += 1
    # clamp day (e.g. Jan 31 -> Feb 28); simple month-length table, no leap edge needed here
    days_in_month = [31, 29 if y % 4 == 0 and (y % 100 != 0 or y % 400 == 0) else 28,
                     31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    d = min(d, days_in_month[m - 1])
    return f"{y:04d}-{m:02d}-{d:02d}"


# --------------------------------------------------------------------------- #
# READ TOOLS                                                                   #
# --------------------------------------------------------------------------- #

@mcp.tool
def get_desk_date() -> dict:
    """Return the shop's 'today' (`desk.date_today`).

    Every overdue / due-soon decision must compare against this date, not the
    real calendar. Reads the `desk` table.
    """
    conn = _connect()
    try:
        row = conn.execute("SELECT date_today, notes FROM desk LIMIT 1").fetchone()
    finally:
        conn.close()
    if row is None:
        return {"found": False, "date_today": None}
    return {"found": True, **dict(row)}


@mcp.tool
def get_cash_balance(account: str = CHECKING) -> dict:
    """Return the current cash balance for an account from `cash_accounts`.

    Accounting must check this before any payment; the shop never spends into a
    negative balance.
    """
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT name, balance, date FROM cash_accounts WHERE name = ?", (account,)
        ).fetchone()
    finally:
        conn.close()
    if row is None:
        return {"found": False, "account": account, "balance": None}
    return {"found": True, **dict(row)}


@mcp.tool
def list_tickets(status: Optional[str] = None) -> dict:
    """List tickets on the board from the `tickets` table.

    Pass `status` (e.g. "open") to filter, or omit it for all tickets. This is
    the work queue the Boss triages and routes to the other agents.
    """
    conn = _connect()
    try:
        if status is not None:
            rows = conn.execute(
                "SELECT * FROM tickets WHERE status = ? ORDER BY id", (status,)
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM tickets ORDER BY id").fetchall()
    finally:
        conn.close()
    return {"count": len(rows), "tickets": [dict(r) for r in rows]}


@mcp.tool
def get_ticket(ticket_id: int) -> dict:
    """Return a single ticket (and its links) by id from the `tickets` table."""
    conn = _connect()
    try:
        row = conn.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
    finally:
        conn.close()
    if row is None:
        return {"found": False, "ticket": None}
    return {"found": True, "ticket": dict(row)}


@mcp.tool
def get_inventory(sku: str, size: Optional[str] = None) -> dict:
    """Look up on-hand stock for a SKU from the `inventory` table.

    Pass a `size` for one size, or omit it for every size of that SKU. Use this
    to answer "can we fill this order from stock?". Returns `found: false` when
    nothing matches -- no stock is invented.
    """
    conn = _connect()
    try:
        if size is not None:
            rows = conn.execute(
                "SELECT sku, name, size, qty, location FROM inventory "
                "WHERE sku = ? AND size = ?", (sku, size),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT sku, name, size, qty, location FROM inventory "
                "WHERE sku = ? ORDER BY size", (sku,),
            ).fetchall()
    finally:
        conn.close()
    items = [dict(r) for r in rows]
    return {"found": bool(items), "items": items}


@mcp.tool
def get_pricing(sku: str) -> dict:
    """Return unit cost and list price for a SKU from the `pricing` table.

    Margin per unit is list_price - unit_cost, which bounds how far a discount
    can go before the shop loses money. Returns `found: false` if unpriced.
    """
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT sku, unit_cost, list_price FROM pricing WHERE sku = ?", (sku,)
        ).fetchone()
    finally:
        conn.close()
    if row is None:
        return {"found": False, "pricing": None}
    return {"found": True, "pricing": dict(row)}


@mcp.tool
def get_lease(lease_id: int) -> dict:
    """Return a lease (rent obligation) by id from the `leases` table.

    Gives monthly_rent and next_due so a rent notice can be acted on. Returns
    `found: false` if the lease id does not exist -- no amount/date is invented.
    """
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT id, space_name, landlord, monthly_rent, next_due, notes "
            "FROM leases WHERE id = ?", (lease_id,),
        ).fetchone()
    finally:
        conn.close()
    if row is None:
        return {"found": False, "lease": None}
    return {"found": True, "lease": dict(row)}


@mcp.tool
def get_vendor(vendor_id: int) -> dict:
    """Return a vendor plus whether it can ship right now, from `vendors`.

    Reads `vendors` for name/specialty/lead_days and checks `invoices` for any
    open invoice owed to this vendor. Because a vendor will not ship new product
    while it has an open unpaid invoice, the response includes
    `has_open_invoice` and `can_ship` so Inventory knows if a restock is
    currently possible.
    """
    conn = _connect()
    try:
        v = conn.execute(
            "SELECT id, name, specialty, lead_days FROM vendors WHERE id = ?", (vendor_id,)
        ).fetchone()
        if v is None:
            return {"found": False, "vendor": None}
        open_inv = conn.execute(
            "SELECT id, amount, due_date FROM invoices "
            "WHERE vendor_id = ? AND status = 'open' ORDER BY id", (vendor_id,)
        ).fetchall()
    finally:
        conn.close()
    has_open = len(open_inv) > 0
    return {
        "found": True,
        "vendor": dict(v),
        "has_open_invoice": has_open,
        "can_ship": not has_open,
        "open_invoices": [dict(r) for r in open_inv],
    }


@mcp.tool
def list_open_invoices(vendor_id: Optional[int] = None) -> dict:
    """List open (unpaid) invoices from the `invoices` table.

    Pass `vendor_id` to scope to one vendor. An invoice with due_date before the
    shop's today is overdue and blocks that vendor from shipping.
    """
    today = _shop_today()
    conn = _connect()
    try:
        if vendor_id is not None:
            rows = conn.execute(
                "SELECT * FROM invoices WHERE status = 'open' AND vendor_id = ? ORDER BY id",
                (vendor_id,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM invoices WHERE status = 'open' ORDER BY id"
            ).fetchall()
    finally:
        conn.close()
    invoices = []
    for r in rows:
        d = dict(r)
        d["overdue"] = d["due_date"] < today
        invoices.append(d)
    return {"shop_today": today, "count": len(invoices), "invoices": invoices}


# --------------------------------------------------------------------------- #
# ACTION TOOLS (writes) -- payments require approval + sufficient cash         #
# --------------------------------------------------------------------------- #

def _require_approval(approved_by: Optional[str]) -> Optional[str]:
    if not approved_by or not approved_by.strip():
        return "refused: human approval required (no approved_by supplied)"
    return None


@mcp.tool
def pay_invoice(invoice_id: int, approved_by: str) -> dict:
    """Pay an open vendor invoice. REQUIRES human approval.

    Refuses unless `approved_by` names the human who approved it, and refuses if
    the shop lacks the cash (no negative balances). On success it writes a
    `payments` row, flips the invoice `status` to 'paid' (which unblocks that
    vendor's shipping), and decrements `cash_accounts`.
    """
    err = _require_approval(approved_by)
    if err:
        return {"ok": False, "error": err}

    conn = _connect()
    try:
        inv = conn.execute(
            "SELECT id, vendor_id, amount, status FROM invoices WHERE id = ?", (invoice_id,)
        ).fetchone()
        if inv is None:
            return {"ok": False, "error": f"refused: invoice {invoice_id} not found"}
        if inv["status"] != "open":
            return {"ok": False, "error": f"refused: invoice {invoice_id} is already {inv['status']}"}

        amount = inv["amount"]
        cash = conn.execute(
            "SELECT balance FROM cash_accounts WHERE name = ?", (CHECKING,)
        ).fetchone()
        balance = cash["balance"] if cash else 0.0
        if amount > balance:
            return {
                "ok": False,
                "error": f"refused: insufficient cash (need {amount}, have {balance})",
            }

        paid_at = _shop_today()
        with conn:  # atomic
            conn.execute(
                "INSERT INTO payments (kind, ref_id, amount, account, paid_at, approved_by) "
                "VALUES ('invoice', ?, ?, ?, ?, ?)",
                (invoice_id, amount, CHECKING, paid_at, approved_by),
            )
            conn.execute("UPDATE invoices SET status = 'paid' WHERE id = ?", (invoice_id,))
            conn.execute(
                "UPDATE cash_accounts SET balance = balance - ?, date = ? WHERE name = ?",
                (amount, paid_at, CHECKING),
            )
        new_balance = balance - amount
    finally:
        conn.close()
    return {
        "ok": True,
        "kind": "invoice",
        "invoice_id": invoice_id,
        "amount": amount,
        "approved_by": approved_by,
        "paid_at": paid_at,
        "new_balance": new_balance,
        "note": "invoice marked paid; vendor can now ship",
    }


@mcp.tool
def pay_rent(lease_id: int, approved_by: str) -> dict:
    """Pay the monthly rent on a lease. REQUIRES human approval.

    Refuses without `approved_by` and refuses if cash is insufficient. On
    success it writes a `payments` row, decrements `cash_accounts`, and advances
    the lease `next_due` by one month.
    """
    err = _require_approval(approved_by)
    if err:
        return {"ok": False, "error": err}

    conn = _connect()
    try:
        lease = conn.execute(
            "SELECT id, monthly_rent, next_due FROM leases WHERE id = ?", (lease_id,)
        ).fetchone()
        if lease is None:
            return {"ok": False, "error": f"refused: lease {lease_id} not found"}

        amount = lease["monthly_rent"]
        cash = conn.execute(
            "SELECT balance FROM cash_accounts WHERE name = ?", (CHECKING,)
        ).fetchone()
        balance = cash["balance"] if cash else 0.0
        if amount > balance:
            return {
                "ok": False,
                "error": f"refused: insufficient cash (need {amount}, have {balance})",
            }

        paid_at = _shop_today()
        new_due = _add_one_month(lease["next_due"])
        with conn:
            conn.execute(
                "INSERT INTO payments (kind, ref_id, amount, account, paid_at, approved_by) "
                "VALUES ('rent', ?, ?, ?, ?, ?)",
                (lease_id, amount, CHECKING, paid_at, approved_by),
            )
            conn.execute("UPDATE leases SET next_due = ? WHERE id = ?", (new_due, lease_id))
            conn.execute(
                "UPDATE cash_accounts SET balance = balance - ?, date = ? WHERE name = ?",
                (amount, paid_at, CHECKING),
            )
        new_balance = balance - amount
    finally:
        conn.close()
    return {
        "ok": True,
        "kind": "rent",
        "lease_id": lease_id,
        "amount": amount,
        "approved_by": approved_by,
        "paid_at": paid_at,
        "next_due": new_due,
        "new_balance": new_balance,
    }


@mcp.tool
def update_ticket(ticket_id: int, status: Optional[str] = None,
                  notes: Optional[str] = None, append_notes: bool = True) -> dict:
    """Update a ticket's status and/or notes in the `tickets` table.

    Use this to move a ticket (e.g. to 'resolved') and leave an audit note. By
    default `notes` is appended to the existing notes (append_notes=True); pass
    append_notes=False to replace them.
    """
    conn = _connect()
    try:
        row = conn.execute("SELECT id, notes FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
        if row is None:
            return {"ok": False, "error": f"ticket {ticket_id} not found"}

        new_notes = row["notes"]
        if notes is not None:
            new_notes = f"{row['notes']}\n{notes}".strip() if (append_notes and row["notes"]) else notes

        with conn:
            if status is not None:
                conn.execute("UPDATE tickets SET status = ? WHERE id = ?", (status, ticket_id))
            if notes is not None:
                conn.execute("UPDATE tickets SET notes = ? WHERE id = ?", (new_notes, ticket_id))
        updated = conn.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
    finally:
        conn.close()
    return {"ok": True, "ticket": dict(updated)}


@mcp.tool
def draft_customer_reply(ticket_id: int, message: str) -> dict:
    """Draft a reply to a customer -- WITHOUT sending it.

    We never email customers. This records the draft onto the ticket (the board)
    with a [DRAFT REPLY] tag so a human can review it, and returns the draft
    text. Nothing is sent anywhere.
    """
    conn = _connect()
    try:
        row = conn.execute("SELECT id, notes FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
        if row is None:
            return {"ok": False, "error": f"ticket {ticket_id} not found"}
        tag = f"[DRAFT REPLY] {message}"
        new_notes = f"{row['notes']}\n{tag}".strip() if row["notes"] else tag
        with conn:
            conn.execute("UPDATE tickets SET notes = ? WHERE id = ?", (new_notes, ticket_id))
    finally:
        conn.close()
    return {"ok": True, "ticket_id": ticket_id, "draft_reply": message, "sent": False}


@mcp.tool
def draft_vendor_order(ticket_id: int, vendor_id: int, sku: str, size: str,
                       qty: int, note: str = "") -> dict:
    """Draft a purchase order to a vendor -- WITHOUT placing it.

    We never place real vendor orders. This records the draft PO onto the ticket
    (the board) with a [DRAFT PO] tag and returns it. It also reports whether the
    vendor can currently ship (a vendor with an open unpaid invoice cannot), so
    the human sees the blocker. Nothing is ordered.
    """
    conn = _connect()
    try:
        v = conn.execute("SELECT id, name FROM vendors WHERE id = ?", (vendor_id,)).fetchone()
        if v is None:
            return {"ok": False, "error": f"vendor {vendor_id} not found"}
        row = conn.execute("SELECT id, notes FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
        if row is None:
            return {"ok": False, "error": f"ticket {ticket_id} not found"}
        blocking = conn.execute(
            "SELECT id FROM invoices WHERE vendor_id = ? AND status = 'open'", (vendor_id,)
        ).fetchall()
        can_ship = len(blocking) == 0
        tag = (f"[DRAFT PO] vendor={v['name']} sku={sku} size={size} qty={qty} "
               f"can_ship={can_ship}" + (f" note={note}" if note else ""))
        new_notes = f"{row['notes']}\n{tag}".strip() if row["notes"] else tag
        with conn:
            conn.execute("UPDATE tickets SET notes = ? WHERE id = ?", (new_notes, ticket_id))
    finally:
        conn.close()
    return {
        "ok": True,
        "ticket_id": ticket_id,
        "vendor_id": vendor_id,
        "sku": sku,
        "size": size,
        "qty": qty,
        "can_ship": can_ship,
        "blocking_invoice_ids": [r["id"] for r in blocking],
        "placed": False,
    }


if __name__ == "__main__":
    mcp.run()
