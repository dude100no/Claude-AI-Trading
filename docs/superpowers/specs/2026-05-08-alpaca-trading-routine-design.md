# Alpaca AI Trading Routine — Design Spec

**Date:** 2026-05-08
**Status:** Approved

---

## Overview

An autonomous AI trading routine built on Claude Code that runs Mon–Fri at 7:00 AM ET. Each session researches market conditions, loads prior context from a persistent memory layer, makes trading decisions across US equities, and executes orders via the Alpaca API. The agent notifies the user via Telegram after every session. On Fridays, it also produces a weekly performance review.

The routine starts in paper trading mode. Once validated, a single config flag switches it to live trading with ~SG$5000 (~US$3700) capital.

---

## Schedule

| Day | Behaviour |
|---|---|
| Mon–Thu | Market gate check → memory load → research → analysis → execution → memory update → Telegram summary |
| Friday | All of the above + weekly performance review and Telegram weekly report |
| NYSE Holidays | Session starts, detects holiday, exits immediately with no action |

The routine is defined as a Claude Code routine (`.claude/routines/trading-routine.md`), run locally via the Claude Code CLI. Future migration to Claude.ai cloud requires no code changes.

---

## Session Flow

### Step 1 — Market Gate Check
Query the Alpaca calendar API to confirm today is a trading day. If not (weekend or NYSE holiday), exit immediately and send no notification.

### Step 2 — Load Agent Memory
Read from the `memory/` folder before any analysis:

- `positions.json` — open positions with entry price, date, quantity, and original thesis
- `session_log.jsonl` — append-only log of every past session's decisions and reasoning
- `performance.json` — running P&L, win/loss record, full trade history
- `market_context.md` — prior session's market assessment and notes

This gives the agent full continuity across sessions. It knows why it holds each position and how its prior expectations compare to current reality.

### Step 3 — Portfolio Snapshot
Pull live state from Alpaca: cash balance, open positions, unrealized P&L, buying power. Cross-reference against `positions.json` to detect discrepancies (e.g., a stop-loss that triggered overnight).

### Step 4 — Market Research
- **Macro context:** VIX level, SPY/QQQ/DJI prior-day close and pre-market performance, sector ETF heatmap — via web search
- **News sweep:** Top market headlines from Alpaca's news feed + web search for major overnight/pre-market stories
- **Position-specific news:** For every currently held stock, check for relevant news that might affect the thesis

### Step 5 — AI Analysis & Decision
Claude reasons over memory + live portfolio + research data together:
- Assess overall market sentiment: bullish / bearish / neutral / mixed
- Choose trading style for the session: swing entry, short-term momentum, news-driven, or hold/defensive
- Revisit open position theses: hold conviction, add, trim, or exit
- Identify new position candidates with rationale
- Apply risk guardrails before finalising any trade

**Defensive mode:** If VIX > 40 or market opens down >2%, the agent enters defensive mode — no new positions, only manages existing ones (tighten stop-losses or exit). This is reasoned by Claude and explained in the summary, not hardcoded.

### Step 6 — Trade Execution
Place orders via `alpaca_client.py`. Every new position has a linked stop-loss order. Risk guardrails are enforced before any order is placed.

### Step 7 — Update Agent Memory
Write back to `memory/`:
- Update `positions.json` with any new or closed positions and their theses
- Append session record to `session_log.jsonl`
- Update `performance.json` with realised P&L from any closed trades
- Overwrite `market_context.md` with today's assessment and key notes for the next session

### Step 8 — Telegram Notification
Send a structured message containing:
- Market sentiment assessment
- Trades executed (symbol, direction, size, rationale) — or "No trades today" with reason
- Current portfolio: positions, cash, total value
- Any risk flags triggered

### Step 9 — Friday Weekly Review (Fridays only)
After Steps 1–8 complete, run the weekly review:
- Read all session logs from Mon–Fri
- Calculate: weekly P&L, best/worst trade, win rate, max drawdown
- Assess whether the agent's strategy appears to be working or needs adjustment
- Send a detailed weekly Telegram report separate from the daily summary

---

## Risk Guardrails

All enforced in `alpaca_client.py` before any order is placed:

| Guardrail | Default | Configurable |
|---|---|---|
| Max portfolio % per position | 10% | Yes (`max_position_pct`) |
| Stop-loss below entry | 5% | Yes (`stop_loss_pct`) |
| Max open positions | 5 | Yes (`max_open_positions`) |
| Kill switch | Off | Yes (`halt: true` in config.json) |

---

## Error Handling

| Scenario | Behaviour |
|---|---|
| Market calendar API fails | Default to no trading, send Telegram alert |
| Alpaca order rejected | Log failure, notify via Telegram, do not retry |
| Alpaca connection failure | Retry once after 30s, then skip and notify |
| Partial fill | Treat as executed at actual filled quantity, update memory |
| Web search / news fetch fails | Proceed with available data, apply conservative stance (no new positions), flag in summary |
| Memory file missing or corrupt | Rebuild from live Alpaca portfolio, start fresh log, notify via Telegram |
| Friday weekly review fails | Daily summary still sent; weekly review failure is non-blocking |
| `halt: true` in config | Skip all trading, send Telegram alert, exit |

---

## Components

### `alpaca_client.py`
Thin wrapper around the Alpaca REST API. Reads credentials from environment variables. Exposes:
- `get_calendar(date)` — check if market is open
- `get_portfolio()` — positions, cash, buying power
- `get_market_data(symbols)` — price, volume, basic technicals
- `get_news(symbols, limit)` — Alpaca news feed
- `place_order(symbol, qty, side, stop_loss_pct)` — buy/sell with linked stop-loss
- `close_position(symbol)` — full exit

### `telegram_notify.py`
Sends messages via Telegram Bot API (HTTP POST, no library dependency). Reads `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` from environment.

### `config.json`
Tunable parameters only — no secrets:
```json
{
  "max_position_pct": 0.10,
  "stop_loss_pct": 0.05,
  "max_open_positions": 5,
  "paper_trading": true,
  "halt": false
}
```

### `memory/`
```
memory/
  positions.json       # open positions + entry data + thesis
  session_log.jsonl    # one JSON line per session (append-only)
  performance.json     # running P&L and trade history
  market_context.md    # last session's market notes
```

### `.claude/routines/trading-routine.md`
The Claude Code routine definition. Contains the agent's full instructions, cron schedule (Mon–Fri 7AM ET), and environment variable declarations (no secret values stored here — values are set in the routine's environment config).

---

## Environment Variables (stored in routine environment config, not in repo)

- `ALPACA_API_KEY`
- `ALPACA_SECRET_KEY`
- `ALPACA_BASE_URL` — `https://paper-api.alpaca.markets` for paper, `https://api.alpaca.markets` for live
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

---

## Project Structure

```
Claude-AI-Trading/
  .claude/
    routines/
      trading-routine.md      # routine definition + instructions
  memory/
    positions.json
    session_log.jsonl
    performance.json
    market_context.md
  logs/                        # raw session output archive
  docs/
    superpowers/
      specs/
        2026-05-08-alpaca-trading-routine-design.md
  alpaca_client.py
  telegram_notify.py
  config.json
  requirements.txt
```

---

## Out of Scope (for now)

- ETF trading (planned future expansion)
- Crypto trading
- Intraday / day trading
- Options or leveraged instruments
- Multi-account support
- Web dashboard or UI
