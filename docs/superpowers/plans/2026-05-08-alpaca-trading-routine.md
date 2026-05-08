# Alpaca AI Trading Routine — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a fully autonomous Claude Code trading routine that researches US equity markets each weekday, makes risk-managed trading decisions, executes orders via Alpaca, maintains persistent memory across sessions, and sends Telegram notifications.

**Architecture:** A Claude Code routine definition drives the agent logic. Two Python utility scripts (`alpaca_client.py`, `telegram_notify.py`) handle external API calls and are invoked by the agent via bash. A `memory/` folder provides full cross-session continuity. All secrets live in the routine's environment config — nothing in the repo.

**Tech Stack:** Python 3.10+, alpaca-py, requests, pytest, pytest-mock

---

## File Map

| File | Action | Purpose |
|---|---|---|
| `.gitignore` | Create | Exclude caches, logs, secrets |
| `requirements.txt` | Create | Python dependencies |
| `config.json` | Create | Tunable trading parameters (no secrets) |
| `logs/.gitkeep` | Create | Preserve empty logs directory in git |
| `memory/positions.json` | Create | Open positions with entry data and thesis |
| `memory/session_log.jsonl` | Create | Append-only log of every session |
| `memory/performance.json` | Create | Running P&L and trade history |
| `memory/market_context.md` | Create | Prior session market notes |
| `tests/test_telegram_notify.py` | Create | Tests for Telegram notifier |
| `telegram_notify.py` | Create | Telegram Bot API sender + CLI |
| `tests/test_alpaca_client.py` | Create | Tests for Alpaca client |
| `alpaca_client.py` | Create | Alpaca REST API wrapper + CLI |
| `.claude/routines/trading-routine.md` | Create | Claude Code routine definition |

---

## Task 1: Project Scaffolding

**Files:**
- Create: `.gitignore`
- Create: `requirements.txt`
- Create: `config.json`
- Create: `logs/.gitkeep`

- [ ] **Step 1: Create `.gitignore`**

```
__pycache__/
*.pyc
*.pyo
.pytest_cache/
.eggs/
*.egg-info/
dist/
build/
logs/*.log
logs/*.jsonl
```

- [ ] **Step 2: Create `requirements.txt`**

```
alpaca-py>=0.38.0
requests>=2.31.0
pytest>=8.0.0
pytest-mock>=3.12.0
```

- [ ] **Step 3: Create `config.json`**

```json
{
  "max_position_pct": 0.10,
  "stop_loss_pct": 0.05,
  "max_open_positions": 5,
  "paper_trading": true,
  "halt": false
}
```

- [ ] **Step 4: Create `logs/.gitkeep`**

Create an empty file at `logs/.gitkeep`.

- [ ] **Step 5: Install dependencies**

Run: `pip install -r requirements.txt`

Expected: All packages install without error.

- [ ] **Step 6: Commit**

```bash
git add .gitignore requirements.txt config.json logs/.gitkeep
git commit -m "feat: project scaffolding — config, deps, gitignore"
```

---

## Task 2: Memory Layer Initialization

**Files:**
- Create: `memory/positions.json`
- Create: `memory/session_log.jsonl`
- Create: `memory/performance.json`
- Create: `memory/market_context.md`

- [ ] **Step 1: Create `memory/positions.json`**

```json
[]
```

This is an array. Each entry when populated will be:
```json
{
  "symbol": "AAPL",
  "qty": 5,
  "entry_price": 185.50,
  "entry_date": "2026-05-08",
  "thesis": "Breaking out above 200-day MA on high volume",
  "stop_loss_pct": 0.05,
  "order_id": "abc123"
}
```

- [ ] **Step 2: Create `memory/session_log.jsonl`**

Create an empty file at `memory/session_log.jsonl`.

Each session will append one JSON line in this format:
```json
{"date": "2026-05-08", "sentiment": "bullish", "style": "swing", "trades": [{"symbol": "AAPL", "side": "buy", "qty": 5, "price": 185.50, "rationale": "Breakout on volume"}], "no_trade_reason": null, "notes": "VIX at 18, tech sector strong"}
```

- [ ] **Step 3: Create `memory/performance.json`**

```json
{
  "total_realized_pl": 0.0,
  "total_trades": 0,
  "winning_trades": 0,
  "losing_trades": 0,
  "trade_history": []
}
```

Each closed trade appended to `trade_history`:
```json
{
  "symbol": "AAPL",
  "side": "sell",
  "qty": 5,
  "entry_price": 185.50,
  "exit_price": 192.00,
  "entry_date": "2026-05-06",
  "exit_date": "2026-05-08",
  "realized_pl": 32.50
}
```

- [ ] **Step 4: Create `memory/market_context.md`**

```markdown
# Market Context

No prior session data. Starting fresh.
```

- [ ] **Step 5: Commit**

```bash
git add memory/
git commit -m "feat: initialise memory layer with empty state files"
```

---

## Task 3: Telegram Notifier

**Files:**
- Create: `tests/test_telegram_notify.py`
- Create: `telegram_notify.py`

- [ ] **Step 1: Create `tests/` directory and write failing tests**

Create `tests/__init__.py` (empty file).

Create `tests/test_telegram_notify.py`:

```python
import pytest
from unittest.mock import patch, MagicMock


def test_send_message_posts_to_correct_url(monkeypatch):
    monkeypatch.setenv('TELEGRAM_BOT_TOKEN', 'test-token')
    monkeypatch.setenv('TELEGRAM_CHAT_ID', '12345')

    mock_response = MagicMock()
    mock_response.json.return_value = {'ok': True, 'result': {'message_id': 1}}
    mock_response.raise_for_status = MagicMock()

    with patch('requests.post', return_value=mock_response) as mock_post:
        import telegram_notify
        result = telegram_notify.send_message('Hello World')

        mock_post.assert_called_once_with(
            'https://api.telegram.org/bottest-token/sendMessage',
            json={'chat_id': '12345', 'text': 'Hello World', 'parse_mode': 'Markdown'},
            timeout=10,
        )
        assert result == {'ok': True, 'result': {'message_id': 1}}


def test_send_message_raises_on_http_error(monkeypatch):
    monkeypatch.setenv('TELEGRAM_BOT_TOKEN', 'test-token')
    monkeypatch.setenv('TELEGRAM_CHAT_ID', '12345')

    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = Exception('HTTP 400')

    with patch('requests.post', return_value=mock_response):
        import telegram_notify
        with pytest.raises(Exception, match='HTTP 400'):
            telegram_notify.send_message('test')


def test_send_message_missing_token_raises(monkeypatch):
    monkeypatch.delenv('TELEGRAM_BOT_TOKEN', raising=False)
    monkeypatch.delenv('TELEGRAM_CHAT_ID', raising=False)

    import telegram_notify
    with pytest.raises(KeyError):
        telegram_notify.send_message('test')
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_telegram_notify.py -v`

Expected: 3 failures with `ModuleNotFoundError: No module named 'telegram_notify'`

- [ ] **Step 3: Implement `telegram_notify.py`**

```python
import os
import sys
import requests


def send_message(text):
    token = os.environ['TELEGRAM_BOT_TOKEN']
    chat_id = os.environ['TELEGRAM_CHAT_ID']
    url = f'https://api.telegram.org/bot{token}/sendMessage'
    response = requests.post(
        url,
        json={'chat_id': chat_id, 'text': text, 'parse_mode': 'Markdown'},
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


if __name__ == '__main__':
    message = sys.argv[1]
    send_message(message)
    print('sent')
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_telegram_notify.py -v`

Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add telegram_notify.py tests/
git commit -m "feat: telegram notifier with send_message and CLI"
```

---

## Task 4: Alpaca Client — Scaffold, Calendar & Portfolio

**Files:**
- Create: `alpaca_client.py` (partial — calendar + portfolio only)
- Modify: `tests/test_alpaca_client.py` (new file)

- [ ] **Step 1: Write failing tests for `get_calendar` and `get_portfolio`**

Create `tests/test_alpaca_client.py`:

```python
import pytest
from unittest.mock import patch, MagicMock
import json


@pytest.fixture(autouse=True)
def env(monkeypatch):
    monkeypatch.setenv('ALPACA_API_KEY', 'test-key')
    monkeypatch.setenv('ALPACA_SECRET_KEY', 'test-secret')
    monkeypatch.setenv('ALPACA_BASE_URL', 'https://paper-api.alpaca.markets')


# --- get_calendar ---

def test_get_calendar_returns_true_on_trading_day():
    mock_client = MagicMock()
    mock_client.get_calendar.return_value = [MagicMock()]

    with patch('alpaca_client._get_trading_client', return_value=mock_client):
        import alpaca_client
        assert alpaca_client.get_calendar('2024-01-02') is True


def test_get_calendar_returns_false_on_holiday():
    mock_client = MagicMock()
    mock_client.get_calendar.return_value = []

    with patch('alpaca_client._get_trading_client', return_value=mock_client):
        import alpaca_client
        assert alpaca_client.get_calendar('2024-01-01') is False


# --- get_portfolio ---

def test_get_portfolio_returns_account_and_positions():
    mock_client = MagicMock()

    mock_account = MagicMock()
    mock_account.cash = '10000.00'
    mock_account.buying_power = '20000.00'
    mock_account.portfolio_value = '12000.00'
    mock_client.get_account.return_value = mock_account

    mock_pos = MagicMock()
    mock_pos.symbol = 'AAPL'
    mock_pos.qty = '10'
    mock_pos.avg_entry_price = '150.00'
    mock_pos.market_value = '1600.00'
    mock_pos.unrealized_pl = '100.00'
    mock_pos.unrealized_plpc = '0.067'
    mock_pos.current_price = '160.00'
    mock_client.get_all_positions.return_value = [mock_pos]

    with patch('alpaca_client._get_trading_client', return_value=mock_client):
        import alpaca_client
        result = alpaca_client.get_portfolio()

    assert result['cash'] == 10000.0
    assert result['buying_power'] == 20000.0
    assert result['portfolio_value'] == 12000.0
    assert len(result['positions']) == 1
    assert result['positions'][0]['symbol'] == 'AAPL'
    assert result['positions'][0]['qty'] == 10.0
    assert result['positions'][0]['current_price'] == 160.0


def test_get_portfolio_empty_positions():
    mock_client = MagicMock()
    mock_account = MagicMock()
    mock_account.cash = '5000.00'
    mock_account.buying_power = '5000.00'
    mock_account.portfolio_value = '5000.00'
    mock_client.get_account.return_value = mock_account
    mock_client.get_all_positions.return_value = []

    with patch('alpaca_client._get_trading_client', return_value=mock_client):
        import alpaca_client
        result = alpaca_client.get_portfolio()

    assert result['positions'] == []
    assert result['cash'] == 5000.0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_alpaca_client.py::test_get_calendar_returns_true_on_trading_day tests/test_alpaca_client.py::test_get_portfolio_returns_account_and_positions -v`

Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement scaffold, `_get_trading_client`, `get_calendar`, and `get_portfolio` in `alpaca_client.py`**

```python
import os
import json
import time
import requests
from datetime import datetime, timedelta, timezone

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import (
    MarketOrderRequest,
    TrailingStopOrderRequest,
    GetCalendarRequest,
)
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest, StockLatestBarRequest
from alpaca.data.timeframe import TimeFrame

_CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')


def _load_config():
    with open(_CONFIG_PATH) as f:
        return json.load(f)


def _get_trading_client():
    api_key = os.environ['ALPACA_API_KEY']
    secret_key = os.environ['ALPACA_SECRET_KEY']
    base_url = os.environ.get('ALPACA_BASE_URL', 'https://paper-api.alpaca.markets')
    paper = 'paper' in base_url
    return TradingClient(api_key, secret_key, paper=paper)


def _get_data_client():
    api_key = os.environ['ALPACA_API_KEY']
    secret_key = os.environ['ALPACA_SECRET_KEY']
    return StockHistoricalDataClient(api_key, secret_key)


def _retry_once(func, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except Exception:
        time.sleep(30)
        return func(*args, **kwargs)


def get_calendar(date_str=None):
    if date_str is None:
        date_str = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    target = datetime.strptime(date_str, '%Y-%m-%d').date()
    client = _get_trading_client()
    req = GetCalendarRequest(start=target, end=target)
    calendar = client.get_calendar(req)
    return len(calendar) > 0


def get_portfolio():
    client = _get_trading_client()
    account = _retry_once(client.get_account)
    positions = _retry_once(client.get_all_positions)

    positions_list = []
    for p in positions:
        positions_list.append({
            'symbol': p.symbol,
            'qty': float(p.qty),
            'avg_entry_price': float(p.avg_entry_price),
            'market_value': float(p.market_value),
            'unrealized_pl': float(p.unrealized_pl),
            'unrealized_plpc': float(p.unrealized_plpc),
            'current_price': float(p.current_price),
        })

    return {
        'cash': float(account.cash),
        'buying_power': float(account.buying_power),
        'portfolio_value': float(account.portfolio_value),
        'positions': positions_list,
    }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_alpaca_client.py -k "calendar or portfolio" -v`

Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add alpaca_client.py tests/test_alpaca_client.py
git commit -m "feat: alpaca client scaffold with calendar check and portfolio snapshot"
```

---

## Task 5: Alpaca Client — Market Data & News

**Files:**
- Modify: `alpaca_client.py` (add `get_market_data`, `get_news`)
- Modify: `tests/test_alpaca_client.py` (add tests)

- [ ] **Step 1: Add failing tests for `get_market_data` and `get_news`**

Append to `tests/test_alpaca_client.py`:

```python
# --- get_market_data ---

def test_get_market_data_returns_ohlcv_per_symbol():
    mock_bar = MagicMock()
    mock_bar.timestamp = MagicMock()
    mock_bar.timestamp.strftime.return_value = '2024-01-02'
    mock_bar.open = 150.0
    mock_bar.high = 155.0
    mock_bar.low = 149.0
    mock_bar.close = 153.0
    mock_bar.volume = 1000000

    mock_bars_data = {'AAPL': [mock_bar]}
    mock_data_client = MagicMock()
    mock_data_client.get_stock_bars.return_value = mock_bars_data

    with patch('alpaca_client._get_data_client', return_value=mock_data_client):
        import alpaca_client
        result = alpaca_client.get_market_data(['AAPL'])

    assert 'AAPL' in result
    assert len(result['AAPL']) == 1
    assert result['AAPL'][0]['close'] == 153.0
    assert result['AAPL'][0]['volume'] == 1000000


def test_get_market_data_returns_empty_for_missing_symbol():
    mock_data_client = MagicMock()
    mock_data_client.get_stock_bars.return_value = {}

    with patch('alpaca_client._get_data_client', return_value=mock_data_client):
        import alpaca_client
        result = alpaca_client.get_market_data(['UNKNOWN'])

    assert result['UNKNOWN'] == []


# --- get_news ---

def test_get_news_returns_headlines():
    api_response = {
        'news': [
            {
                'headline': 'AAPL hits record high',
                'summary': 'Apple stock surged on strong earnings.',
                'symbols': ['AAPL'],
                'created_at': '2024-01-02T10:00:00Z',
                'url': 'https://example.com/news/1',
            }
        ]
    }
    mock_response = MagicMock()
    mock_response.json.return_value = api_response
    mock_response.raise_for_status = MagicMock()

    with patch('requests.get', return_value=mock_response):
        import alpaca_client
        result = alpaca_client.get_news(['AAPL'], limit=5)

    assert len(result) == 1
    assert result[0]['headline'] == 'AAPL hits record high'
    assert result[0]['symbols'] == ['AAPL']


def test_get_news_no_symbols_fetches_general_news():
    api_response = {'news': []}
    mock_response = MagicMock()
    mock_response.json.return_value = api_response
    mock_response.raise_for_status = MagicMock()

    with patch('requests.get', return_value=mock_response) as mock_get:
        import alpaca_client
        alpaca_client.get_news(symbols=None, limit=10)

        call_kwargs = mock_get.call_args
        assert 'symbols' not in call_kwargs.kwargs.get('params', {})
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_alpaca_client.py -k "market_data or news" -v`

Expected: 4 failures with `AttributeError: module 'alpaca_client' has no attribute 'get_market_data'`

- [ ] **Step 3: Implement `get_market_data` and `get_news` in `alpaca_client.py`**

Append to `alpaca_client.py` (after `get_portfolio`):

```python
def get_market_data(symbols, days=5):
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days + 7)

    client = _get_data_client()
    req = StockBarsRequest(
        symbol_or_symbols=symbols,
        timeframe=TimeFrame.Day,
        start=start,
        end=end,
    )
    bars_data = _retry_once(client.get_stock_bars, req)

    result = {}
    for symbol in symbols:
        raw = list(bars_data[symbol]) if symbol in bars_data else []
        result[symbol] = [
            {
                'date': bar.timestamp.strftime('%Y-%m-%d'),
                'open': float(bar.open),
                'high': float(bar.high),
                'low': float(bar.low),
                'close': float(bar.close),
                'volume': int(bar.volume),
            }
            for bar in raw[-days:]
        ]
    return result


def get_news(symbols=None, limit=10):
    api_key = os.environ['ALPACA_API_KEY']
    secret_key = os.environ['ALPACA_SECRET_KEY']

    params = {'limit': limit}
    if symbols:
        params['symbols'] = ','.join(symbols)

    resp = _retry_once(
        requests.get,
        'https://data.alpaca.markets/v1beta1/news',
        headers={
            'APCA-API-KEY-ID': api_key,
            'APCA-API-SECRET-KEY': secret_key,
        },
        params=params,
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()

    return [
        {
            'headline': a['headline'],
            'summary': a.get('summary', ''),
            'symbols': a.get('symbols', []),
            'created_at': a['created_at'],
            'url': a.get('url', ''),
        }
        for a in data.get('news', [])
    ]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_alpaca_client.py -k "market_data or news" -v`

Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add alpaca_client.py tests/test_alpaca_client.py
git commit -m "feat: alpaca client market data and news feed"
```

---

## Task 6: Alpaca Client — Order Execution & CLI

**Files:**
- Modify: `alpaca_client.py` (add `place_order`, `close_position`, CLI entry point)
- Modify: `tests/test_alpaca_client.py` (add tests)

- [ ] **Step 1: Add failing tests for `place_order` and `close_position`**

Append to `tests/test_alpaca_client.py`:

```python
# --- place_order ---

def test_place_order_raises_when_halted(tmp_path, monkeypatch):
    config = {'halt': True, 'max_position_pct': 0.10, 'stop_loss_pct': 0.05, 'max_open_positions': 5}
    (tmp_path / 'config.json').write_text(json.dumps(config))

    with patch('alpaca_client._CONFIG_PATH', str(tmp_path / 'config.json')):
        import alpaca_client
        with pytest.raises(RuntimeError, match='Kill switch active'):
            alpaca_client.place_order('AAPL', 5, 'buy', 0.05)


def test_place_order_buy_places_market_and_trailing_stop(tmp_path):
    config = {'halt': False, 'max_position_pct': 0.10, 'stop_loss_pct': 0.05, 'max_open_positions': 5}
    (tmp_path / 'config.json').write_text(json.dumps(config))

    mock_client = MagicMock()
    mock_order = MagicMock()
    mock_order.id = 'order-123'
    mock_order.status = 'accepted'
    mock_stop = MagicMock()
    mock_stop.id = 'stop-456'
    mock_client.submit_order.side_effect = [mock_order, mock_stop]

    with patch('alpaca_client._CONFIG_PATH', str(tmp_path / 'config.json')), \
         patch('alpaca_client._get_trading_client', return_value=mock_client):
        import alpaca_client
        result = alpaca_client.place_order('AAPL', 5, 'buy', 0.05)

    assert result['symbol'] == 'AAPL'
    assert result['qty'] == 5.0
    assert result['side'] == 'buy'
    assert result['order_id'] == 'order-123'
    assert result['stop_order_id'] == 'stop-456'
    assert mock_client.submit_order.call_count == 2


def test_place_order_sell_does_not_place_stop(tmp_path):
    config = {'halt': False, 'max_position_pct': 0.10, 'stop_loss_pct': 0.05, 'max_open_positions': 5}
    (tmp_path / 'config.json').write_text(json.dumps(config))

    mock_client = MagicMock()
    mock_order = MagicMock()
    mock_order.id = 'sell-789'
    mock_order.status = 'accepted'
    mock_client.submit_order.return_value = mock_order

    with patch('alpaca_client._CONFIG_PATH', str(tmp_path / 'config.json')), \
         patch('alpaca_client._get_trading_client', return_value=mock_client):
        import alpaca_client
        result = alpaca_client.place_order('AAPL', 5, 'sell', 0.05)

    assert result['side'] == 'sell'
    assert result['stop_order_id'] is None
    assert mock_client.submit_order.call_count == 1


# --- close_position ---

def test_close_position_returns_order_details():
    mock_client = MagicMock()
    mock_result = MagicMock()
    mock_result.id = 'close-999'
    mock_result.status = 'accepted'
    mock_client.close_position.return_value = mock_result

    with patch('alpaca_client._get_trading_client', return_value=mock_client):
        import alpaca_client
        result = alpaca_client.close_position('TSLA')

    assert result['symbol'] == 'TSLA'
    assert result['order_id'] == 'close-999'
    mock_client.close_position.assert_called_once_with('TSLA')
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_alpaca_client.py -k "place_order or close_position" -v`

Expected: 4 failures with `AttributeError`

- [ ] **Step 3: Implement `place_order` and `close_position` in `alpaca_client.py`**

Append to `alpaca_client.py` (after `get_news`):

```python
def place_order(symbol, qty, side, stop_loss_pct):
    config = _load_config()
    if config.get('halt'):
        raise RuntimeError('Kill switch active — trading halted')

    client = _get_trading_client()
    order_side = OrderSide.BUY if side == 'buy' else OrderSide.SELL

    market_req = MarketOrderRequest(
        symbol=symbol,
        qty=qty,
        side=order_side,
        time_in_force=TimeInForce.DAY,
    )
    order = _retry_once(client.submit_order, market_req)

    stop_order = None
    if side == 'buy':
        stop_req = TrailingStopOrderRequest(
            symbol=symbol,
            qty=qty,
            side=OrderSide.SELL,
            time_in_force=TimeInForce.GTC,
            trail_percent=round(stop_loss_pct * 100, 2),
        )
        stop_order = _retry_once(client.submit_order, stop_req)

    return {
        'order_id': str(order.id),
        'symbol': symbol,
        'qty': float(qty),
        'side': side,
        'status': str(order.status),
        'stop_order_id': str(stop_order.id) if stop_order else None,
    }


def close_position(symbol):
    client = _get_trading_client()
    result = _retry_once(client.close_position, symbol)
    return {
        'symbol': symbol,
        'order_id': str(result.id),
        'status': str(result.status),
    }
```

- [ ] **Step 4: Add CLI entry point to `alpaca_client.py`**

Append to the end of `alpaca_client.py`:

```python
if __name__ == '__main__':
    import sys

    cmd = sys.argv[1]
    args = sys.argv[2:]

    dispatch = {
        'check_calendar': lambda: get_calendar(args[0] if args else None),
        'get_portfolio': lambda: get_portfolio(),
        'get_market_data': lambda: get_market_data(args[0].split(',')),
        'get_news': lambda: get_news(
            args[0].split(',') if args and args[0] else None,
            int(args[1]) if len(args) > 1 else 10,
        ),
        'place_order': lambda: place_order(args[0], int(args[1]), args[2], float(args[3])),
        'close_position': lambda: close_position(args[0]),
    }

    result = dispatch[cmd]()
    print(json.dumps(result))
```

- [ ] **Step 5: Run all tests to verify everything passes**

Run: `pytest tests/ -v`

Expected: All tests pass (no failures, no errors)

- [ ] **Step 6: Commit**

```bash
git add alpaca_client.py tests/test_alpaca_client.py
git commit -m "feat: alpaca client order execution, close position, and CLI entry point"
```

---

## Task 7: Claude Code Routine Definition

**Files:**
- Create: `.claude/routines/trading-routine.md`

- [ ] **Step 1: Create the `.claude/routines/` directory and write the routine**

Create `.claude/routines/trading-routine.md`:

```markdown
---
description: Autonomous US equities trading agent — Mon–Fri 7AM ET
schedule: "0 12 * * 1-5"
env:
  - ALPACA_API_KEY
  - ALPACA_SECRET_KEY
  - ALPACA_BASE_URL
  - TELEGRAM_BOT_TOKEN
  - TELEGRAM_CHAT_ID
---

# Alpaca AI Trading Routine

You are an autonomous trading agent for US equities. You run every weekday at 7:00 AM ET (schedule is set as 12:00 UTC; adjust for DST if needed). Your goal is to research market conditions, make intelligent risk-managed trading decisions, execute them via Alpaca, maintain full memory across sessions, and notify the user via Telegram.

**Capital:** ~US$3,700 (SG$5,000). Treat it seriously.
**Mode:** Paper trading until `config.json` sets `paper_trading: false`.
**Working directory:** The project root (where `alpaca_client.py` lives).

## Tools Available

Run these from the project root:

```
python alpaca_client.py check_calendar [YYYY-MM-DD]
python alpaca_client.py get_portfolio
python alpaca_client.py get_market_data SYMBOL1,SYMBOL2
python alpaca_client.py get_news [SYMBOL1,SYMBOL2] [limit]
python alpaca_client.py place_order SYMBOL QTY buy|sell STOP_PCT
python alpaca_client.py close_position SYMBOL
python telegram_notify.py "message text"
```

All scripts print JSON to stdout. Parse responses to inform your decisions.

---

## Step 1: Halt & Market Gate Check

Read `config.json`. If `halt` is `true`:
- Run: `python telegram_notify.py "⚠️ Trading halted — kill switch is active."`
- Stop immediately.

Run: `python alpaca_client.py check_calendar`
- If `false`: today is a holiday or weekend. Exit silently with no Telegram message.
- If `true`: continue to Step 2.

---

## Step 2: Load Agent Memory

Read these files:
- `memory/positions.json` — your open positions with entry data and thesis
- `memory/session_log.jsonl` — past session decisions (focus on the last 5 lines)
- `memory/performance.json` — running P&L and trade history
- `memory/market_context.md` — your notes from the last session

Synthesise into a mental model before proceeding:
- What positions do you hold and why?
- Is each thesis still valid based on what you remember?
- What was the market doing last session?
- What were you watching or expecting?

---

## Step 3: Live Portfolio Snapshot

Run: `python alpaca_client.py get_portfolio`

Compare live positions to `memory/positions.json`:
- Position in memory but NOT live → stop-loss triggered overnight. Mark it as closed and note the exit in your working state.
- Position live but NOT in memory → unexpected. Log it in your session notes, do NOT trade it without understanding it first.

Note: cash, buying_power, portfolio_value. You will need these for position sizing.

---

## Step 4: Market Research

Gather intelligence before making any decisions.

**Macro (use web search):**
- Search: "VIX index today [today's date]" — note the level
- Search: "SPY QQQ pre-market [today's date]" — note direction and magnitude
- Search: "US stock market news [today's date]" — key overnight stories

**Sector (use web search):**
- Search: "sector ETF performance today [today's date]" — identify hot/cold sectors

**News feed (use Alpaca):**
- Run: `python alpaca_client.py get_news "" 20` — top 20 general market headlines
- For each open position [SYMBOL]: `python alpaca_client.py get_news SYMBOL 5`

**Open position price data:**
- If you hold any positions: `python alpaca_client.py get_market_data SYMBOL1,SYMBOL2`
- Review the last 5 days of OHLCV data for each. Is price moving as the thesis expected?

Synthesise into a market assessment:
1. Overall sentiment: bullish / bearish / neutral / mixed
2. Key catalysts or risks today
3. Which sectors are leading or lagging
4. Any news that specifically affects your current positions

---

## Step 5: Analysis & Trading Decisions

Reason carefully over all context: memory + live portfolio + research. Think through your decisions explicitly.

**Defensive mode check:** If VIX > 40 OR any major index is down >2% pre-market:
- Enter defensive mode: no new positions
- Only manage existing ones (consider tightening or exiting)
- Explain your defensive stance clearly in the session log

**Trading style for today** (choose one, explain why):
- **Swing entry** — stocks at key support or breaking resistance with trend momentum
- **Short-term momentum** — news-driven movers with volume confirmation
- **News-driven** — specific catalysts (earnings, analyst upgrades, sector news)
- **Defensive/hold** — preserve capital, no new entries

**Review each open position:**
For every position in `memory/positions.json`, decide:
- Is the original thesis still valid?
- Has price moved as expected since entry?
- Any new risk (news, technical breakdown, sector rotation)?
- Decision: hold / add / trim / exit — with explicit rationale

**New position candidates:**
Identify 1–3 stocks that fit today's trading style. For each, define:
- Ticker and current price
- Thesis (why this, why now)
- Entry rationale (what technical or fundamental signal)
- Expected hold period (days)
- Risk: what would invalidate the thesis

**Position sizing (apply BEFORE deciding to trade):**
```
max_dollars = portfolio_value × max_position_pct   (from config.json, default 0.10)
qty = floor(max_dollars / current_price)
```
- Never exceed max_position_pct in a single stock
- Count current open positions. If already at max_open_positions, no new entries.
- Round qty DOWN to whole shares always

**Conservative bias:** When uncertain, do nothing. Capital preservation > making trades.

---

## Step 6: Execute Trades

For each confirmed trade decision:

**To open a new position (buy):**
```
python alpaca_client.py place_order SYMBOL QTY buy STOP_LOSS_PCT
```
Example: `python alpaca_client.py place_order AAPL 5 buy 0.05`

This places a market order AND a trailing stop-loss automatically.

**To exit a position (full close):**
```
python alpaca_client.py close_position SYMBOL
```

**On order failure:** If the script returns an error or non-accepted status, log it and move on. Do NOT retry automatically. Include the failure in the Telegram summary.

Record all order IDs from the responses — you need them for the memory update.

---

## Step 7: Update Memory

After all trades are executed, update all memory files.

**`memory/positions.json`** — rewrite the full array to reflect current state:
- Add new positions opened this session (include order_id, entry_price use approximate market price, entry_date as today, thesis)
- Remove positions that were closed (stop-loss triggered or explicit exit)
- Keep unchanged positions as-is

Schema for each entry:
```json
{
  "symbol": "AAPL",
  "qty": 5,
  "entry_price": 185.50,
  "entry_date": "2026-05-08",
  "thesis": "Breaking out above 200-day MA on high volume, strong sector momentum",
  "stop_loss_pct": 0.05,
  "order_id": "abc-123"
}
```

**`memory/session_log.jsonl`** — append ONE new line (do not rewrite the file):
```json
{"date": "2026-05-08", "sentiment": "bullish", "style": "swing", "trades": [{"symbol": "AAPL", "side": "buy", "qty": 5, "price": 185.50, "rationale": "200-day MA breakout on volume"}], "no_trade_reason": null, "notes": "VIX 18, tech leading, entered AAPL breakout position"}
```
If no trades: set `"trades": []` and fill `"no_trade_reason"` with a concise explanation.

**`memory/performance.json`** — update for any CLOSED trades this session:
- Add each closed trade to `trade_history` with entry/exit price and realized P&L
- Recalculate `total_realized_pl` (sum of all realized_pl in trade_history)
- Update `total_trades`, `winning_trades` (pl > 0), `losing_trades` (pl <= 0)

**`memory/market_context.md`** — overwrite with today's assessment:
```markdown
# Market Context — [date]

**Sentiment:** [bullish/bearish/neutral/mixed]
**VIX:** [level]
**Key indices:** SPY [+/-X%], QQQ [+/-X%]
**Style used today:** [swing/momentum/news-driven/defensive]

**Key observations:**
- [observation 1]
- [observation 2]
- [observation 3]

**Watching next session:**
- [stock or theme 1]
- [stock or theme 2]
```

---

## Step 8: Telegram Daily Summary

Send the daily summary. Use plain text (not Markdown) for any dynamic content containing prices or symbols to avoid parse errors.

Format:
```
📊 Trading Summary — [date]

Market: [Bullish/Bearish/Neutral/Mixed] | VIX: [X]
Style: [Swing/Momentum/News-driven/Defensive]

Trades Executed:
• BUY [SYMBOL] x[QTY] — [reason in 1 line]
• SOLD [SYMBOL] — [reason in 1 line]
(or: No trades today — [reason])

Portfolio:
• Cash: $[X]
• Open positions: [SYMBOL1, SYMBOL2, ...]
• Total value: $[X]
• Unrealised P&L: $[X]

Notes: [1-2 sentences on key observations or what to watch]
```

Run:
```
python telegram_notify.py "[full message]"
```

---

## Step 9: Friday Weekly Review (Fridays only)

Check the current day. If today is Friday, run this after Step 8.

**Read:**
- `memory/session_log.jsonl` — extract all entries where `date` falls in the current Mon–Fri week
- `memory/performance.json` — current P&L state

**Calculate:**
- Weekly realised P&L: sum of `realized_pl` from trades closed this week (from `trade_history` filtered by `exit_date`)
- Trades this week: count entries in session_log with this week's dates, sum their `trades` arrays
- Win rate: winning_trades / total_trades for the week
- Best trade: highest realized_pl this week
- Worst trade: lowest realized_pl this week

**Assess honestly:**
- Is the overall strategy working? Are wins outpacing losses?
- What patterns do the losing trades share?
- What worked well?
- What should be adjusted for next week?

**Send separate Telegram message:**
```
📈 Weekly Review — Week of [Monday date]

Performance:
• Realised P&L: $[X] ([+/-X%] of starting value)
• Trades: [N] total | [W] wins | [L] losses
• Win rate: [X%]
• Best: [SYMBOL] +$[X]
• Worst: [SYMBOL] -$[X]

Portfolio Value: $[X]

Assessment: [2-3 sentences — honest evaluation of what worked and what didn't]

Next Week: [1-2 sentences on approach adjustments or themes to watch]
```

---

## Critical Rules (Never Break These)

1. **Always check `halt` flag first** — if true, stop immediately
2. **Never exceed position size limits** — calculate before placing any order
3. **Stop-loss on every new buy** — `place_order` handles this, never bypass it
4. **Never trade on a non-trading day** — always check the calendar first
5. **When uncertain, do nothing** — no trade is always a valid decision
6. **Write thorough session notes** — future-you depends on clear reasoning in the log
7. **Paper mode first** — `paper_trading: true` until explicitly changed in config.json
```

- [ ] **Step 2: Commit**

```bash
git add .claude/routines/trading-routine.md
git commit -m "feat: Claude Code routine definition with full trading agent instructions"
```

- [ ] **Step 3: Commit design spec and plan docs**

```bash
git add docs/
git commit -m "docs: add design spec and implementation plan"
```

---

## Setup Checklist (Post-Implementation)

Before running the routine for the first time:

1. **Alpaca account:** Sign up at alpaca.markets, generate paper trading API keys
2. **Telegram bot:** Message @BotFather on Telegram, create a new bot, save the token. Start a chat with the bot and get your chat ID from `https://api.telegram.org/bot<TOKEN>/getUpdates`
3. **Register the routine:** Run `/schedule` in Claude Code and configure:
   - Point to `.claude/routines/trading-routine.md`
   - Set environment variables: `ALPACA_API_KEY`, `ALPACA_SECRET_KEY`, `ALPACA_BASE_URL=https://paper-api.alpaca.markets`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`
4. **Test the scripts manually:**
   - `python alpaca_client.py check_calendar` — should return `true` or `false`
   - `python alpaca_client.py get_portfolio` — should return your paper account state
   - `python telegram_notify.py "Test message from trading bot"` — should appear in Telegram
5. **Verify paper trading mode:** Confirm `config.json` has `"paper_trading": true` and `"halt": false`
