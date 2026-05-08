# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Is

An autonomous AI trading agent that runs on a cron schedule (Mon–Fri 7 AM ET). The agent researches markets, decides on trades, executes orders via Alpaca, persists state across sessions, and sends a Telegram summary. The routine definition lives in `.claude/routines/trading-routine.md`.

## Environment Variables

All secrets are passed as environment variables — nothing is hardcoded:

| Variable | Purpose |
|---|---|
| `ALPACA_API_KEY` | Alpaca API key |
| `ALPACA_SECRET_KEY` | Alpaca secret key |
| `ALPACA_BASE_URL` | `https://paper-api.alpaca.markets` (paper) or live URL |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token |
| `TELEGRAM_CHAT_ID` | Target chat or channel ID |

## Commands

```bash
# Setup (creates .venv, installs deps, initializes memory files, runs tests)
bash setup.sh

# Run all tests
python -m pytest tests/

# Run a single test file
python -m pytest tests/test_alpaca_client.py

# Run a single test by name
python -m pytest tests/test_alpaca_client.py::test_place_order_buy

# CLI — each module is directly invokable
python alpaca_client.py check_calendar
python alpaca_client.py get_portfolio
python alpaca_client.py get_market_data AAPL MSFT
python alpaca_client.py get_news AAPL
python alpaca_client.py place_order AAPL 5 buy 0.05
python alpaca_client.py close_position AAPL

python telegram_notify.py "Your message here"
```

## Architecture

### Core Modules

**`alpaca_client.py`** — All Alpaca interaction. Exposes a CLI (`python alpaca_client.py <command> [args]`) that outputs JSON. Functions: `get_calendar`, `get_portfolio`, `get_market_data`, `get_news`, `place_order`, `close_position`. Every `place_order` call automatically attaches a trailing stop-loss. The `halt` flag in `config.json` blocks all orders.

**`telegram_notify.py`** — Thin wrapper around the Telegram Bot HTTP API (no library). Sends markdown-formatted messages to the configured chat. CLI: `python telegram_notify.py "text"`.

### Session Orchestration

The routine (`.claude/routines/trading-routine.md`, schedule `0 12 * * 1-5`) runs the agent as Claude Code. The 9-step flow is:

1. **Halt check** → read `config.json`; abort if `halt: true`
2. **Market gate** → `check_calendar`; abort silently on non-trading days
3. **Load memory** → read all four `memory/` files to reconstruct context
4. **Portfolio reconciliation** → compare live positions to `memory/positions.json`; detect stop-loss triggers
5. **Market research** → web search (VIX, SPY/QQQ, sectors) + Alpaca news + OHLCV for held positions
6. **AI analysis** → sentiment classification, style selection, hold/exit/add decisions, new candidates
7. **Position sizing** → `qty = floor(portfolio_value × max_position_pct / price)`; enforce `max_open_positions`
8. **Trade execution** → `place_order` / `close_position` via CLI
9. **Memory update + Telegram summary** → rewrite all four files; send daily message; Friday = weekly review

### Memory Layer (`memory/`)

Four files persist state across sessions. The routine rewrites all of them at end-of-session:

| File | Format | Purpose |
|---|---|---|
| `positions.json` | JSON array | Open positions with entry data and thesis |
| `session_log.jsonl` | Append-only JSONL | One line per session: trades, sentiment, rationale |
| `performance.json` | JSON object | Cumulative P&L, win/loss counts, closed trade history |
| `market_context.md` | Markdown | Current market assessment and next-session watch list |

### Risk Controls

Defined in `config.json` (non-secret, committed):
- `max_position_pct: 0.10` — no single position > 10% of portfolio
- `stop_loss_pct: 0.05` — default trailing stop on every buy
- `max_open_positions: 5` — hard cap enforced before any buy
- `paper_trading: true` — points at paper API; flip to `false` for live
- `halt: false` — kill switch; set `true` to block all trading immediately

Defensive mode activates automatically when VIX > 40 or market opens down > 2%.

## Testing

All tests use mocks — no live API calls. The test suite covers every public function in both modules including edge cases (halted trading, empty positions, missing credentials).

```bash
python -m pytest tests/ -v
```
