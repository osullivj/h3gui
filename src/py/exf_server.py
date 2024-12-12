import asyncio
import json
import logging
import time
import tornado
import tornado.websocket
import os.path
import uuid

from tornado.options import define, options, parse_command_line

# command line option definitions
define("port", default=8090, help="run on the given port", type=int)
define("debug", default=True, help="run in debug mode")
define( "host", default="localhost")
define( "node_port", default=8080)

SRC_ROOT_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

exf_layout = [
    dict(
        rname='Home',
        cspec=dict(
            title='Eurex Futures',
        ),
        children=[
            dict(rname='DatePicker', cspec=dict(cname='start_date')),
            dict(rname='Separator', cspec=dict()),
            dict(rname='Footer', cspec=dict()),
        ],
    ),
]

# TODO: cache behaviour
# 1. Notify BE when val changes
# 2. Consume only data eg mkt data
exf_cache = dict(
    home_title = 'FGB',
    start_date = (2008,9,21),     # 3 tuple YMD
)

class APIHandlerBase(tornado.web.RequestHandler):
    def set_default_headers(self, *args, **kwargs):
        self.set_header("Access-Control-Allow-Origin", f"http://{options.host}:{options.node_port}")
        # self.set_header("Access-Control-Allow-Headers", "x-requested-with")
        # self.set_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")


class LayoutHandler(APIHandlerBase):
    def get(self):
        # Access-Control-Allow-Origin: http://siteA.com
        exf_layout_json = json.dumps(exf_layout)
        self.write(exf_layout_json)
        self.finish()


class CacheHandler(APIHandlerBase):
    def get(self):
        exf_cache_json = json.dumps(exf_cache)
        self.write(exf_cache_json)
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
        if msg_dict["nd_type"] == "DataChange":
            ckey = msg_dict["cache_key"]
            exf_cache[ckey] = msg_dict["new_value"]
            op1 = exf_cache["op1"]
            op2 = exf_cache["op2"]
            op1_plus_op2 = op1 + op2
            msg_dict["cache_key"] = "op1_plus_op2"
            msg_dict["old_value"] = exf_cache["op1_plus_op2"]
            msg_dict["new_value"] = op1_plus_op2
            exf_cache["op1_plus_op2"] = op1_plus_op2
            logging.info(f'on_message: OUT {msg_dict}')
            self.write_message(json.dumps(msg_dict))



async def main():
    parse_command_line()
    app = tornado.web.Application(
        [
            # common "/api/" base route to make life easier in nginx.conf
            (r"/api/layout", LayoutHandler),
            (r"/api/cache", CacheHandler),
            (r'/api/websock', WebSockHandler),
        ],
        # cookie_secret="__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__",
        # template_path=os.path.join(SRC_ROOT_DIR, "h3gui", "html"),
        # static_path=os.path.join(SRC_ROOT_DIR, "imgui-jswt", "example"),  # common base dir
        # static_url_prefix="/",  # not '/static/' !!
        xsrf_cookies=True,
        debug=options.debug,
    )
    app.listen(options.port)
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())