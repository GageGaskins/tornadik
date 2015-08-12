import tornado.web
import tornado.gen

import json
import aiohttp

from tornadik.piwik import piwik

import json

from tornadik.server.handlers import core

class NodeDataHandler(core.BaseHandler):

    @tornado.gen.coroutine
    def get(self, *args, **kwargs):

        piwik_client = piwik.PiwikClient()

        node_id = kwargs.get('nodeID', None)
        method = self.get_argument('method', None)
        period = self.get_argument('period', None)
        date = self.get_argument('date', None)

        if node_id is None:
            self.write("Error retrieving nodeID")
            return

        response = yield from piwik_client.bulk_node_data(nodeID=node_id, method=method, period=period, date=date)

        self.write(response)

class NodeFileDataHandler(core.BaseHandler):

    @tornado.gen.coroutine
    def get(self, *args, **kwargs):

        piwik_client = piwik.PiwikClient()

        method = self.get_argument('method', None)
        period = self.get_argument('period', None)
        date = self.get_argument('date', None)

        files = json.loads(self.get_argument('files', None))

        if files:
            response = yield from piwik_client.bulk_node_file_data(files=files, method=method, period=period, date=date)

            self.write(response)
            return

        self.write({'files': []})
