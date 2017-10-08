"""
This module contains the BambooAPIClient, used for communicating with the
Bamboo server web service API.
"""

import requests


class BambooAPIClient(object):
    """
    Adapter for Bamboo's web service API.
    """
    # Default host is local
    DEFAULT_HOST = 'http://localhost'
    DEFAULT_PORT = 8085

    # Endpoints
    BUILD_SERVICE = '/rest/api/latest/result'
    DEPLOY_SERVICE = '/rest/api/latest/deploy/project'
    ENVIRONMENT_SERVICE = '/rest/api/latest/deploy/environment/{env_id}/results'
    PLAN_SERVICE = '/rest/api/latest/plan'
    QUEUE_SERVICE = '/rest/api/latest/queue'
    RESULT_SERVICE = '/rest/api/latest/result'

    def __init__(self, host=None, port=None, user=None, password=None):
        """
        Set connection and auth information (if user+password were provided).
        """
        self._host = host or self.DEFAULT_HOST
        self._port = port or self.DEFAULT_PORT
        self._session = requests.Session()
        if user and password:
            self._session.auth = (user, password)

    def _get_response(self, url, params=None):
        """
        Make the call to the service with the given queryset and whatever params
        were set initially (auth).
        """
        res = self._session.get(url,  params=params or {}, headers={'Accept': 'application/json'})
        if res.status_code != 200:
            raise Exception(res.reason)
        return res

    def _post_response(self, url, params=None):
        """
        Post to the service with the given queryset and whatever params
        were set initially (auth).
        """
        res = self._session.post(url, params=params or {}, headers={'Accept': 'application/json'})
        if res.status_code != 200:
            raise Exception(res.reason)
        return res

    def _get_url(self, endpoint):
        """
        Get full url string for host, port and given endpoint.

        :param endpoint: path to service endpoint
        :return: full url to make request
        """
        return '{}:{}{}'.format(self._host, self._port, endpoint)

    def get_builds(self, plan_key=None, expand=False):
        """
        Get the builds in the Bamboo server.

        :param plan_key: str
        :param expand: boolean
        :return: Generator
        """
        # Build starting qs params
        qs = {'max-result': 25, 'start-index': 0}
        if expand:
            qs['expand'] = 'results.result'

        # Get url
        if plan_key:
            # All builds for one plan
            url = '{}/{}'.format(self._get_url(self.BUILD_SERVICE), plan_key)
        else:
            # Latest build for all plans
            url = self._get_url(self.BUILD_SERVICE)

        # Cycle through paged results
        size = 1
        while size:
            # Get page, update page and size
            response = self._get_response(url, qs).json()
            results = response['results']
            size = results['size']

            # Check if start index was reset
            # Note: see https://github.com/liocuevas/python-bamboo-api/issues/6
            if results['start-index'] < qs['start-index']:
                # Not the page we wanted, abort
                break

            # Yield results
            for r in results['result']:
                yield r

            # Update paging info
            # Note: do this here to keep it current with yields
            qs['start-index'] += size

    def get_deployments(self, project_key=None):
        """
        Returns the list of deployment projects set up on the Bamboo server.
        :param project_key: str
        :return: Generator
        """
        url = "{}/{}".format(self._get_url(self.DEPLOY_SERVICE), project_key or 'all')
        response = self._get_response(url).json()
        for r in response:
            yield r

    def get_environment_results(self, environment_id):
        """
        Returns the list of environment results.
        :param environment_id: int
        :return: Generator
        """
        # Build starting qs params
        qs = {'max-result': 25, 'start-index': 0}

        # Get url for results
        url = self._get_url(self.ENVIRONMENT_SERVICE.format(env_id=environment_id))

        # Cycle through paged results
        size = 1
        while qs['start-index'] < size:
            # Get page, update page size and yield results
            response = self._get_response(url, qs).json()
            size = response['size']
            for r in response['results']:
                yield r

            # Update paging info
            # Note: do this here to keep it current with yields
            qs['start-index'] += response['max-result']

    def get_plans(self, expand=False):
        """
        Return all the plans in a Bamboo server.

        :return: generator of plans
        """
        # Build starting qs params
        qs = {'max-result': 25, 'start-index': 0}
        if expand:
            qs['expand'] = 'plans.plan'

        # Get url for results
        url = self._get_url(self.PLAN_SERVICE)

        # Cycle through paged results
        size = 1
        while qs['start-index'] < size:
            # Get page, update page size and yield plans
            response = self._get_response(url, qs).json()
            plans = response['plans']
            size = plans['size']
            for r in plans['plan']:
                yield r

            # Update paging info
            # Note: do this here to keep it current with yields
            qs['start-index'] += plans['max-result']

    def queue_build(self, plan_key):
        """
        Queue a build for building
        :param plan_key: str
        """
        url = "{}/{}".format(self._get_url(self.QUEUE_SERVICE), plan_key)
        return self._post_response(url).json()

    def get_build_queue(self):
        """
        List all builds currently in the Queue
        """
        url = "{}".format(self._get_url(self.QUEUE_SERVICE))
        return self._get_response(url).json()

    def get_results(self, plan_key=None, build_number=None):
        """
        Returns a list of results for builds
        :param build_number: str
        :param plan_key: str
        :return: Generator
        """
        if build_number is not None and plan_key is not None:
            plan_key = plan_key + '-' + build_number
        url = "{}/{}".format(self._get_url(self.RESULT_SERVICE), plan_key or 'all')
        response = self._get_response(url).json()
        return response
