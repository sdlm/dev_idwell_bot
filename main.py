import traceback

import requests
from telegram.ext import Updater

TOKEN = '383519781:AAFBKloOU50Ofst3B1f7XKX24oEbRekujgc'
CHAT_ID = '-1001129781142'

servers = [
    {'alias': 'dev', 'url': 'dev.idwell.ru', 'status': None},
    {'alias': 'qa', 'url': 'qa.idwell.ru', 'status': None},
    {'alias': 'live', 'url': 'blackfriday.idwell.at', 'status': None},
]


def echo_server_status(bot, server: dict, status: bool):
    alias = server['alias']
    status_word = 'up' if status else 'down'
    text = f'{alias} is {status_word} right now'
    bot.send_message(chat_id=CHAT_ID, text=text)


def get_server_status(url):
    for _ in range(10):
        try:
            r = requests.get(f'http://{url}/api/system/system-status/', timeout=2)
        except:
            continue
        else:
            if r.status_code == requests.codes.ok:
                return True
    return False


def callback_minute(bot, job):
    try:
        for server in servers:
            print('{alias}: {status}'.format(alias=server['alias'], status=server['status']))
            is_server_alive = get_server_status(server['url'])
            if server['status'] is None:
                server['status'] = 0.5 if is_server_alive else -0.5
                continue
            status = float(server['status'])
            if is_server_alive:
                if status == -1:
                    server['status'] = -0.5
                elif status == -0.5:
                    echo_server_status(bot, server, is_server_alive)
                    server['status'] = 1
                else:
                    server['status'] = 1
            else:
                if status == 1:
                    server['status'] = 0.5
                elif status == 0.5:
                    echo_server_status(bot, server, is_server_alive)
                    server['status'] = -1
                else:
                    server['status'] = -1
    except:
        with open('/tmp/bot.log', 'w') as file:
            traceback.print_exc(file=file)


if __name__ == '__main__':
    updater = Updater(token=TOKEN)
    j = updater.job_queue
    # job_minute = Job(callback_minute, 60.0, name='test')
    # j.put(job_minute, next_t=0.0)
    # j.run_repeating(job_minute, 60.0)

    j.run_repeating(callback_minute, 5.0, first=0.0, context=None, name='test')
    updater.start_polling()
