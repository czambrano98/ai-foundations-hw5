# Campus Customs Operations Desk: Design Notes

Carine Zambrano · AI Foundations · Fall 2026

This file records the look-and-feel decisions for the dashboard: the layout, the
palette, how the agents read apart, how resolved tickets and the cash show up, how
the human approves work, and the creative choices that make the desk feel unique
and worth using. Each section states the decision (the "what"). The rationale (the
"why") is in my own words, marked in each section.

## Intent

The dashboard should feel like a real desk a person would want to sit at: calm,
uncluttered, and a little special, not a busy control panel. The whole thing is
built around working one ticket at a time without anxiety.

**Why (in my words):** One sentence at the top. No mystery about what this place is.

## Layout: two-pane desk

A quiet ticket rail runs down the left. The selected ticket opens into a focused
workspace on the right. The cash tile sits at the top of the rail so the shop's
most important number stays in view.

**Why (in my words):** Board on the left, ticket in the center. You never lose sight of what's open.

## Palette and type

- **Base is Yale navy** (`#00366b`) and its variants. Navy carries the room, so the
  page reads as the shop's brand rather than a generic admin tool.
- **Each status color means one thing and nothing else:**
  - Open = gold (`#B0863F`)
  - Needs approval = red (`#9B2C3B`)
  - Resolved / Paid = green (`#2E6B4F`)
  - Error = vermilion (`#E5451F`), deliberately off-brand so a problem looks wrong
- No color is reused for a second meaning. Gold never appears except on Open, so a
  gold mark is always "this is still open."
- **Type pairing:** Fraunces (serif) for the nameplate, headers, ticket numbers,
  and the cash figure; Inter (sans) for the working UI. Numbers use tabular figures
  so the cash does not shift as it changes.

**Why (in my words):** Navy stays calm. One accent color per meaning: gold means "open," red means "needs your approval," green means "done" so you read the room instantly.

## How the agents read apart

Each agent appears in the activity feed as a little teddy bear (🧸). The bear glyph
itself is tinted to that agent's color with a CSS hue-rotate filter, and its badge
ring uses the same color:

- Boss = purple (`#8B3FB0`), with a lead ring to mark who runs the team
- Inventory = teal (`#0C8F8F`)
- Accounting = blue (`#2E6AD0`)
- Facilities = magenta (`#BE3A82`)
- Customer Service = indigo (`#5244C4`)

These five hues are spread wide and sit outside every status color, so a bear can
never be mistaken for a status. Each step also shows who asked (the delegation) and
the tools it used, laid out as one compact line of chips under the agent's comment.

**Why (in my words):** Each agent gets a named avatar, not just a color blob. They feel like teammates you root for a little, and I like teddy bears.

## Running a ticket

Pressing **Run the agent team** streams the agents' steps into the feed as they
work, with a gentle pulse while the run is in flight. The feed updates live instead
of dropping a single result at the end.

**Why (in my words):** You watch the agents work in real time. See when they're thinking, blocked, or done, which builds trust and helps see if there's anything going wrong.

## Ticket lifecycle: Open to Needs approval to Done

Tickets move through three groups in the rail: **Open**, then **Needs approval**,
then **Done**. The status is decided from the actual state of the shop (an unpaid
payable, or a pending pricing decision), not from the model's self-report. Nothing
in the agent prompts ever said a needs-approval ticket should jump straight to Done,
so it does not: a ticket only reaches Done once a human signs off.

A resolved ticket moves into the **Done** group with a green ✓ Resolved pill and a
slightly dimmed card, and stays one click away for review. The Open queue visibly
shrinks as you clear tickets.

**Why (in my words):** Clear states. You know exactly what each ticket needs from you without guessing.

## The approval pop-up

When a run finishes and the ticket lands in Needs approval, a red toast slides in
("Ticket #N needs your approval. Review it below.") and the ticket card and banner
keep a soft pulse until it is handled.

**Why (in my words):** Quick confirmation that doesn't interrupt. Approve, it toasts, you move on.

## Cash tile

A persistent tile at the top of the rail shows the checking balance in large
tabular figures. On an approved payment it ticks down with a brief neutral navy
flash (not a status color, so gold stays reserved for Open).

**Why (in my words):** Cash is always visible. A quiet flash when money moves confirms the approval went through.

## Approval: human in the loop

When the agents prepare work that needs a person, a red approval panel appears and
names exactly what is waiting. There are two kinds:

- **Payment** (an invoice or rent): clicking **Approve & pay** is the only thing
  that moves cash. The guarded pay tool still refuses without an approver or without
  enough cash, so the shop can never go negative.
- **Discount** (a bulk-pricing request): clicking **Approve discount** grants the
  decision and moves no cash at all, since cash only goes out this term.

The agents only prepare these; nothing changes the shop until a person signs off.

**Why (in my words):** Some decisions are only for the owner. The dashboard makes that clear.

## Errors look off-brand on purpose

Error messages use the vermilion that sits outside the whole brand palette, with a
heavier border. A problem is meant to look wrong at a glance rather than blend in.

**Why (in my words):** When something breaks, it should look wrong. Keeps you alert; you won't miss it.

## Plain, human copy

The interface copy avoids the tics people associate with machine-written text: no
em-dashes, no filler, no balanced "not just X but Y" lines. Sentences are short and
say what the screen is doing.

**Why (in my words):** No jargon. "Invoice overdue" not "accounting artifact threshold exceeded."

## Creative touches that make it enjoyable

A few choices are here to make the desk feel unique and worth returning to, not just
functional:

- **Teddy-bear teammates.** The five agents are tinted bears with their own colors
  and names, so a run feels like a small team working for you rather than a log file.
- **Watching the work happen.** The live feed lets you see the agents reason and hand
  off in real time. That is more satisfying, and more trustworthy, than a spinner
  that pops out a finished answer.
- **Small, earned moments.** The approval toast and the quiet navy cash flash are
  tiny confirmations that your action landed. The Open queue shrinking as you clear
  tickets turns a work session into visible progress.
- **Restraint as a feature.** Calm navy, lots of white space, one meaning per color,
  and plain copy. The desk stays quiet so the work stands out.

**Why (in my words):** A tool you use every day should have a little personality, so these touches make the desk feel made for a person instead of just shipped.

## Brand consistency with the storefront

The header matches the Campus Customs storefront from Homework 4: a navy circular
"CC" monogram, the name "Campus *Customs*" set in Fraunces with Customs in italic,
Inter for the UI, Yale navy throughout, and no gold in the brand mark itself.

**Why (in my words):** This desk is the shop. Same feel as the storefront so everything reads as one thing. Also, I was in marketing and deeply care about this.
