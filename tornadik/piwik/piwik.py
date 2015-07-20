import aiohttp
import asyncio

import furl
import urllib.parse

from tornadik.piwik import settings

class PiwikClient():

    def __init__(self):
        self.auth_token = settings.PIWIK_TOKEN
        self.site_id = settings.PIWIK_SITEID
        self.url = settings.PIWIK_URL
        self.period = 'day'
        self.date = 'last7'

    @property
    def base_single_request_url(self):
        """
        Base URL for making a single request to Piwik
        :return:
        """

        base_single_url = furl.furl(self.url)

        base_parameters = {
            'token_auth': self.auth_token,
            'module': 'API',
            'format': 'json',
            'idSite': self.site_id
        }

        return base_single_url.add(args=base_parameters).url

    @property
    def base_bulk_request_url(self):
        """
        Base URL for making a bulk request to Piwik.
        :return:
        """
        base_bulk_url = furl.furl(self.url)

        base_parameters = {
            'token_auth': self.auth_token,
            'module': 'API',
            'format': 'json',
            'method': 'API.getBulkRequest'
        }

        return base_bulk_url.add(args=base_parameters).url

    @asyncio.coroutine
    def bulk_node_data(self, **kwargs):
        """
        Async call to Piwik that returns data for current node as well as any children if they exist.
        :param kwargs: {
                    nodeID: GUID of the node calling statistics page
                    method: Optional, specifies specific type of data retrieved from Piwik, defaults to Visits
                    period: Optional, specifies what type of period Piwik archives data retrieved, defaults to 'day'
                    date: Optional, specifies range of data for Piwik to retrieve, defaults to 'last7' to get past week's
                }
        :return: Node data and any child data
        """

        node_id = kwargs.get('nodeID', None)
        method = kwargs.get('method', 'VisitsSummary.get')
        date = kwargs.get('date', 'last20')
        period = kwargs.get('period', 'day')

        request = yield from aiohttp.request('get', settings.API_HOST + 'nodes/{}/children'.format(node_id))
        response = yield from request.json()

        bulk_node_url = self.base_bulk_request_url

        parent_parameters = {
            'idSite': self.site_id,
            'method': method,
            'date': date,
            'period': period,
            'segment': 'pageUrl=@' + settings.HOST_URL + '{}/'.format(node_id)
        }

        url_parameters = furl.furl()
        url_parameters.set(args=parent_parameters)

        bulk_node_url += '&urls[0]={}'.format(urllib.parse.quote(url_parameters.querystr))

        for idx, child in enumerate(response['data']):
            child_parameters = {
                'idSite': self.site_id,
                'method': method,
                'date': date,
                'period': period,
                'segment': 'pageUrl=@' + settings.HOST_URL + '{}/'.format(child['id'])
            }

            url_parameters.set(args=child_parameters)
            bulk_node_url += '&urls[{}]={}'.format(idx+1, urllib.parse.quote(url_parameters.querystr))

        piwik_data = yield from self.make_request(bulk_node_url)

        node_data = {
            'node': {
                node_id: piwik_data[0]
            },
            'children': {}
        }

        dates = []
        for date in piwik_data[0]:
            dates.append(date)

        node_data['dates'] = dates

        if len(piwik_data) > 1:
            for idx, child in enumerate(response['data']):
                child_id = child['id']
                node_data['children'][child_id] = piwik_data[idx+1]
        else:
            node_data['children'] = []

        return node_data

    @asyncio.coroutine
    def bulk_node_file_data(self, **kwargs):
        """
        Async call to Piwik that returns specified data for passed GUID files.
        :param kwargs: {
                    files: List of file GUID's request will call data for. This function acts independent of NodeID
                           as file GUID's are passed through a 'GET' argument to Tornado from OSF javascript call.
                    method: Optional, specifies type of data retrieved from Piwik, defaults to VisitsSummary.get
                    period: Optional, specifies what type of period Piwik archives data retrieved, defaults to 'day'
                    date: Optional, specifies range of data for Piwik to retrieve, defaults to 'last7' to get past week's
                }
        :return: Formatted Piwik Bulk node file data
        """
        file_guids = kwargs.get('files', None)

        if file_guids is None:
            pass

        method = kwargs.get('method', 'VisitsSummary.get')
        date = kwargs.get('date', 'last20')
        period = kwargs.get('period', 'day')

        bulk_node_file_url = self.base_bulk_request_url
        url_parameters = furl.furl()

        for idx, id in enumerate(file_guids):
            file_parameters = {
                'idSite': self.site_id,
                'method': method,
                'period': period,
                'date': date,
                'segment': 'pageUrl=@' + settings.HOST_URL + '{}/'.format(id)
            }

            url_parameters.set(args=file_parameters)
            bulk_node_file_url += '&urls[{}]={}'.format(idx, urllib.parse.quote(str(url_parameters.query)))

        piwik_data = yield from self.make_request(bulk_node_file_url)

        file_data = {
            'files': {}
        }

        for idx, guid in enumerate(file_guids):
            file_data['files'][guid] = piwik_data[idx]

        return file_data

    @asyncio.coroutine
    def single_request_builder(self, **kwargs):

        single_url = furl.furl(self.base_single_request_url)

        node_id = kwargs.get('nodeID', None)
        method = kwargs.get('method', 'VisitsSummary.get')
        date = kwargs.get('date', 'last7')
        period = kwargs.get('period', 'day')

        parameters = {
            'method': method,
            'period': period,
            'date': date,
            'segment': 'pageUrl=@' + settings.HOST_URL + '{}/'.format(node_id)
        }

        single_url.add(args=parameters)

        return single_url.url

    @asyncio.coroutine
    def make_request(self, url):
        request = yield from aiohttp.request('get', url)
        response = yield from request.json()

        return response



if __name__ == '__main__':
    piwik = PiwikClient()
    asyncio.get_event_loop().run_until_complete(piwik.bulk_node_data(nodeID='f4gnt'))
