// Agent identity for the activity feed. Each agent is a little teddy bear (🧸).
// The 🧸 glyph is a fixed brown bear, so to make each BEAR itself a different
// color we tint its pixels with a per-agent CSS hue-rotate `filter`; the badge
// RING uses the matching hex so the identity reads the same way twice.
// Both are chosen OUTSIDE the status palette (gold/red/green), the navy base,
// and the vermilion error, so a bear can never be mistaken for a status.

export interface AgentMeta {
  label: string;
  ring: string;    // badge ring color = agent identity (matches the tint)
  filter: string;  // CSS filter that tints the brown 🧸 onto this agent's hue
  lead?: boolean;  // the Boss leads the team
}

// Five hues spread wide across the cool→magenta arc so each bear reads as
// clearly its own color. The brown 🧸 sits near hue ~30°, so each hue-rotate is
// (target hue − 30) and saturate keeps the tint vivid rather than muddy.
export const AGENTS: Record<string, AgentMeta> = {
  boss: { label: "Boss", ring: "#8B3FB0", filter: "hue-rotate(250deg) saturate(1.5)", lead: true }, // purple
  inventory: { label: "Inventory", ring: "#0C8F8F", filter: "hue-rotate(150deg) saturate(1.6)" },   // teal
  accounting: { label: "Accounting", ring: "#2E6AD0", filter: "hue-rotate(190deg) saturate(1.6)" },  // blue
  facilities: { label: "Facilities", ring: "#BE3A82", filter: "hue-rotate(300deg) saturate(1.5)" },  // magenta
  customer_service: { label: "Customer Service", ring: "#5244C4", filter: "hue-rotate(220deg) saturate(1.5)" }, // indigo
};

export function agentMeta(key: string): AgentMeta {
  return AGENTS[key] ?? { label: key, ring: "#567A8A", filter: "none" };
}
