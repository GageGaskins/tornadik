import asyncio

import aiohttp

import tornado.web
import tornado.httpserver
import tornado.gen
import tornado.platform.asyncio

from tornadik.server.handlers import statistics

def make_app():
    app = tornado.web.Application(
        [
            (r'/(?P<nodeID>\w*)/nodeData', statistics.NodeDataHandler),
            (r'/fileData', statistics.NodeFileDataHandler)
        ],
        debug=True
    )

    return app

if __name__ == "__main__":
    print("I'm running")
    tornado.platform.asyncio.AsyncIOMainLoop().install()
    application = make_app()
    application.listen(6969, address='127.0.0.1')
    asyncio.get_event_loop().run_forever()
