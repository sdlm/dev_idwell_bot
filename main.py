import traceback
from time import sleep

import requests
from pony.orm import commit, db_session
from telegram.error import BadRequest, Unauthorized
from telegram.ext import Updater, CommandHandler

from commands import follow, forget, start, build, status
from models import Server

TOKEN = '383519781:AAFBKloOU50Ofst3B1f7XKX24oEbRekujgc'
DEV_CHAT_ID = '-142032518'
TIMEOUT = 15.0
DEFAULT_SERVERS = {
    'dev': 'dev.idwell.ru',
    'qa': 'qa.idwell.ru',
    'live': 'blackfriday.idwell.at',
}

servers = [
    {'alias': 'dev', 'url': 'dev.dev.idwell.ru', 'prev_state': None},
    {'alias': 'qa', 'url': 'qa.qa.idwell.ru', 'prev_state': None},
    {'alias': 'live', 'url': 'blackfriday.idwell.at', 'prev_state': None},
]


def echo_server_status(bot, server: dict, status: bool):
    _alias = server['alias']
    status_word = 'up' if status else 'down'
    text = f'{_alias} is {status_word} right now'

    # send to dev chat
    # if _alias == 'dev':
    #     try:
    #         bot.send_message(chat_id=DEV_CHAT_ID, text=text)
    #     except (BadRequest, Unauthorized):
    #         traceback.print_exc()

    # send to followers
    with db_session:
        for user in Server.get(alias=_alias).users:
            print(f'send to {user.name}: {text}')
            try:
                bot.send_message(chat_id=user.chat_id, text=text)
            except (BadRequest, Unauthorized):
                traceback.print_exc()


def get_server_status(url, tries=10):
    for _ in range(tries):
        try:
            r = requests.get(f'https://{url}/api/system/get_status/?telegram_bot=1', timeout=2)
        except Exception:
            sleep(1)
            continue
        else:
            if r.status_code == requests.codes.ok:
                return True
    return False


def callback_minute(bot, *_):
    try:
        for server in servers:
            print('{alias}: {prev_state}'.format(alias=server['alias'], prev_state=server['prev_state']))
            tries = 10 if server['prev_state'] else 1
            is_server_alive = get_server_status(server['url'], tries=tries)
            if server['prev_state'] is None:
                server['prev_state'] = is_server_alive
                continue
            if is_server_alive != server['prev_state']:
                echo_server_status(bot, server, is_server_alive)
            server['prev_state'] = is_server_alive
    except Exception:
        with open('/tmp/bot.log', 'w') as file:
            traceback.print_exc(file=file)


if __name__ == '__main__':

    print('main: init db')
    # init db
    with db_session:
        for alias, url in DEFAULT_SERVERS.items():
            obj = Server.get(alias=alias)
            if obj is None:
                Server(alias=alias, url=url)
        commit()

    print('main: init bot')
    # init bot
    updater = Updater(token=TOKEN)
    j = updater.job_queue
    dispatcher = updater.dispatcher

    print('main: regular send messages')
    # regular send messages to channel dev_idwell_ru
    j.run_repeating(callback_minute, TIMEOUT, first=0.0, context=None, name='test')

    print('main: define commands')
    # define commands
    commands = {
        'follow': follow,
        'forget': forget,
        'status': status,
        'start': start,
        'build': build
    }
    for name, func in commands.items():
        handler = CommandHandler(name, func, pass_args=True)
        dispatcher.add_handler(handler)

    print('main: start_polling')
    updater.start_polling()
