import traceback
from time import sleep

import requests
from telegram.ext import Updater

TOKEN = '383519781:AAFBKloOU50Ofst3B1f7XKX24oEbRekujgc'
CHANNEL_ID = '-1001129781142'
TIMEOUT = 15.0

servers = [
    {'alias': 'dev', 'url': 'dev.idwell.ru', 'prev_state': None},
    {'alias': 'qa', 'url': 'qa.idwell.ru', 'prev_state': None},
    {'alias': 'live', 'url': 'blackfriday.idwell.at', 'prev_state': None},
]


def echo_server_status(bot, server: dict, status: bool):
    alias = server['alias']
    status_word = 'up' if status else 'down'
    text = f'{alias} is {status_word} right now'
    bot.send_message(chat_id=CHANNEL_ID, text=text)


def get_server_status(url, tries=10):
    for _ in range(tries):
        try:
            r = requests.get(f'http://{url}/api/system/get_status/?telegram_bot=1', timeout=2)
        except:
            sleep(1)
            continue
        else:
            if r.status_code == requests.codes.ok:
                return True
    return False


def callback_minute(bot, job):
    try:
        for server in servers:
            print('{alias}: {status}'.format(alias=server['alias'], status=server['status']))
            tries = 10 if server['prev_state'] else 1
            is_server_alive = get_server_status(server['url'], tries=tries)
            if server['prev_state'] is None:
                server['prev_state'] = is_server_alive
                continue
            if is_server_alive != server['prev_state']:
                echo_server_status(bot, server, is_server_alive)
            server['prev_state'] = is_server_alive
    except:
        with open('/tmp/bot.log', 'w') as file:
            traceback.print_exc(file=file)


if __name__ == '__main__':
    updater = Updater(token=TOKEN)
    j = updater.job_queue
    j.run_repeating(callback_minute, TIMEOUT, first=0.0, context=None, name='test')
    updater.start_polling()
