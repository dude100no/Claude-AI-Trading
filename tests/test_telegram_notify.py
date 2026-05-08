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
