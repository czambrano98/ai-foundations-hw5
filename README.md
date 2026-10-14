# Campus Customs: Multi-Agent Operations

A small agentic team that runs a Yale apparel shop. Five PydanticAI agents (Boss,
Inventory, Accounting, Facilities, Customer Service) share one MCP tool server, a
FastAPI backend wires them to a React dashboard, and a human approves every payment
before any cash moves.

- **Agents' runtime model:** gpt-6-luna via Portkey (OpenAI-compatible gateway).
- **Three pieces:** an MCP server (`mcp_server/`), a FastAPI backend (`backend/`),
  and a React + Vite board (`frontend/`).
- **Safety:** agents never move money on their own, never go negative, never email a
  customer, and never place a real vendor order. Drafts stay on the board for a
  human.

The graded write-ups and run evidence live in `output/` (harness, design notes,
ticket plans with the Expected/Actual/Cash/Reflection tabs, the resolved board with
screenshots, the audit trail, and the resolved-tickets JSON).

---

## Prerequisites

- Python 3.11+ and Node.js 20+
- A Portkey API key with access to `gpt-6-luna`

---

## 1. Install

```bash
# from the project root
python -m venv .venv
# macOS / Linux:
source .venv/bin/activate
# Windows (PowerShell):
#   .venv\Scripts\Activate.ps1
pip install -r requirements.txt

# frontend deps
cd frontend
npm install
cd ..
```

## 2. Set your Portkey key

The backend reads `PORTKEY_API_KEY` from the environment (see `.env.example` for all
variable names). Set it in your shell before starting the backend:

```bash
# macOS / Linux:
export PORTKEY_API_KEY=your-portkey-api-key-here
# Windows (PowerShell):
#   $env:PORTKEY_API_KEY = "your-portkey-api-key-here"
```

## 3. Give yourself a clean database

The MCP server and backend read and write the **working** database
`data/campus_customs_new.db`. The **pristine** copy `data/campus_customs.db` is
never written to. When you want a clean run, copy the pristine DB over the working
copy:

```bash
# macOS / Linux:
cp data/campus_customs.db data/campus_customs_new.db
# Windows (PowerShell):
#   Copy-Item data\campus_customs.db data\campus_customs_new.db -Force
```

(Both files are included in this repo so you can run everything immediately.)

## 4. Start the MCP server

The MCP server exposes every shop fact and action as a tool over
`data/campus_customs_new.db`. **The backend starts it for you automatically** from
`.mcp.json` (a persistent stdio client opened in the FastAPI lifespan), so for
normal use you do not launch it by hand. To run it standalone for testing:

```bash
# macOS / Linux:
.venv/bin/python mcp_server/server.py
# Windows (PowerShell):
#   .venv\Scripts\python.exe mcp_server\server.py
```

## 5. Start the FastAPI backend

```bash
cd backend
# macOS / Linux:
../.venv/bin/python -m uvicorn main:app --port 8000
# Windows (PowerShell):
#   ..\.venv\Scripts\python.exe -m uvicorn main:app --port 8000
```

The API serves at `http://localhost:8000`. It spawns the MCP server on startup, so
make sure `PORTKEY_API_KEY` is set first.

## 6. Start the React board

In a second terminal:

```bash
cd frontend
npm run dev
```

Vite serves the dashboard at `http://localhost:5173` (or the next free port). Start
the backend first, or every tile shows a "can't reach the backend" error.

---

## Running the three tickets

1. **Reset the database before a full run.** This restores the pristine values and
   clears the event log so the run starts from $3,400.00 with all three tickets
   open. Click **Reset board** in the dashboard header, or:

   ```bash
   curl -X POST http://localhost:8000/reset
   ```

   (Reset copies the pristine DB over the working copy and empties
   `output/audit_trail.json`, which is the same clean slate as step 3 above.)

2. For each ticket, click it, press **Run the agent team**, and watch the agents
   work in the live feed.

3. When a ticket needs you, approve it: a payment (invoice or rent) moves cash
   through the guarded pay tool; a discount moves no cash. Nothing changes the shop
   until you approve.

After all three resolve, the ending checking balance is **$160.00** (start
$3,400.00, minus invoice #501 $840.00 and rent $2,400.00; the bulk discount moves no
cash), which matches `cash_accounts` in the working database.

---

## Project layout

| Path | What it is |
|---|---|
| `mcp_server/server.py` | The FastMCP server: all shop tools over the working DB. |
| `backend/` | FastAPI app, the five-agent team, settings, audit trail, prompts. |
| `frontend/` | React + Vite + TypeScript dashboard. |
| `data/` | `campus_customs.db` (pristine) and `campus_customs_new.db` (working). |
| `output/` | Write-ups and run evidence (harness, design, ticket plans, resolved board, audit trail). |
| `.mcp.json` | The single source of truth for the MCP server command. |
| `AI_prompts.md` | The prompts used to build this, one section per problem. |
