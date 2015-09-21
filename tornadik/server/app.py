import asyncio

import aiohttp

import tornado.web
import tornado.httpserver
import tornado.gen
import tornado.platform.asyncio
import tornado.log

from tornadik.server.handlers import statistics

def make_app():
    app = tornado.web.Application(
        [
            (r'/(?P<nodeId>\w*)/nodeData', statistics.NodeDataHandler),
            (r'/fileData', statistics.NodeFileDataHandler),
            (r'/statistics', statistics.StatisticsHandler)
        ],
        debug=True
    )

    return app

if __name__ == "__main__":
    tornado.platform.asyncio.AsyncIOMainLoop().install()
    application = make_app()
    tornado.log.enable_pretty_logging()
    application.listen(7000, address='127.0.0.1')
    asyncio.get_event_loop().run_forever()
