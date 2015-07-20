import tornado.web
import tornado.gen

import aiohttp

from tornadik.piwik import piwik

import json

from tornadik.server.handlers import core

class NodeDataHandler(core.BaseHandler):

    @tornado.gen.coroutine
    def get(self, *args, **kwargs):

        piwik_client = piwik.PiwikClient()

        node_id = kwargs.get('nodeID', None)

        if node_id is None:
            self.write("Error retrieving nodeID")
            return

        response = yield from piwik_client.bulk_node_data(nodeID=node_id)

        self.write(response)

class NodeFileDataHandler(core.BaseHandler):

    @tornado.gen.coroutine
    def get(self, *args, **kwargs):

        piwik_client = piwik.PiwikClient()

        if self.request.arguments.get('files[]'):
            files_guids = [guid.decode("utf-8") for guid in self.request.arguments.get('files[]')]
            response = yield from piwik_client.bulk_node_file_data(files=files_guids)

            self.write(response)
            return

        self.write({'files': []})
