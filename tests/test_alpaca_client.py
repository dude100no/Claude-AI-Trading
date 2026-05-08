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
