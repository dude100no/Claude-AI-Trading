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
from alpaca.data.requests import StockBarsRequest
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
