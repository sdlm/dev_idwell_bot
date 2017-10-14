import datetime
import traceback
from time import sleep

from pony.orm import db_session, select, commit
from telegram.error import BadRequest

from bamboo_api import BambooAPIClient
from models import Server, User


class ValidationError(Exception):
    pass


def get_server(is_follow=True, **kwargs):
    # get alias
    server_alias = kwargs['args'][0] if 'args' in kwargs and len(kwargs['args']) > 0 else None
    if not server_alias:
        cmd = 'follow' if is_follow else 'forget'
        with db_session:
            aliases = [s.alias for s in Server.select()]
        msg = f'correct syntax is "/{cmd} {{server_alias}}"\n' \
              f'where server_alias is one of {aliases}'
        raise ValidationError(msg)

    # validate alias
    with db_session:
        server_obj = Server.get(alias=server_alias)
        if server_obj is None:
            # noinspection PyTypeChecker
            server_aliases = [obj.alias for obj in select(s for s in Server)]
            msg = 'choice server_alias from: {}'.format(', '.join(server_aliases))
            raise ValidationError(msg)

    return server_obj.id


def update_followed_list(bot, update, is_follow=True, *_, **kwargs):
    try:
        server_obj_id = get_server(is_follow=is_follow, **kwargs)

        with db_session:
            server_obj = Server.get(id=server_obj_id)

            # save user
            user_name = update.message.from_user.first_name
            user_id = update.message.from_user.id
            now = datetime.datetime.now()
            user = User.get(chat_id=user_id)
            if user is None:
                user = User(
                    name=user_name,
                    chat_id=user_id,
                    active=False,
                    created=now,
                    last_msg=now,
                )
                if is_follow:
                    user.servers.add(server_obj)
            else:
                if is_follow:
                    user.servers.add(server_obj)
                else:
                    user.servers.remove(server_obj)
            commit()
            # user_servers_str = ', '.join([s.alias for s in user.servers]) if user is not None else ''

        cmd = 'will' if is_follow else 'will not'

        # send message
        msg = f'you {cmd} receive messages about {server_obj.alias} server status'
        try:
            bot.send_message(chat_id=update.message.chat_id, text=msg)
        except BadRequest:
            traceback.print_exc()

        # send status message
        # msg = f'you do\'t follow any servers' if user_servers_str == '' else f'now you follow to: {user_servers_str}'
        # bot.send_message(chat_id=update.message.chat_id, text=msg)

    except ValidationError as e:
        try:
            bot.send_message(chat_id=update.message.chat_id, text=str(e))
        except BadRequest:
            traceback.print_exc()

    except Exception:
        traceback.print_exc()


# noinspection SpellCheckingInspection
def setup_new_build():
    # https://developer.atlassian.com/bamboodev/rest-apis/bamboo-rest-resources
    # http -a arseniy.kuznetsov:smithclerk45 bamboo.idwell.ru/rest/api/latest/?os_authType=basic
    try:
        bamboo = BambooAPIClient(
            host='http://bamboo.idwell.ru',
            port='80',
            user='arseniy.kuznetsov',
            password='smithclerk45'
        )
        plan_key = 'ID-FULL'

        # run new build
        resp = bamboo.queue_build(plan_key=plan_key)
        build_number = str(resp['buildNumber'])

        successful = False
        link = None
        for _ in range(100500):
            resp = bamboo.get_results(plan_key=plan_key, build_number=build_number)
            print(resp)
            finished = resp['finished']
            successful = resp['successful']
            link = resp['link']['href']
            if finished:
                break
            sleep(15)

    except Exception:
        return traceback.format_exc()

    else:
        human_link = link.replace('rest/api/latest/result', 'browse')
        return f'Build {"complete successful." if successful else "failed !!"}\n' \
               f'result: {human_link}'
