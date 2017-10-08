from time import sleep

from bamboo_api import BambooAPIClient


# noinspection SpellCheckingInspection
def test_bamboo_api():
    # https://developer.atlassian.com/bamboodev/rest-apis/bamboo-rest-resources
    # http -a arseniy.kuznetsov:smithclerk45 bamboo.idwell.ru/rest/api/latest/?os_authType=basic
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

    return f'Build {"complete successful." if successful else "failed !!"}\n' \
           f'result: {link}'
