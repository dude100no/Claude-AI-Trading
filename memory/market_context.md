# Market Context — 2026-07-07 (ACCOUNT-INTEGRITY INCIDENT)

**Sentiment:** N/A — session dominated by an account anomaly, not market conditions
**VIX:** not researched (defensive posture; no new entries possible this session)
**Key indices:** not researched this session
**Style used today:** Defensive / incident remediation — flattened to cash, no new capital deployed

## What happened (the incident)

This branch's memory was **stale since 2026-06-02**. Between 06-03 and 07-07, ~30+ live
trades ran on the Alpaca paper account that were never persisted to this branch (they may
have run against a different branch/environment). The live account, not memory, is the
source of truth.

On 2026-07-07 the live snapshot showed a **corrupted state**:
- Equity had fallen from `last_equity` **$104,224.70** to **$51,934.57** — roughly **-50% in
  one day** — with **no trades** explaining it (07-07 activity was only the GEV stop firing).
- The entire long book (~8 positions: **COST, GOOGL, UNH, HD, ABBV, NEE, VEA, V**) had been
  **wiped from the account without any sale proceeds** — cash stayed ~$56k, so ~$48k of
  position value simply evaporated. This is a **paper-account reset / position-wipe
  (broker/account integrity event), not a trading loss.**
- The 8 wiped positions left **8 orphaned trailing-stop SELL orders** behind. One of them
  (GEV) already **fired against a non-existent long, opening an unintended naked short (-4)**.

## Remediation taken (safest posture given the anomaly)

1. **Cancelled all 8 orphaned trailing-stop SELL orders** — each could otherwise fire and
   open a further naked short (unbounded risk on long-only mandate).
2. **Covered the GEV naked short** via `close_position` (bought 4 @ $1040.01, realized
   +$41.96).
3. **Opened no new positions** — DEFENSIVE. The ~$52k unexplained account drop means the
   environment cannot be trusted for capital deployment this session. "When uncertain, do
   nothing."

**Account now:** FLAT — **$51,918.89 all cash, 0 positions, 0 open orders.**

## Watching / needs user attention next session

- **User must investigate the paper-account wipe.** Confirm whether Alpaca reset the paper
  account, whether it was a manual intervention, or a data/margin anomaly. Until understood,
  do not resume normal deployment.
- Branch/memory divergence: this branch (`claude/gifted-lovelace-fz25i3`) is disconnected
  from wherever the 06-03..07-07 sessions ran. Confirm the intended persistence branch
  (routine specifies a `remote` branch that does not exist in this checkout).
- Once the account is confirmed healthy and starting equity is known, rebuild a diversified
  book from the clean cash base using the normal 5%-per-entry sizing.
- Historical P&L for 06-03..07-07 is unreconciled and likely meaningless given the wipe.
