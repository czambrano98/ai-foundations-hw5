// Thin client for the Campus Customs backend (the FastAPI routes from Problem 7).
// The backend runs at http://localhost:8000 (plain http, not https).
const BASE = "http://localhost:8000";

export interface Ticket {
  id: number;
  type: string;
  subject: string;
  requester: string;
  status: string;
  resolved: boolean;
  sku?: string | null;
  size?: string | null;
  qty?: number | null;
  lease_id?: number | null;
  invoice_id?: number | null;
  notes?: string | null;
}

export interface AgentEvent {
  ts: string;
  run_id: string;
  agent: string;
  delegated_from: string | null;
  said: string;
  tools_used: string[];
  needs_human_approval: boolean;
  resolved: boolean;
  usage: Record<string, number>;
}

export interface Decision {
  summary: string;
  actions: string[];
  delegated_to: string[];
  needs_human_approval: boolean;
  resolved: boolean;
  drafts: string[];
}

export interface Cash {
  account: string;
  balance: number;
  as_of?: string;
}

export interface ApproveResult {
  ok: boolean;
  kind: string;
  amount: number;
  approved_by: string;
  new_balance: number;
  [k: string]: unknown;
}

async function jget<T>(path: string): Promise<T> {
  const r = await fetch(`${BASE}${path}`);
  if (!r.ok) throw new Error((await safeDetail(r)) || `GET ${path} failed (${r.status})`);
  return r.json();
}

async function jpost<T>(path: string, body?: unknown): Promise<T> {
  const r = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!r.ok) throw new Error((await safeDetail(r)) || `POST ${path} failed (${r.status})`);
  return r.json();
}

async function safeDetail(r: Response): Promise<string | null> {
  try {
    const j = await r.json();
    return typeof j?.detail === "string" ? j.detail : null;
  } catch {
    return null;
  }
}

export const api = {
  getTickets: () => jget<{ count: number; tickets: Ticket[] }>("/tickets"),
  getCash: () => jget<Cash>("/cash"),
  getEvents: (limit = 100) => jget<{ count: number; events: AgentEvent[] }>(`/events?limit=${limit}`),
  runTicket: (id: number) =>
    jpost<{ ticket_id: number; decision: Decision; resolved: boolean }>(`/tickets/${id}/run`),
  approve: (body: { kind: "invoice" | "rent" | "discount"; ref_id?: number; approved_by: string; ticket_id?: number }) =>
    jpost<ApproveResult>("/approve", body),
  reset: () => jpost<{ ok: boolean; message: string }>("/reset"),
};
