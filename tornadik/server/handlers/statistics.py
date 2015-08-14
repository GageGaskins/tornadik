import tornado.web
import tornado.gen

from tornadik.piwik import piwik

import json

from tornadik.server.handlers import core

# Not used after StatistcsHandler implemented, save for possible use later
class NodeDataHandler(core.BaseHandler):

    @tornado.gen.coroutine
    def get(self, *args, **kwargs):

        piwik_client = piwik.PiwikClient()

        node_id = kwargs.get('nodeId', None)
        method = self.get_argument('method', None)
        period = self.get_argument('period', None)
        date = self.get_argument('date', None)

        if node_id is None:
            self.write("Error retrieving nodeId")
            return

        response = yield from piwik_client.bulk_node_data(nodeId=node_id, method=method, period=period, date=date)

        self.write(response)

# Not used after StatistcsHandler implemented, save for possible use later
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

class StatisticsHandler(core.BaseHandler):

    @tornado.gen.coroutine
    def get(self, *args, **kwargs):

        piwik_client = piwik.PiwikClient()

        node_id = self.get_argument('nodeId', None)
        method = self.get_argument('method', None)
        period = self.get_argument('period', None)
        date = self.get_argument('date', None)

        files = json.loads(self.get_argument('files', None))

        node_data = yield from piwik_client.bulk_node_data(nodeId=node_id, method=method, period=period, date=date)
        file_data = yield from piwik_client.bulk_node_file_data(files=files, method=method, period=period, date=date)

        self.write({'node_data': node_data, 'files_data': file_data})



