import { useEffect, useMemo, useRef, useState } from "react";
import { api, type AgentEvent, type ApproveResult, type Cash, type Decision, type Ticket } from "./api";
import { agentMeta } from "./agents";

const TYPE_LABEL: Record<string, string> = {
  customer_order: "Customer order",
  rent_notice: "Rent notice",
  price_override: "Discount request",
};

// Something a human can approve. A payment (invoice/rent) actually moves cash;
// a discount (price_override) is a judgment call that moves no money but still
// needs a human to grant it, so it gets an approval step of its own.
type Approvable =
  | { kind: "invoice" | "rent"; ref_id: number; label: string; pays: true }
  | { kind: "discount"; label: string; pays: false };

function approvableFor(t: Ticket): Approvable | null {
  if (t.type === "rent_notice" && t.lease_id != null)
    return { kind: "rent", ref_id: t.lease_id, label: `Rent for lease #${t.lease_id}`, pays: true };
  if (t.type === "customer_order" && t.invoice_id != null)
    return { kind: "invoice", ref_id: t.invoice_id, label: `Invoice #${t.invoice_id}`, pays: true };
  if (t.type === "price_override")
    return { kind: "discount", label: t.subject, pays: false };
  return null;
}

export default function App() {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [cash, setCash] = useState<Cash | null>(null);
  const [events, setEvents] = useState<AgentEvent[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [runningId, setRunningId] = useState<number | null>(null);
  const [runInfo, setRunInfo] = useState<Record<number, { startTs: string; decision?: Decision }>>({});
  const [paid, setPaid] = useState<Record<number, ApproveResult>>({});
  const [approver, setApprover] = useState("Carine (owner)");
  const [approveError, setApproveError] = useState<string | null>(null);
  const [cashFlash, setCashFlash] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [toast, setToast] = useState<string | null>(null);
  const pollRef = useRef<number | null>(null);
  const toastRef = useRef<number | null>(null);

  function popToast(msg: string) {
    setToast(msg);
    if (toastRef.current) window.clearTimeout(toastRef.current);
    toastRef.current = window.setTimeout(() => setToast(null), 6000);
  }

  useEffect(() => {
    void refreshAll();
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function refreshAll() {
    try {
      const [t, c, e] = await Promise.all([api.getTickets(), api.getCash(), api.getEvents(100)]);
      setTickets(t.tickets); setCash(c); setEvents(e.events); setError(null);
      if (selectedId == null && t.tickets.length) setSelectedId(t.tickets[0].id);
    } catch (e) {
      setError(`Can't reach the backend at http://localhost:8000. Is it running? (${String(e)})`);
    }
  }

  function flashCash() { setCashFlash(true); window.setTimeout(() => setCashFlash(false), 950); }

  const openT = tickets.filter((t) => t.status === "open");
  const awaiting = tickets.filter((t) => t.status === "awaiting_approval");
  const done = tickets.filter((t) => t.status === "resolved");
  const selected = useMemo(() => tickets.find((t) => t.id === selectedId) ?? null, [tickets, selectedId]);

  async function runSelected() {
    if (selectedId == null || runningId != null) return;
    const id = selectedId;
    setApproveError(null); setError(null);
    let afterTs = "";
    try {
      const before = await api.getEvents(100);
      afterTs = before.events.reduce((m, e) => (e.ts > m ? e.ts : m), "");
    } catch { /* surfaced below */ }
    setRunInfo((r) => ({ ...r, [id]: { startTs: afterTs } }));
    setRunningId(id);

    pollRef.current = window.setInterval(async () => {
      try {
        const [ev, c] = await Promise.all([api.getEvents(100), api.getCash()]);
        setEvents(ev.events); setCash(c);
      } catch { /* transient */ }
    }, 1500);

    try {
      const res = await api.runTicket(id);
      setRunInfo((r) => ({ ...r, [id]: { ...(r[id] ?? { startTs: afterTs }), decision: res.decision } }));
    } catch (e) {
      setError(`Run failed: ${String(e)}`);
    } finally {
      if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null; }
      try {
        const [t, ev, c] = await Promise.all([api.getTickets(), api.getEvents(100), api.getCash()]);
        setTickets(t.tickets); setEvents(ev.events); setCash(c);
        const ran = t.tickets.find((x) => x.id === id);
        if (ran && ran.status === "awaiting_approval") {
          popToast(`Ticket #${id} needs your approval. Review it below.`);
        }
      } catch { /* ignore */ }
      setRunningId(null);
    }
  }

  async function approve(t: Ticket) {
    const a = approvableFor(t);
    if (!a) return;
    setApproveError(null);
    try {
      const res = await api.approve({
        kind: a.kind,
        ref_id: a.pays ? a.ref_id : undefined,
        approved_by: approver,
        ticket_id: t.id,
      });
      setPaid((s) => ({ ...s, [t.id]: res }));
      const [c, tk] = await Promise.all([api.getCash(), api.getTickets()]);
      setCash(c); setTickets(tk.tickets);
      if (a.pays) flashCash();  // only a real payment moves cash, so only it flashes
    } catch (e) {
      setApproveError(String(e instanceof Error ? e.message : e));
    }
  }

  async function reset() {
    try {
      await api.reset();
      setRunInfo({}); setPaid({}); setApproveError(null);
      await refreshAll();
    } catch (e) {
      setError(`Reset failed: ${String(e)}`);
    }
  }

  return (
    <div className="app">
      <div className="topbar">
        <div className="brand">
          <span className="brand-mark" aria-hidden="true">CC</span>
          <h1>Campus <span className="accent">Customs</span></h1>
          <span className="tag">Operations Desk</span>
        </div>
        <div className="right">
          {cash?.as_of && <span className="shopdate">Shop date&nbsp;<b>{cash.as_of}</b></span>}
          <button className="btn ghost small" onClick={reset}>Reset board</button>
        </div>
      </div>
      {error && <div className="topbar-err"><span>⚠</span>{error}</div>}

      {toast && (
        <div className="toast" role="status" onClick={() => setToast(null)}>
          <span className="toast-ic">⚑</span>
          <span>{toast}</span>
          <span className="toast-x" aria-hidden="true">×</span>
        </div>
      )}

      <div className="main">
        <aside className="rail">
          <div className={`cash ${cashFlash ? "flash" : ""}`}>
            <div className="label">Checking</div>
            <div className="value num">{cash ? fmtMoney(cash.balance) : "—"}</div>
            <div className="sub">Cash only goes out this term</div>
          </div>

          <RailGroup title="Open" tickets={openT} selectedId={selectedId} runningId={runningId}
            paid={paid} onPick={setSelectedId} emptyText="No open tickets" />
          <RailGroup title="Needs approval" tickets={awaiting} selectedId={selectedId} runningId={runningId}
            paid={paid} onPick={setSelectedId} emptyText="Nothing awaiting approval" />
          <RailGroup title="Done" tickets={done} selectedId={selectedId} runningId={runningId}
            paid={paid} onPick={setSelectedId} emptyText="Nothing resolved yet" />
        </aside>

        <main className="workspace">
          {!selected ? (
            <div className="empty-state">
              <div className="big">Pick a ticket to begin</div>
              <div>Select a ticket on the left to run the team and watch them work.</div>
            </div>
          ) : (
            <Workspace
              t={selected}
              running={runningId === selected.id}
              events={events.filter((e) => runInfo[selected.id] && e.ts > runInfo[selected.id].startTs)}
              decision={runInfo[selected.id]?.decision}
              paid={paid[selected.id]}
              approver={approver} setApprover={setApprover}
              approveError={approveError}
              onRun={runSelected} onApprove={() => approve(selected)}
            />
          )}
        </main>
      </div>
    </div>
  );
}

/* ---------------- rail ---------------- */

function RailGroup(props: {
  title: string; tickets: Ticket[]; selectedId: number | null; runningId: number | null;
  paid: Record<number, ApproveResult>; onPick: (id: number) => void; emptyText: string;
}) {
  const { title, tickets, selectedId, runningId, paid, onPick, emptyText } = props;
  return (
    <div>
      <h2>{title}</h2>
      <div className="ticket-group">
        {tickets.length === 0 && <div className="group-empty">{emptyText}</div>}
        {tickets.map((t) => (
          <TicketCard key={t.id} t={t} active={t.id === selectedId}
            running={t.id === runningId} paid={!!paid[t.id]} onClick={() => onPick(t.id)} />
        ))}
      </div>
    </div>
  );
}

function TicketCard(props: { t: Ticket; active: boolean; running: boolean; paid: boolean; onClick: () => void }) {
  const { t, active, running, onClick } = props;
  const awaiting = t.status === "awaiting_approval";
  return (
    <button className={`tcard ${active ? "active" : ""} ${t.status === "resolved" ? "resolved" : ""} ${awaiting ? "awaiting" : ""}`} onClick={onClick}>
      <div className="row">
        <span className="id">#{t.id}</span>
        {running ? <span className="pill running">running…</span>
          : t.status === "resolved" ? <span className="pill resolved">✓ Resolved</span>
          : awaiting ? <span className="pill approval">● Needs approval</span>
          : <span className="pill open">Open</span>}
      </div>
      <span className="subj">{t.subject}</span>
      <span className="req">{TYPE_LABEL[t.type] ?? t.type} · {t.requester}</span>
    </button>
  );
}

/* ---------------- workspace ---------------- */

function Workspace(props: {
  t: Ticket; running: boolean; events: AgentEvent[]; decision?: Decision;
  paid?: ApproveResult; approver: string; setApprover: (s: string) => void;
  approveError: string | null; onRun: () => void; onApprove: () => void;
}) {
  const { t, running, events, decision, paid, approver, setApprover, approveError, onRun, onApprove } = props;
  const approvable = approvableFor(t);
  const awaiting = t.status === "awaiting_approval";

  const banner = running
    ? { cls: "working", ic: "⏳", text: "The team is working on this ticket." }
    : awaiting && !paid
    ? { cls: "action", ic: "⚑", text: "Action needed. Review and approve below." }
    : paid || t.status === "resolved"
    ? { cls: "done", ic: "✓", text: paid ? "Payment approved." : "Resolved." }
    : null;

  return (
    <>
      <div className="ws-head">
        <div>
          <h2>#{t.id} · {t.subject}</h2>
          <div className="meta">{TYPE_LABEL[t.type] ?? t.type} · requested by {t.requester}</div>
          <div className="facts">
            {t.sku && <span><b>Item</b> {t.sku}{t.size ? ` / ${t.size}` : ""}{t.qty ? ` ×${t.qty}` : ""}</span>}
            {t.invoice_id != null && <span><b>Invoice</b> #{t.invoice_id}</span>}
            {t.lease_id != null && <span><b>Lease</b> #{t.lease_id}</span>}
          </div>
        </div>
        <div>
          {t.status === "open"
            ? <button className="btn" onClick={onRun} disabled={running}>{running ? "Team is working…" : "Run the agent team"}</button>
            : t.status === "resolved" ? <span className="pill resolved">✓ Resolved</span>
            : <span className="pill approval">● Needs approval</span>}
        </div>
      </div>

      {banner && <div className={`banner ${banner.cls}`}><span className="ic">{banner.ic}</span> {banner.text}</div>}

      <div className="section">
        <h3>Agent activity {events.length > 0 && <span className="count">· {events.length} steps</span>}</h3>
        <div className="feed">
          {events.length === 0 && !running && (
            <div className="feed-empty">
              {t.status === "open" ? "Run the team to watch the agents work this ticket."
                : "This ticket was handled in an earlier session. The outcome is below."}
            </div>
          )}
          {events.map((e, i) => <EventRow key={`${e.run_id}-${i}`} e={e} />)}
          {running && (
            <div className="event">
              <div className="badge" style={{ borderColor: "var(--navy-ring)" }}>🧸</div>
              <div className="body"><div className="thinking">
                <span className="dot" /><span className="dot" /><span className="dot" />&nbsp;the team is working…
              </div></div>
            </div>
          )}
        </div>
      </div>

      {approvable && !paid && awaiting && (
        <div className="section">
          <div className="panel approve">
            <h4>⚑ Awaiting your approval</h4>
            <div className="approve-what">
              {approvable.pays ? (
                <>The agents prepared a payment, <b>{approvable.label}</b>. The agents can't move money,
                so your approval here is what pays it.</>
              ) : (
                <>The agents prepared a decision, <b>{approvable.label}</b>. No cash moves. Your approval
                here grants the discount.</>
              )}
            </div>
            <div className="approve-row">
              <label>Approved by</label>
              <input value={approver} onChange={(ev) => setApprover(ev.target.value)} />
              <button className="btn" onClick={onApprove}>{approvable.pays ? "Approve & pay" : "Approve discount"}</button>
            </div>
            {approveError && <div className="err">⚠ {approveError}</div>}
          </div>
        </div>
      )}
      {approvable && paid && (
        <div className="section">
          <div className="panel paid">
            <h4>✓ {paid.kind === "discount" ? "Discount approved" : "Payment approved"}</h4>
            <div className="summary">
              {paid.kind === "discount" ? (
                <>Discount granted, approved by {paid.approved_by}. No cash moved. Balance stays
                at <b className="num">{fmtMoney(paid.new_balance)}</b>.</>
              ) : (
                <>Paid <b className="num">{fmtMoney(paid.amount)}</b> ({paid.kind}), approved by {paid.approved_by}.
                New balance <b className="num">{fmtMoney(paid.new_balance)}</b>.</>
              )}
            </div>
          </div>
        </div>
      )}

      {decision && (
        <div className="section">
          <h3>Outcome</h3>
          <div className="panel">
            <div className="summary">{decision.summary}</div>
            {decision.drafts?.length > 0 && (
              <div style={{ marginTop: 10 }}>
                <b style={{ fontSize: 13 }}>Drafts left on the board (not sent):</b>
                <ul style={{ margin: "6px 0 0", paddingLeft: 18 }}>
                  {decision.drafts.map((d, i) => <li key={i} style={{ fontSize: 13 }}>{d}</li>)}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}
    </>
  );
}

function EventRow({ e }: { e: AgentEvent }) {
  const m = agentMeta(e.agent);
  return (
    <div className={`event ${e.needs_human_approval ? "needs" : ""}`}>
      <div className={`badge ${m.lead ? "lead" : ""}`} style={{ borderColor: m.ring, color: m.ring }} title={m.label}>
        <span className="bear" style={{ filter: m.filter }}>🧸</span>
      </div>
      <div className="body">
        <div className="who">
          <span className="name">{m.label}</span>
          {e.delegated_from && <span className="from">· asked by {agentMeta(e.delegated_from).label}</span>}
          {e.needs_human_approval && <span className="pill approval">● action needed</span>}
        </div>
        <div className="said">{e.said}</div>
        {e.tools_used.length > 0 && (
          <div className="tool-thread">
            <span className="thread-lead">↳ used</span>
            {e.tools_used.map((tool, i) => (
              <span className="bubble" key={i}>
                <span className="t">{tool.replace("campus-customs_", "")}</span>
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function fmtMoney(n: number): string {
  return n.toLocaleString("en-US", { style: "currency", currency: "USD", minimumFractionDigits: 0, maximumFractionDigits: 0 });
}
