from pony.orm import db_session

from models import Server, User
from utils import update_followed_list, setup_new_build


def start(bot, update, **_):
    with db_session:
        aliases = [s.alias for s in Server.select()]
    msg = f'commands:\n' \
          f'/follow {{server_alias}} - receive messages about server status\n' \
          f'/forget {{server_alias}} - suppress messages about this server\n' \
          f'where server_alias is one of {aliases}'
    bot.send_message(chat_id=update.message.chat_id, text=msg)


def follow(bot, update, *_, **kwargs):
    update_followed_list(bot, update, is_follow=True, **kwargs)


def forget(bot, update, *_, **kwargs):
    update_followed_list(bot, update, is_follow=False, **kwargs)


def status(bot, update, **_):
    with db_session:
        user = User.get(chat_id=update.message.from_user.id)
        user_servers_str = ', '.join([s.alias for s in user.servers]) if user is not None else ''
    msg = f'you do\'t follow any servers' if user_servers_str == '' else f'now you follow to: {user_servers_str}'
    bot.send_message(chat_id=update.message.chat_id, text=msg)


def build(bot, update, **_):
    msg = setup_new_build()
    bot.send_message(chat_id=update.message.chat_id, text=msg)
