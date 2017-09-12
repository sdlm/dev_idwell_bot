import datetime
import traceback

from pony.orm import db_session, commit, select

from models import User, Server


class ValidationError(Exception):
    pass


def get_server(**kwargs):
    # get alias
    server_alias = kwargs['args'][0] if 'args' in kwargs and len(kwargs['args']) > 0 else None
    if not server_alias:
        raise ValidationError('correct syntax is "/follow {server_alias}"')

    # validate alias
    with db_session:
        server_obj = Server.get(alias=server_alias)
        if server_obj is None:
            server_aliases = [obj.alias for obj in select(s for s in Server)]
            msg = 'choice server_alias from: {}'.format(', '.join(server_aliases))
            raise ValidationError(msg)

    return server_obj.id


def follow(bot, update, *_, **kwargs):
    try:
        server_obj_id = get_server(**kwargs)

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
                new_user.servers.add(server_obj)
                print('user created')
            else:
                user.servers.add(server_obj)
            commit()
            user_servers_str = ', '.join([s.alias for s in user.servers]) if user is not None else ''

        # send message
        msg = f'{user_name}({user_id}) follow {server_obj.alias}'
        bot.send_message(chat_id=update.message.chat_id, text=msg)

        msg = 'now you follow to: {servers}'.format(servers=user_servers_str)
        bot.send_message(chat_id=update.message.chat_id, text=msg)

    except ValidationError as e:
        bot.send_message(chat_id=update.message.chat_id, text=str(e))

    except:
        traceback.print_exc()


def forget(bot, update, *_, **kwargs):
    try:
        server_obj_id = get_server(**kwargs)

        with db_session:
            server_obj = Server.get(id=server_obj_id)

            # save user
            user_name = update.message.from_user.first_name
            user_id = update.message.from_user.id
            now = datetime.datetime.now()
            user = User.get(chat_id=user_id)
            if user is None:
                User(
                    name=user_name,
                    chat_id=user_id,
                    active=False,
                    created=now,
                    last_msg=now,
                )
                print('user created')
            else:
                user.servers.remove(server_obj)
            commit()

            user_servers_str = ', '.join([s.alias for s in user.servers]) if user is not None else ''

        # send message
        msg = f'{user_name}({user_id}) forget {server_obj.alias}'
        bot.send_message(chat_id=update.message.chat_id, text=msg)

        msg = 'now you follow to: {servers}'.format(servers=user_servers_str)
        bot.send_message(chat_id=update.message.chat_id, text=msg)

    except ValidationError as e:
        bot.send_message(chat_id=update.message.chat_id, text=str(e))

    except:
        traceback.print_exc()
