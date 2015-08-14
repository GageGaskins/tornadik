import aiohttp
import asyncio

import tornado.web

import furl
import urllib.parse

import pprint

from tornadik.piwik import settings

class PiwikClient():

    def __init__(self):
        self.auth_token = settings.PIWIK_TOKEN
        self.site_id = settings.PIWIK_SITEID
        self.url = settings.PIWIK_URL
        self.period = settings.PIWIK_PERIOD
        self.date = settings.PIWIK_DATE

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
        Async call to Piwik that returns data for current node as well as any components if they exist.
        :param str **kwargs nodeId: Guid of the node
        :param str **kwargs method: Optional, specifies type of data retrieved from Piwik. Defaults to Visits
        :param str **kwargs period: Optional, specifies type of period Piwik archives data retrieved. Defaults to 'day'
        :param str **kwargs date: Optional, specifies range of data for Piwik to retrieve. Defaults to 'last30'

        :return: Node data and any child data
        """

        node_data = {
            'node': [],
            'children': []
        }

        node_id = kwargs['nodeId']
        method = kwargs['method'] or 'VisitsSummary.get'
        date = kwargs['date'] or self.date
        period = kwargs['period'] or self.period

        osf_api_request = yield from aiohttp.request('get', settings.API_HOST + 'nodes/{}/children?page[size]=999'.format(node_id))

        if osf_api_request.status != 200:
            raise tornado.web.HTTPError(osf_api_request.status, 'Error retrieving data from OSF')

        osf_api_response = yield from osf_api_request.json()

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

        for idx, child in enumerate(osf_api_response['data']):
            child_parameters = {
                'idSite': self.site_id,
                'method': method,
                'date': date,
                'period': period,
                'segment': 'pageUrl=@' + settings.HOST_URL + '{}/'.format(child['id'])
            }

            url_parameters.set(args=child_parameters)
            bulk_node_url += '&urls[{}]={}'.format(idx+1, urllib.parse.quote(url_parameters.querystr))

        piwik_data = yield from self.piwik_request(bulk_node_url)

        node_data = {
            'node': [
                {
                    'node_id': node_id,
                    'title': '',
                    'data': piwik_data[0]
                }
            ],
            'children': []
        }

        dates = []
        for date in piwik_data[0]:
            dates.append(date)

        node_data['dates'] = sorted(dates)

        if len(piwik_data) > 1:
            for idx, child in enumerate(osf_api_response['data']):
                child_node = {
                    'node_id': child['id'],
                    'title': child['title'],
                    'data': piwik_data[idx+1]
                }
                node_data['children'].append(child_node)
        else:
            node_data['children'] = []

        return node_data

    @asyncio.coroutine
    def bulk_node_file_data(self, **kwargs):
        """
        Async call to Piwik that returns specified data for passed GUID files.

        :param str **kwargs nodeId: Guid of the node
        :param str **kwargs method: Optional, specifies type of data retrieved from Piwik. Defaults to Visits
        :param str **kwargs period: Optional, specifies type of period Piwik archives data retrieved. Defaults to 'day'
        :param str **kwargs date: Optional, specifies range of data for Piwik to retrieve. Defaults to 'last30'

        :return: Formatted Piwik Bulk node file data
        """
        files = kwargs['files']

        if files is None:
            return {'files': []}

        method = kwargs['method'] or 'VisitsSummary.get'
        date = kwargs['date'] or self.date
        period = kwargs['period'] or self.period

        bulk_node_file_url = self.base_bulk_request_url
        url_parameters = furl.furl()

        for idx, id in enumerate(files.keys()):
            file_parameters = {
                'idSite': self.site_id,
                'method': method,
                'period': period,
                'date': date,
                'segment': 'pageUrl=@' + settings.HOST_URL + '{}/'.format(id)
            }

            url_parameters.set(args=file_parameters)
            bulk_node_file_url += '&urls[{}]={}'.format(idx, urllib.parse.quote(str(url_parameters.query)))

        piwik_data = yield from self.piwik_request(bulk_node_file_url)

        file_data = {
            'files': []
        }

        for idx, guid in enumerate(files.keys()):
            file_node = {
                'node_id': guid,
                'title': files[guid],
                'data': piwik_data[idx]
            }
            file_data['files'].append(file_node)

        return file_data

    @asyncio.coroutine
    def single_request_builder(self, **kwargs):

        single_url = furl.furl(self.base_single_request_url)

        node_id = kwargs.get('nodeId', None)
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
    def piwik_request(self, url):
        request = yield from aiohttp.request('get', url)

        if request.status != 200:
            raise tornado.web.HTTPError(request.status, 'Error retrieving Piwik Data')

        response = yield from request.json()

        return response
