import tornado.web
import tornado.gen


class BaseHandler(tornado.web.RequestHandler):

    # Set to all for functionality purposes during development. Will pull from settings later a la Waterbutler
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")