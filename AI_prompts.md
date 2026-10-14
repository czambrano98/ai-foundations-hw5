# Homework 5 — AI Prompt Log

Carine Zambrano · AI Foundations · Fall 2026

A record of the prompts I gave Claude Code while working through Homework 5. Each
section covers one problem and lists my initial prompt, the follow-up prompt I
needed (if any), and one sentence on what the first answer was missing.

---

## Problem 1 — Vibe Coder Prompts

**Initial prompt**

> incredible, thank you! this is Problem 1: Vibe coder prompts.
> we'll create AI_prompts.md and we'll keep it updated as we move forward. this
> file is the log of what I type into the chat. as previous HWs, we need to put
> one section for each problem, and each section must have the problem number and
> title, what I typed (do not edit my words. if anything, just make sure that
> there are no typos or outlandish grammar mistakes pls), and the follow-up
> prompt if I need it (and one sentence on what was lacking after the first
> prompt)

**Follow-up prompt**

None needed — the prompt specified the file name, the one-section-per-problem
structure, and every required field, so the log could be created in one pass.

**What was lacking after the first prompt**

Nothing was missing; the instructions were complete and self-contained.

---

## Problem 2 — Study the Campus Customs Database

**Context provided at the start of the session** (logged here for situating,
per my request in Problem 2)

> hello! today we'll be working on the homework 5 folder.
> we'll create a Campus Customs Multi-Agent Operations, which is an agentic team
> that runs the shop. open tickets will land on a board (customer orders, rent,
> unpaid bills, discount reqs, etc). we will build three pieces that talk to each
> other: an MCP server, a FastAPI backend with the multi-agent team, and a React
> dashboard so a human can watch the agents at work and approve requests.
> this agent team will have full connectivity, and any agent can delegate tasks
> to any other agent for help. throughout the assignment, we will build a bunch
> of agents: Boss, Inventory, Accounting, Facilities, and Customer Service.
> before we start, let's unzip the data.zip file which is under the Homework 5
> folder. our tools will update the database as tickets get resolved, but we need
> to make a copy of data/campus_customs_new.db and point our MCP server and
> backend at that working copy. we'll keep campus_customs.db untouched so we can
> reset when we want to restart resolving tickets.
> in terms of rules of the shop, the field desk.date_today is "today" for the
> shop. we'll use this date to determine what's overdue. vendor lead times will
> come from the vendors table. a vendor will not ship new product when they still
> have an open unpaid invoice. human approval is required for all payments. points
> will be deducted if that's not done. when payment is processed, we will need to
> update the relevant table. if we don't have enough cash, the pay tool must
> refuse (we do not have neg cash balances). in this hw, cash only goes out, so
> there will be no money coming in. before we do a full run to resolve the
> tickets, we need to make sure to reset the database to the OG values.
> importantly, we will never email customers or call real vendors. the drafts
> will stay on the board.
> we'll work my portkey_api_key for AI calls, and we need to use only gpt-6-luna
> for every agent, and we'll work one problem at a time with the vibe coder. the
> final submission will be a public GitHub repository.
> besides the file, we do not need to make any action final now. i'll prompt you
> as we go.

**Initial prompt**

> thank you! this is Problem 2: Study the Campus Customs database.
> we'll open data/campus_customs.db and look through every table and its fields.
> we'll copy the OG file to data/campus_customs_new.db, and the later problems
> update that working copy.
> I realize that we already did this, so just note in the AI prompts the context
> chat that I provided right at the beginning just so you're situated.
> we'll then study the three open tickets and see how they link to other tables.
> we'll also start output/harness.md. for each table, we list the fields and
> describe one short line on why that table matters for the agents. we'll keep
> growing this harness file as we progress through the hw.

**Follow-up prompt**

None needed — the copy was already made during setup, and the prompt fully
specified the database study and the harness file structure.

**What was lacking after the first prompt**

Nothing was missing; the only note is that the DB copy had already been done in
the setup step, so that part was a no-op this time.

---

## Problem 3 — Build the MCP Server

**Initial prompt**

> yay, ty! this is Problem 3: Build the MCP server.
> we'll write an MCP server in mcp_server/ using FastMCP. this will talk to
> data/campus_customs_new.db, but we do not need to connect or run it in this
> problem.
> every agent in this hw uses the tools in this MCP server. we'll add more tools
> later on, but for now, we will write three tools that we know we will need for
> the tickets in the database. let's keep the names clear, never invent any data,
> and only use info in the database.
> in output/harness.md, we'll list each of the three MCP tools. for every tool,
> let's include which table it reads, which ticket it helps unlock (101, 102, or
> 103), and one sentence on why that tool is the right one for that ticket. vague
> lines like "reads inventory" will dock points, so let's tie the tool to the
> ticket.
> finally, let's add a short mcp_server/README.md file that explains what the MCP
> server is for, which database file it uses and the three tools it has.
> also, going forward I'll refer to database as db so I type faster.

**Follow-up prompt**

None needed — the prompt specified the three tools, the no-invented-data rule,
the harness mapping (table + ticket + why), and the README contents.

**What was lacking after the first prompt**

Nothing was missing; the three-tools-to-three-tickets mapping made the tool
design unambiguous.

---

## Problem 4 — Add the MCP Server to the Vibe Coder and Test Each Tool

**Initial prompt**

> incredddd! now, we're on Problem 4: Add the MCP server to vibe coder and test
> each tool.
> kinda self-explanatory, but now we'll add this MCP server to this project so you
> can call the tools. we'll save the connection JSON text in .mcp.json at the
> project root (or however you save the local MCP server lists). once that
> connection is good to go, we'll test each of our three MCP tools. we'll save the
> evidence in output/mcp_smoke.json. for every tool, we need to include: 1. the
> prompt I asked on the chat; 2. the tool name; 3. the tool output, which must
> match values in data/campus_customs_new.db.

**Follow-up prompt**

> First, how can we fix that Python had a broken partial FastMCP install, or is
> the fix we implemented enough? And, can we try to do a live MCP?

This prompted two things: (1) explaining the broken install — it was one bad
virtual environment (Homework 2_V1's venv, missing the `uncalled_for`
dependency), and the self-contained Homework 5 `.venv` we built is the correct,
sufficient fix; the broken venv is best left untouched since it belongs to a
different homework. (2) A live MCP test: I pointed `.mcp.json` at the HW5 venv
Python and launched `server.py` as a real separate stdio subprocess (not the
in-memory client), which advertised all three tools and returned db-matching
values, including `found: false` for a bogus SKU.

**What was lacking after the first prompt**

Nothing in the instructions; the gaps were environmental (a broken Python/FastMCP
install, fixed with a clean venv) and a demonstration gap (the Problem 4 test
used the in-memory client, so the follow-up added a true live stdio run).

---

## Problem 5 — Build the Agent Team and Grow the MCP Tools

**Initial prompt**

> let's do Problem 5: Build the agent team and grow the MCP tools.
> also self-explanatory. we'll build the agentic team for Campus Customs using
> PydanticAI: Boss, Inventory, Accounting, Facilities, and Customer Service.
> we'll include prompts, models, and agent loops so they can delegate work to
> each other with full connectivity.
> either way, we'll put the agent prompts in backend/prompts/, which should be
> one file per agent. we'll then put data types in backend/models.py, and the
> agent files will go under backend/ (our layout can vary as long as the five
> roles are clear). we'll use the portkey_api_key and only gpt-6-luna for every
> agent.
> I realized one thing. since we're working on VS Code on Claude and my
> instructor is asking that we only use gpt-6-luna, can we instead [use] that, or
> do we need to use the Claude-equivalent for that model?
> we'll write each prompt in our/my own words with the shop rules that the agent
> needs. since more detailed prompts that cover all aspects of the agent's work
> and scope will score higher, pls lmk if I should tweak the description if mine
> is too generic or short.
> we'll then add any tools the agents need to our MCP server so they can work on
> the open tickets. shop facts come from the MCP server over
> data/campus_customs_new.db. we must not invent a second shop-tools layer that
> bypasses the MCP.
> we'll write the agents so they append to output/audit_trail.json as they run:
> for each agent-loop stop, we must record enough to audit later. we'll append to
> this file, instead of wiping it each run.
> in output/harness.md, we'll list each agent and each MCP tool (including ones
> that we'll add in this problem) along with which table the tool uses. we'll also
> add a short safety section, including the guardrails a real business would want
> when agents touch real customers and real money, plus limits that keep token
> use in check.
> if anything is needed from me for those, pls lmk. we'll then update
> mcp_server/README.md so the tool list matches what we have now.

**Answer to the embedded model question**

Use `gpt-6-luna` for every agent — no Claude-equivalent. Claude Code is only the
*author* (build time); the agents' runtime brain is `gpt-6-luna` reached through
Portkey's OpenAI-compatible endpoint. The two never collide, so the instructor's
"only gpt-6-luna" rule is satisfied by the agent config regardless of coding with
Claude.

**Follow-up prompts**

> I'll personalize the prompts. once we're done with that, let's do a trial live
> run. I don't think we need a virtual key besides the portkey api key on the env
> and/or the provider slug

> OK, prompts are personalized and good to go!

The user rewrote the five prompts in their own voice, then asked for a trial live
run. The run reached `gpt-6-luna` through Portkey on the first try (key alone, no
virtual key), which surfaced three issues that were fixed in order:
1. **Reasoning model + function tools.** gpt-6-luna rejected Chat Completions
   with tools; switched the agents to the Responses API (`OpenAIResponsesModel`).
2. **Slow MCP cold-start.** The FastMCP server takes ~9s to start on Windows and
   the toolset's default init timeout was shorter; built the toolset manually
   from `.mcp.json` with a 60s `init_timeout` and `keep_alive=True`.
3. **Delegation loop.** Full connectivity let agents delegate in a cycle until
   the request budget raised `UsageLimitExceeded` and crashed; added a cycle
   guard (no delegating to an agent already in the chain), a per-run delegation
   cap, and graceful handling that returns a partial result instead of crashing.

After the fixes the trial run completed cleanly (exit 0): the Boss triaged all 3
tickets, delegated across the team, drafted customer replies (not sent), and left
every payment awaiting human approval — cash unchanged at $3,400, no payments,
invoice 501 still open. 9 audit entries were appended.

> let's do one more quick run to populate token usage

> Let's do so that each audit entry show that agent's own token delta

Two more follow-ups on the audit trail. First, `usage` turned out to be a
property (not a method), so token usage logged empty — fixed. Then, because all
agents shared one usage object, the logged usage was the cumulative total; and
because pydantic-ai runs an agent's tool calls (including delegations)
concurrently, bracketing that shared counter double-counted and produced a
negative Boss delta. Final fix: give each agent run its own usage object so
`result.usage` is that agent-loop's own delta, and enforce the global request
ceiling separately via a shared per-run counter (each run limited to the budget
still remaining). The per-agent deltas now sum exactly to the run total
(35 requests / 100,895 tokens).

**What was lacking after the first prompt**

The prompt itself was thorough; the gaps were runtime, not instructions — a
reasoning-model API detail, a Windows cold-start timeout, and a full-connectivity
delegation loop, all resolved so the live run succeeds end to end.

---

## Problem 6 — Plan the Three Tickets

**Initial prompt**

> awesome! Problem 6: Plan the three tickets.
> before we wire the backend, we need to write down what we expect the team to do
> on each open ticket. we'll build output/desk_tickets.html, which is a page that
> one can double-click with one tab per ticket (101, 102, and 103). we'll also add
> empty cash and reflection tabs for later problems (we'll leave them blank or with
> a short "coming later" note for now).
> on each ticket tab, we'll fill an Expected section only, leaving room for an
> Actual section that we'll fill after we run the agents. for each ticket's
> Expected section, I'll write in my own words: 1. who should the Boss call first,
> and why; 2. All the agent delegations expected (not "Boss calls everyone");
> 3. Which MCP tools we expected that run to use.
> note that plans that send every specialist on every ticket score low, and this
> will be compared to what actually happens when our agents resolve the three
> tickets.

**Follow-up prompt**

> Ticket 101: Tauhid wants 1 size-S CC-TEE-WHITE, but it's out of stock. A reprint
> is already on order, but invoice 501 ($840) is overdue and unpaid, which blocks
> the vendor from shipping.
>
> Who should Boss call first, and why?
> The issue isn't inventory availability. It's payment instead. The reprint can't
> proceed until the blocking invoice is paid. So Accounting needs to come first to
> clear that invoice, then Inventory can confirm the order proceeds.
> All agent delegations expected:
> Boss → Accounting (pay invoice 501), then Accounting → Inventory (confirm reprint
> will ship once paid)
> Which MCP tools: get_inventory (check size-S stock = 0), list_open_invoices
> (find 501), pay_invoice (clear it with approval)
>
> Ticket 102 — Rent Due: $2,400 rent due in 2 days (2026-09-02).
>
> Who should Boss call first? Facilities (owns lease dates) → then Accounting
> (moves the money)
> Delegations: Boss → Facilities (flag rent due), Facilities → Accounting (pay it)
> Tools: get_lease (confirm amount/date), pay_rent (with approval)
>
> Ticket 103: Yale AI Club wants 20 size-M CC-HOOD-NAVY hoodies. Only 8 in stock,
> which is the same reprint problem as ticket 101 (blocked by invoice 501). Also a
> margin/discount question.
>
> Who should Boss call first? Accounting or Customer Service (to handle the
> discount margin)?
> Delegations: Customer Service first, then Accounting
> Tools: get_inventory, get_pricing (for margin math), then same invoice/restock
> chain as 101

I inserted these three Expected plans into `output/desk_tickets.html` (light
typo/grammar cleanup only), and answered the ticket-103 question: Customer
Service first, because the ticket's primary ask is a discount decision (Customer
Service's domain), with Accounting/Inventory as secondary dependencies in the
same invoice/restock chain as ticket 101.

**What was lacking after the first prompt**

Nothing — the first pass built the page scaffold as specified; the only thing it
couldn't contain was the user's own plan wording, which the user then supplied
and which was dropped in.

---

## Problem 7 — Backend Routes

**Initial prompt**

> Problem 7: Backend routes.
> we'll work on the React frontend dashboard on the next problem, but right now,
> we need a backend that it can call. in backend/main.py, we'll use FastAPI and
> add routes to: 1. return the three tickets and whether each is open or resolved;
> 2. take a ticket ID and run the agent team on that ticket; 3. return recent agent
> events (what each agent said and which tools they used), so the board can
> refresh; 4. approve a payment or purchase after a human clicks approve (agents
> only prepare the pay, but this route is what actually changes the cash);
> 5. return the current checking balance from cash_accounts; 6. reset the database
> to the og values when we want to try a fresh run.
> from the backend/ folder, we need to start the server with: uvicorn main:app
> --reload --port 8000, which should turn our backend at http://localhost:8000 so
> the frontend dashboard can call those routes. in output/harness.md, we'll list
> each route in one line (what URL and what it does).

**Follow-up prompt**

None needed. Built `backend/main.py` (FastAPI) with the six routes, all shop-state
access going through the one MCP server via a persistent client (no bypass).
Installed fastapi + uvicorn into the venv, started the server, and tested end to
end: `/tickets` lists all three open, `/cash` reads $3,400, `/approve` pays
invoice 501 and drops cash to $2,560 (and refuses a re-pay or an empty approver),
`/run` 404s on a bad ticket, and `/reset` restores $3,400. Routes documented in
`output/harness.md`.

**What was lacking after the first prompt**

Nothing in the instructions. One implementation detail worth noting: because the
start command runs `main:app` from inside `backend/`, `main.py` adds the project
root to `sys.path` so the `backend` package imports resolve, and the MCP client's
command path is resolved to absolute with cwd pinned to the project root so it
works regardless of where uvicorn is launched.

---

## Problem 8 — Agent Dashboard

**Initial prompt**

> Problem 8: Agent dashboard.
> we'll build the frontend dashboard in frontend/ with React + Vite + TypeScript.
> this page should call the routes that we built in P7.
> at minimum, the board must: 1. list all three tickets; 2. let one pick one
> ticket and start the agent team on it; 3. show each agent and what they are
> saying/doing while the ticket runs; 4. mark a ticket resolved when the run
> finishes; 5. show a short summary of what each agent did on that ticket; 6. let
> a human approve a pay or purchase when asked; 7. show the checking balance (it
> should drop after an approved pay).
> we'll make the style the dashboard with a calm and minimalistic feel, since this
> is a real desk that people should want to sit at. for colors, let's stay with
> neutrals (white, off white, beige, and let's pick gold and Yale blue for
> accents).
> we'll tell the frontend to talk to the backend at http://localhost:8000. on the
> backend, we'll allow the Vite page origin (which is usually http://localhost:5173)
> so the browser is allowed to call those routes. we'll start the board with:
> npm run dev.
> this command should open the React desk in the browser so I can pick tickets and
> watch the agents. we'll write output/design.md with what I wrote down for the
> dashboard look including layout, how agents read different, how resolved tickets
> and cash show up, and why (including the creative choices that make it feel
> special and something humans would enjoy using).
> while writing the output/design.md, ask me what explicitly you need so I can make
> the call and explain my reasoning. if, for whatever reason, my prompt is not good
> enough, let me know and I'll rewrite.

**Follow-up prompt** (the design calls I asked the user to make)

> [Via a design questionnaire, the user chose:] Layout = **two-pane desk** (ticket
> rail + focused workspace); agents "read different" via a **monogram badge +
> role name** (keeping the minimal palette); resolved tickets **move to a "Done"
> group**; the checking balance is a **persistent cash stat tile that animates
> down** on an approved payment.

The prompt was complete, so no rewrite was needed. I built the React + Vite + TS
app in `frontend/`, wired it to all the P7 routes, and verified end to end: the
production build type-checks, both servers run together, and CORS allows the Vite
origin. Two small backend touches were needed for the board: `/tickets` now
exposes the `lease_id`/`invoice_id` links so the approval panel knows what to pay,
and `/run` marks the ticket resolved once the team finishes. `output/design.md`
captures the look-and-feel decisions and rationale (left for the user to put the
"why" in their own words).

**Follow-up prompts** (preview + a live bug)

> I'll write the rationale, just tell me which I have to write I'll send it over
> Before moving fwd, can you open a draft so I can see what it looks like?

> Uh oh, when I clicked "run the agent team", it said "run failed: TypeError:
> Failed to fetch"

I installed Playwright + Chromium and screenshotted the real UI (initial board,
plus a full run + approval of ticket 102). The "Failed to fetch" surfaced a real
bug: the agents' MCP toolset in `agents.py` spawned the server with the *relative*
command `.venv/Scripts/python.exe`, which Windows resolves against the parent's
cwd — fine from the project root (the CLI runs) but not under uvicorn (cwd =
`backend/`). Fixed by resolving that command to an absolute path (as `main.py`
already did for its own client), in both `_build_mcp_toolsets` and
`_fetch_shop_date`. After the fix, a browser-driven run of ticket 102 completed,
the approval moved cash from $3,400 to $1,000, and the UI showed the feed, the
Done group, and the gold cash-flash — all verified with 0 console errors.

**What was lacking after the first prompt**

Nothing in the instructions (two typos corrected: "alow" → "allow", and the two
`https://localhost` URLs → `http://localhost`, since both servers run over http).
The gap was a cwd-dependent path bug that only showed up when the backend ran the
agents under uvicorn — caught by actually clicking the button in a browser.

**Follow-up prompts** (design polish, several mid-turn)

> 1. Let's make Resolved a green that matches the rest of the colors, Open should
> be dark red, and Needs approval should be gold. To make sure it pops, let's make
> the base colors Yale blue and its variants
> 2. For the font, let's make sure that headers and sub-headers are the serif that
> we chose so it looks cleaner
> 3. For what the agents are doing, we need to make it cleaner and more obvious for
> a human to understand what's happening and what action is required
> 4. Let's make the listing the skills at the bottom of each agent action cleaner.
> Maybe it's a balloon right below the action that has a smaller font

> Also, let me know if my color clashes with any that we already chose. And, let's
> choose little teddy bears for each agent so it looks different for each addition

> Let's swap the colors of Open and Need approval. And, for the header of the
> website, can you read Homework 4 folder and make sure that the header is
> consistent for branding

> go back into our prompts: is there anything explicitly saying that when something
> needs approval, it should be moved to Done? either way, we should make it so that
> when something needs approval that it gives a little pop for the approver
> for the colors, let's make sure that the colors are not the same at any point. for
> error messages, make sure that they look off-brand so it catches ppl attention
> that something is wrong
> the skills on the agent comment looks horrible now. can we make it so they look
> like "reply messages" within a thread?

What I did: made the base Yale-navy-forward; status colors each used for ONE
meaning — Open = gold, Needs approval = red, Resolved/Paid = green, errors = an
OFF-BRAND vermilion (deliberately jarring); pulled gold off the Boss ring and the
cash flash so gold means only "Open". Headers/sub-headers are the serif. Agents
are little teddy bears (🧸) with distinct jewel identity rings (none a status
color). Tool calls now render as threaded "reply" bubbles under each agent
message. The header matches the Homework 4 storefront branding (navy "CC"
monogram, "Campus *Customs*" in Fraunces, Inter UI, navy #00366b, no gold).
Confirmed via the prompt log that nothing ever said a needs-approval ticket should
go to Done — so the lifecycle is now Open → (run) → **Needs approval** (its own
group, with a gentle "pop") → (approve) → **Done**, and that status is decided
deterministically from an unpaid payable rather than the model's self-reported
flag. All verified in the browser (0 console errors): run → Needs approval → pay
$2,400 → cash $3,400 → $1,000 → Done.

**Follow-up prompts** (teddy colors, tools layout, the pop-up, ticket 103)

> It looks great, TY! Let's change the teddy bear colors so they're different from
> each other. And for the Tools, can we make it on one line so it looks cleaner, or
> do you think it'll make it look more cluttered? If the latter, let's just reduce
> the font size.
> Also, I didn't get the little pop-up when the invoice needed my approval.

> I also, for ticket 103, I don't see the option to approve. Can we see what's going
> on there?

> Let's make sure that the colors of the teddy bears themselves change, pls.

What I did: respread the five bear hues wide across the cool→magenta arc (purple /
teal / blue / magenta / indigo) so each reads as its own color, and tinted the 🧸
glyph **itself** with a per-agent hue-rotate CSS filter (not just the ring), since
the emoji is otherwise a fixed brown. Put the tools on one compact line of chips
under each agent comment (a small "↳ used" lead-in plus smaller bubbles) instead of
a vertical thread. Added a real approval **pop-up**: when a run finishes and the
ticket lands in Needs approval, a red toast slides in ("Ticket #N needs your
approval") and the card/banner keep their gentle pulse. Fixed ticket 103 (a
price_override / bulk-discount request): it has no invoice or lease, so the old
code showed no approve option; added a non-payment "discount" approval path —
front end shows an **Approve discount** panel, and `/approve` with `kind:"discount"`
just resolves the ticket and moves **no** cash (cash only ever goes out this term).
Verified in the browser (0 console errors): 103 now shows the Approve-discount
panel + action banner, and the five tinted bears render as distinct colors.

---

## Problem 9 — Resolve the Tickets

**Prompt**

> Resolve the tickets. Before we test the agents on a full run with the three
> tickets, let's reset the working db `data/campus_customs_new.db` so we start
> clean. Then, we'll note the starting checking balance and run all three tickets on
> the board until they're all resolved.
>
> Then, we'll open `output/desk_tickets.html` from Problem 6. On each ticket tab,
> we'll fill the Actual section from this run: which agents worked, what they
> delegated, and which tools they used. Let's keep Expected as is so we can compare
> the two.
>
> On the Cash tab of `output/desk_tickets.html`, we'll itemize the money: 1. starting
> checking balance (after the reset) 2. for each ticket: how cash changed when that
> ticket resolved, and why (which pay/purchase, dollar amount), and 3. ending
> checking balance, which must match `cash_accounts` in the working db.
>
> Wrong cash math loses points, so please let's make sure it's good to go. Also,
> let's save `output/resolved_tickets.json` (saving id, final status, short outcome,
> what each agent contributed, and any human approvals for each ticket) and
> `output/resolved_board.html` (a page we can double-click with a screenshot of your
> React board for each resolved ticket).
>
> We'll add read runs to `output/audit_trail.json`, and we'll finish
> `output/harness.md` so it covers tables, MCP tools, the five agents, API routes,
> the dashboard, and safety rules.

What I did: reset the working db, noted the starting balance ($3,400.00), and ran
all three tickets to resolution through the live React board (driven with
Playwright), approving each payment as the human. Final cash $160.00, verified to
match `cash_accounts` and the `payments` ledger (invoice #501 $840 + rent $2,400 =
$3,240 out; ticket 103's discount moved no cash). Filled the Actual section on each
ticket tab of `output/desk_tickets.html` from the real run (first call, delegation
chain, tools used) and left Expected unchanged, with an Expected-vs-actual note per
ticket. Filled the Cash tab with the starting balance, a per-ticket itemization
(what moved the money and why), the ending balance, and a reconciliation. Saved
`output/resolved_tickets.json` (per-ticket id, final status, outcome, each agent's
contribution, human approvals) and `output/resolved_board.html` (one board
screenshot per resolved ticket). The three runs appended to
`output/audit_trail.json`, and `output/harness.md` now also covers the dashboard and
the full-run results. 0 console errors across all three runs.

---

## Problem 10 — Reflection

**Prompt**

> Reflection. Now, we'll open `output/desk_tickets.html` and fill the Reflection
> tab. We'll answer in our own vibe while being detailed and thorough.
>
> 1. How would you evaluate the performance of the agents on each ticket and why?
> 2. For each ticket, how did Actual compare to the Expected plan we wrote earlier?
> 3. What would have been simpler as one agent with tools, and why?
> 4. Describe three new problems Campus Customs might face that this agent team could
>    solve with the tools we built.
> 5. Describe three new problems Campus Customs might face that this agent team could
>    not solve with the tools we built, and explain the tools and agent needed to
>    solve them.
>
> We need to tie every answer to this app and the three tickets we ran, using the
> ticket tabs and Cash tab on the same page as our evidence. Generic AI essays
> without Campus Customs details will score low, so please be mindful.

What I did: filled the Reflection tab of `output/desk_tickets.html` with all five
answers, each grounded in the actual run and this page's own evidence (the ticket
tabs and the Cash tab). Specifics used throughout: invoice #501 / <code>can_ship</code>
and the Boss over-delegating on 101; the minimal Boss → Facilities → Accounting
chain and the $2,560 cushion on 102; the 10% / $52.20 discount and the $0.00 cash
change on 103; the pattern that every payment ran at human approval, not in the loop;
the 0-stock mug and size-S tee for the "could solve" cases; and the fulfillment,
customer-billing, and send-message gaps (with the tools/agents each would need) for
the "could not solve" cases. Written in a plain voice with no AI-tell punctuation. 0
console errors.
