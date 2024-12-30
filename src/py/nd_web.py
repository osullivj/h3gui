# std pkgs
import json
import logging
# tornado
import tornado
import tornado.websocket
from tornado.options import define, options

# command line option definitions
define("port", default=8090, help="run on the given port", type=int)
define("debug", default=True, help="run in debug mode")
define( "host", default="localhost")
define( "node_port", default=8080)

class APIHandlerBase(tornado.web.RequestHandler):
    def set_default_headers(self, *args, **kwargs):
        self.set_header("Access-Control-Allow-Origin", f"http://{options.host}:{options.node_port}")
        # self.set_header("Access-Control-Allow-Headers", "x-requested-with")
        # self.set_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")


class JSONHandler(APIHandlerBase):
    def get(self, slug):
        response_json = self.application.on_api_request(slug)
        self.write(response_json)
        self.finish()


class WebSockHandler(tornado.websocket.WebSocketHandler):
    clients = set()     # NB class member

    def check_origin(self, origin):
        return True

    def open(self):
        self.__class__.clients.add(self)

    def on_close(self):
        self.__class__.clients.remove(self)

    def on_message(self, msg):
        logging.info(f'on_message: IN {msg}')
        msg_dict = json.loads(msg)
        self.application.on_ws_message(self, msg_dict)


ND_HANDLERS = [
    (r'/api/websock', WebSockHandler),
    (r'/api/(.*)', JSONHandler),
]

class NDAPIApp( tornado.web.Application):
    def __init__( self, extra_handlers = [], settings_dict = {}):
        handlers = ND_HANDLERS + extra_handlers
        settings = settings_dict
        tornado.web.Application.__init__( self, handlers, **settings)

    def on_api_request(self, json_key):
        err = f'NDAPIApp.get_api_response not implemented json_key({json_key})'
        logging.error(err)
        raise Exception(err)

    def on_ws_message(self, websock, msg_dict):
        err = f'NDAPIApp.on_ws_message not implemented msg_dict({msg_dict})'
        logging.error(err)
        raise Exception(err)
