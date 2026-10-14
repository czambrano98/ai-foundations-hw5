# Campus Customs MCP Server

The MCP server is the single tool layer for the Campus Customs agent team. Every
agent (Boss, Inventory, Accounting, Facilities, Customer Service) calls the same
tools here instead of touching the database directly, so all shop state comes
from one place and no agent can invent data.

## Database

- Reads and (in later problems) writes **`data/campus_customs_new.db`** — the
  working copy.
- The pristine `data/campus_customs.db` is never touched, so we can reset the
  working copy before a full ticket-resolution run.

## Tools

All agents share these tools; no agent reads or writes the database directly. R =
read, W = write. Read tools report `found: false` for a missing row instead of
inventing values.

| Tool | Table(s) | R/W | Purpose |
|---|---|---|---|
| `get_desk_date()` | `desk` | R | The shop's "today" — the clock for every overdue check. |
| `get_cash_balance(account="checking")` | `cash_accounts` | R | Cash on hand; checked before any payment. |
| `list_tickets(status?)` | `tickets` | R | The board, optionally filtered by status. |
| `get_ticket(ticket_id)` | `tickets` | R | One ticket and its links. |
| `get_inventory(sku, size?)` | `inventory` | R | On-hand stock to see if an order can ship (ticket 101). |
| `get_pricing(sku)` | `pricing` | R | Unit cost / list price to size a discount (ticket 103). |
| `get_lease(lease_id)` | `leases` | R | Rent amount and next-due date (ticket 102). |
| `get_vendor(vendor_id)` | `vendors` (+ `invoices`) | R | Lead time **and** `can_ship` — false while the vendor has an open unpaid invoice. |
| `list_open_invoices(vendor_id?)` | `invoices` | R | Unpaid bills, each flagged `overdue` vs the shop clock. |
| `pay_invoice(invoice_id, approved_by)` | `invoices` + `payments` + `cash_accounts` | W | Pay a bill — **requires human approval**, refuses on insufficient cash; marks it paid and lowers cash. |
| `pay_rent(lease_id, approved_by)` | `leases` + `payments` + `cash_accounts` | W | Pay rent under the same guards; advances `next_due`. |
| `update_ticket(ticket_id, status?, notes?)` | `tickets` | W | Move a ticket and leave an audit note. |
| `draft_customer_reply(ticket_id, message)` | `tickets` | W | Write a reply **draft** on the board — never emails. |
| `draft_vendor_order(ticket_id, vendor_id, sku, size, qty)` | `tickets` | W | Write a PO **draft** on the board — never places a real order. |

### Rules enforced in the tools
- `desk.date_today` is "today"; overdue is measured against it, not the real date.
- A vendor will not ship while it has an open unpaid invoice (`get_vendor.can_ship`).
- Every payment requires `approved_by` (human approval) and is refused if cash is
  insufficient — the balance never goes negative.
- The `draft_*` tools never contact anyone; drafts stay on the board.

## Running

```bash
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
.venv/Scripts/python.exe mcp_server/server.py
```

The server is named `campus-customs` and is built with
[FastMCP](https://github.com/jlowin/fastmcp). The agent backend reaches it
through `.mcp.json`, so you normally don't run it by hand — the agents launch it.
