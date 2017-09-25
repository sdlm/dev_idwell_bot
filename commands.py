import datetime
import traceback

from pony.orm import db_session, commit, select

from models import User, Server


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
                new_user = User(
                    name=user_name,
                    chat_id=user_id,
                    active=False,
                    created=now,
                    last_msg=now,
                )
                if is_follow:
                    new_user.servers.add(server_obj)
                    print('user created')
                else:
                    print('you already not follow to this server')
            else:
                if is_follow:
                    user.servers.add(server_obj)
                    print(f'you will receive messages about {server_obj.alias} server')
                else:
                    user.servers.remove(server_obj)
                    print(f'you will not receive messages about {server_obj.alias} server')
            commit()
            user_servers_str = ', '.join([s.alias for s in user.servers]) if user is not None else ''

        cmd = 'follow' if is_follow else 'forget'

        # send message
        msg = f'{user_name}({user_id}) {cmd} {server_obj.alias}'
        bot.send_message(chat_id=update.message.chat_id, text=msg)

        msg = f'now you follow to: {user_servers_str}'
        bot.send_message(chat_id=update.message.chat_id, text=msg)

    except ValidationError as e:
        bot.send_message(chat_id=update.message.chat_id, text=str(e))

    except Exception:
        traceback.print_exc()


def follow(bot, update, *_, **kwargs):
    update_followed_list(bot, update, is_follow=True, **kwargs)


def forget(bot, update, *_, **kwargs):
    update_followed_list(bot, update, is_follow=False, **kwargs)


def start(bot, update, **_):
    with db_session:
        aliases = [s.alias for s in Server.select()]
    msg = f'commands:\n' \
          f'/follow {{server_alias}} - receive messages about server status\n' \
          f'/forget {{server_alias}} - suppress messages about this server\n' \
          f'where server_alias is one of {aliases}'
    bot.send_message(chat_id=update.message.chat_id, text=msg)
