# Campus Customs — Agent Harness

Carine Zambrano · AI Foundations · Fall 2026

This file is the shared reference the agent team reads from. It grows as the
homework progresses. Problem 2 establishes the database: every table, its
fields, why it matters to the agents, and how the three open tickets link
together.

- **Source of truth:** `data/campus_customs.db` (pristine, never written to).
- **Working copy:** `data/campus_customs_new.db` (what the MCP server + backend
  read and update as tickets get resolved).
- **The shop clock:** `desk.date_today` is "today." Overdue is measured against
  it, never against the real wall clock.

---

## Shop state at a glance (as of `desk.date_today = 2026-08-31`)

| Fact | Value |
|---|---|
| Today | 2026-08-31 |
| Cash (checking) | $3,400.00 |
| Open tickets | 3 (IDs 101, 102, 103) |
| Open unpaid invoices | 1 (ID 501, $840, **overdue** since 2026-08-28) |
| Rent next due | 2026-09-02 ($2,400) |

---

## Tables

### `desk` — the shop clock
Fields: `date_today`, `notes`.
**Why it matters:** defines "today" for every agent; all overdue / due-soon
checks compare against `date_today`, not the real date.

### `cash_accounts` — the wallet
Fields: `name`, `balance`, `date`.
**Why it matters:** Accounting checks this before any payment. Cash only goes
out this term; the pay tool must refuse anything that would push `balance`
negative.

### `tickets` — the board
Fields: `id`, `type`, `requester`, `subject`, `sku`, `size`, `qty`,
`lease_id`, `invoice_id`, `status`, `notes`, `created_at`.
**Why it matters:** the work queue the Boss triages and routes. `type` tells
which agent owns it; the `sku`/`lease_id`/`invoice_id` columns are the links
into the rest of the database.

### `inventory` — stock on hand
Fields: `sku`, `name`, `size`, `qty`, `location`. (Primary key is `sku` + `size`.)
**Why it matters:** Inventory agent answers "can we fill this order?" A `qty`
shortfall triggers a vendor restock.

### `pricing` — cost & list price
Fields: `sku`, `unit_cost`, `list_price`.
**Why it matters:** lets Customer Service / Accounting compute margin and decide
how far a discount (e.g. a bulk request) can go without losing money.

### `vendors` — suppliers & lead times
Fields: `id`, `name`, `specialty`, `lead_days`.
**Why it matters:** Inventory picks a vendor by `specialty` and quotes delivery
from `lead_days`. A vendor will not ship new product while it still has an open
unpaid invoice.

### `invoices` — bills owed to vendors
Fields: `id`, `vendor_id`, `amount`, `due_date`, `status`, `description`.
**Why it matters:** an `open` invoice blocks that vendor from shipping and, if
`due_date` < today, is overdue. Paying it requires human approval and flips
`status` to paid.

### `leases` — rent obligations
Fields: `id`, `space_name`, `landlord`, `monthly_rent`, `next_due`, `notes`.
**Why it matters:** Facilities watches `next_due` against today to catch rent
coming due; payment goes through Accounting with human approval.

### `payments` — the payment ledger
Fields: `id`, `kind`, `ref_id`, `amount`, `account`, `paid_at`, `approved_by`.
**Why it matters:** the audit trail. Every processed payment writes a row here
(with `approved_by` recording the human approval) and decrements
`cash_accounts.balance`. Starts empty.

---

## The three open tickets and how they link

### Ticket 101 — `customer_order` (Tauhid Zaman, "Bulldog tee")
- Wants `CC-TEE-WHITE`, size **S**, qty **1**.
- → `inventory` (CC-TEE-WHITE / S): **qty 0 — out of stock.**
- → `pricing` (CC-TEE-WHITE): cost $8, list $28.
- → `invoice_id 501` → `invoices` 501: $840, `vendor_id 1`, due 2026-08-28
  (**overdue**), status **open**, "Rush reprint CC-TEE-WHITE S".
- → `vendors` 1 = Bulldog Print Co (apparel reprint, 5-day lead).
- **Chain:** size S is empty; a reprint is already on order but its invoice is
  unpaid, so Bulldog Print Co won't ship. Resolving this means paying invoice
  501 (human approval) so the 5-day reprint can proceed.

### Ticket 102 — `rent_notice` (Elm City Properties, "Rent due")
- → `lease_id 1` → `leases` 1: Chapel Street shop, Elm City Properties,
  $2,400/mo, next due **2026-09-02** (2 days out — matches the notice).
- **Chain:** Facilities flags rent due soon → Accounting pays $2,400 with human
  approval, writing a `payments` row and dropping cash from $3,400 to $1,000.

### Ticket 103 — `price_override` (Yale AI Club, "Bulk hoodie discount")
- Wants `CC-HOOD-NAVY`, size **M**, qty **20**.
- → `inventory` (CC-HOOD-NAVY / M): **qty 8 — short by 12.**
- → `pricing` (CC-HOOD-NAVY): cost $22, list $58.
- → restock vendor = Bulldog Print Co (apparel, 5-day lead) — **blocked again**
  by the open invoice 501.
- **Chain:** only 8 of 20 in stock; filling the rest needs a reprint that is
  blocked until invoice 501 is paid. The discount itself is a margin decision
  against cost $22 / list $58.

**Cross-cutting note:** invoice 501 ($840) sits on the critical path for both
ticket 101 and ticket 103, and rent ($2,400) is due inside the window. Paying
both would use $3,240 of the $3,400 cash, leaving $160 — so cash sequencing
matters.

---

## MCP tools (Problem 3)

All agents share one MCP server (`mcp_server/server.py`, FastMCP, named
`campus-customs`) that reads the working db `data/campus_customs_new.db`. Tools
only return data that exists in the db; a missing row reports `found: false`
instead of inventing values. The first three tools map one-to-one to the open
tickets.

### `get_inventory(sku, size?)` — reads `inventory` → unlocks **Ticket 101**
Ticket 101 asks for a `CC-TEE-WHITE` size S; this tool is the right one because
it returns that exact size's on-hand qty (0), which is the fact the order turns
on — we can't ship from stock, so the reprint path is required.

### `get_lease(lease_id)` — reads `leases` → unlocks **Ticket 102**
Ticket 102 is a rent notice pointing at `lease_id 1`; this tool is the right one
because it returns that lease's `monthly_rent` ($2,400) and `next_due`
(2026-09-02) — the exact amount and date Accounting needs before scheduling the
payment.

### `get_pricing(sku)` — reads `pricing` → unlocks **Ticket 103**
Ticket 103 asks for a bulk discount on `CC-HOOD-NAVY`; this tool is the right one
because it returns that SKU's `unit_cost` ($22) and `list_price` ($58), which
set the per-unit margin that bounds how deep the discount can go.

---

## The agent team (Problem 5)

Five PydanticAI agents, all running the same model — **`gpt-6-luna` via Portkey**
(Claude Code only writes the code; the agents' runtime brain is gpt-6-luna). They
share one tool layer (the MCP server, loaded from `.mcp.json`), and connectivity
is **full**: every agent has a `delegate` tool and can hand a sub-task to any
other agent. Prompts live in `backend/prompts/` (one file per agent).

| Agent | Owns | Tickets it drives | Delegates to |
|---|---|---|---|
| **Boss** | Triages the whole board and routes work | 101, 102, 103 | any agent |
| **Inventory** | Stock, shortfalls, vendors, restock POs | 101, 103 | Accounting (clear a blocking invoice); any |
| **Accounting** | Cash, invoices, and all payments (the only agent that moves money) | 101, 102, 103 | any |
| **Facilities** | Leases and rent due dates | 102 | Accounting (to pay rent); any |
| **Customer Service** | Customer orders, replies, discounts/margins | 101, 103 | Inventory (stock/ETA), Accounting/Boss (discount sign-off); any |

Each agent-loop stop (top-level or delegated) is appended to
`output/audit_trail.json` — see Safety below.

---

## Full MCP tool list (Problem 5)

All tools live on the one `campus-customs` MCP server over
`data/campus_customs_new.db`. R = read, W = write. Payment tools enforce human
approval and the no-negative-cash rule.

| Tool | Table(s) | R/W | What it does |
|---|---|---|---|
| `get_desk_date` | `desk` | R | The shop's "today" — the clock for all overdue checks. |
| `get_cash_balance` | `cash_accounts` | R | Cash on hand; checked before any payment. |
| `list_tickets` | `tickets` | R | The board (optionally filtered by status). |
| `get_ticket` | `tickets` | R | One ticket and its links. |
| `get_inventory` | `inventory` | R | On-hand stock by SKU/size (unlocks 101). |
| `get_pricing` | `pricing` | R | Unit cost / list price for margin (unlocks 103). |
| `get_lease` | `leases` | R | Rent amount and next-due date (unlocks 102). |
| `get_vendor` | `vendors` (+ `invoices`) | R | Vendor lead time **plus** `can_ship` — false while it has an open unpaid invoice. |
| `list_open_invoices` | `invoices` | R | Unpaid bills, each flagged `overdue` vs the shop clock. |
| `pay_invoice` | `invoices` + `payments` + `cash_accounts` | W | Pays a bill **only** with human approval and enough cash; marks it paid (unblocks the vendor) and lowers cash. |
| `pay_rent` | `leases` + `payments` + `cash_accounts` | W | Pays rent under the same guards; advances `next_due`. |
| `update_ticket` | `tickets` | W | Moves a ticket (e.g. to resolved) and appends an audit note. |
| `draft_customer_reply` | `tickets` | W | Writes a reply **draft** on the board — never emails. |
| `draft_vendor_order` | `tickets` | W | Writes a purchase-order **draft** on the board — never places a real order. |

---

## Safety & guardrails

Guardrails a real business would insist on before letting agents touch real
customers and real money, plus the limits that keep token use in check.

**Money controls**
- **Human approval on every payment.** `pay_invoice` / `pay_rent` refuse unless a
  human approver is named; the backend only supplies that approver after a person
  clicks approve in the dashboard. Agents cannot self-approve.
- **No negative cash.** A payment is refused if it would push the balance below
  zero — the shop never spends money it does not have.
- **Least authority.** Only Accounting moves money; the other agents must
  delegate payments to it, so money has a single, auditable choke point.

**No real-world side effects**
- We **never email customers** and **never place real vendor orders**. The
  `draft_*` tools only write a draft onto the ticket (the board) for a human to
  send — every draft returns `sent/placed: false`.
- **One tool layer.** All shop facts and actions go through the MCP server over
  the working db; there is no second tool path that bypasses it, and the pristine
  `campus_customs.db` is never written (we reset the working copy before a full
  run).

**Auditability**
- **Append-only audit trail.** Every agent-loop stop appends to
  `output/audit_trail.json`: run id, real timestamp, shop date, agent (and who
  delegated to it), the task, the tools it called, token usage, and whether the
  result is resolved or awaiting approval. We append, never wipe, so the full
  history survives across runs.

**Token / cost limits**
- A whole-run request budget (default 60) is shared across the Boss and every
  delegation via a run-level counter: each agent run is limited to the requests
  still remaining, so the team as a whole can't exceed the ceiling or loop away.
- Each agent run uses its own usage object, so the audit trail records each
  agent-loop's own token/request delta (not a shared cumulative).
- Full-connectivity delegation is bounded three ways: a per-run delegation cap
  (default 8), a max delegation depth (default 3), and a cycle guard (an agent
  already in the current delegation chain can't be delegated to again).
- Tool-call retries are bounded (default 2).
- The model is pinned to a single value (`gpt-6-luna`) for every agent.

---

## Backend API routes (Problem 7)

FastAPI app in `backend/main.py`. Start it from the `backend/` folder with
`uvicorn main:app --reload --port 8000`, which serves the dashboard at
`http://localhost:8000`. Every shop-state route goes through the one MCP server
(a persistent client), so there is no bypass layer.

| Method & URL | What it does |
|---|---|
| `GET /tickets` | List the tickets, each with an open/resolved flag, for the board. |
| `POST /tickets/{id}/run` | Run the agent team (Boss triages, then delegates) on one ticket. |
| `GET /events` | Recent agent events — what each agent said and which tools it used — so the board can refresh (from the audit trail). |
| `POST /approve` | Human approval step. For `kind` invoice/rent it is the ONLY route that moves cash (calls the guarded `pay_invoice` / `pay_rent`); for `kind` discount (a `price_override`) it just resolves the ticket and moves no cash. |
| `GET /cash` | Current checking balance from `cash_accounts`. |
| `POST /reset` | Reset the working db to the original values (and clear the event log) for a fresh run. |

---

## The dashboard (Problem 8)

A React + Vite + TypeScript single-page app in `frontend/`. Start it with `npm run
dev` (Vite, default port 5173). It calls the backend API at
`http://localhost:8000`, so the backend has to be running first or every tile shows
a "can't reach the backend" error. Full design rationale lives in
`output/design.md`.

- **Two-pane desk.** A ticket rail on the left, grouped **Open / Needs approval /
  Done**, with the cash tile on top. The selected ticket opens into a focused
  workspace on the right.
- **Live agent feed.** Running a ticket streams the team's steps in as they work.
  Each agent is a teddy bear tinted to its own color (Boss purple, Inventory teal,
  Accounting blue, Facilities magenta, Customer Service indigo), shows who delegated
  to it, and lists the tools it used as one line of chips.
- **One color per meaning.** Open = gold, Needs approval = red, Resolved/Paid =
  green, error = off-brand vermilion; the base is Yale navy.
- **Human in the loop.** When a run needs a person, a red pop-up toast appears and a
  red approval panel asks for sign-off. A payment (invoice/rent) actually moves
  cash; a discount (`price_override`) moves none. Nothing changes the shop until the
  human approves.
- **Cash tile** shows the checking balance and gives a brief neutral flash when an
  approved payment goes through.
- **Branding** matches the Homework 4 storefront: navy "CC" monogram, Fraunces +
  Inter, no gold in the brand mark.

---

## Full run results (Problem 9)

Reset the working db, then ran all three tickets to resolution through the
dashboard, approving each payment as the human.

- **Starting checking balance:** $3,400.00 · **Ending:** $160.00 (matches
  `cash_accounts` in the working db).
- **Cash out:** invoice #501 $840.00 (ticket 101) + rent $2,400.00 (ticket 102) =
  $3,240.00. Ticket 103's bulk discount moved no cash.
- Both payments were **approved by a human** (Carine, owner); cash never went
  negative; the `payments` ledger holds exactly those two rows.
- **Where the evidence lives:** per-ticket actuals (agents, delegations, tools) in
  `output/desk_tickets.html`; a machine-readable summary in
  `output/resolved_tickets.json`; board screenshots in
  `output/resolved_board.html`; and the append-only agent-loop audit in
  `output/audit_trail.json`.
