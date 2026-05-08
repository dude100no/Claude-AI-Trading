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
