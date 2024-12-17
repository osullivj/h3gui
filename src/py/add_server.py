import asyncio
import json
import logging
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

addition_layout = [
    dict(
        rname='Home',
        cspec=dict(
            title='Server side addition',
        ),
        children=[
            dict(rname='InputInt', cspec=dict(cname='op1', step=1)),
            dict(rname='InputInt', cspec=dict(cname='op2', step=2)),
            # see src/imgui.ts for enum defns
            # InputTextFlags.ReadOnly == 1 << 14 == 16384
            dict(rname='InputInt', cspec=dict(cname='op1_plus_op2', flags=16384)),
            dict(rname='Separator', cspec=dict()),
            dict(rname='Footer', cspec=dict()),
        ],
    ),
]

# TODO: cache behaviour
# 1. Notify BE when val changes
# 2. Consume only data eg mkt data

addition_cache = dict(
    home_title = 'WebAddition',
    op1=2,
    op2=3,
    op1_plus_op2=5,
)

class APIHandlerBase(tornado.web.RequestHandler):
    def set_default_headers(self, *args, **kwargs):
        self.set_header("Access-Control-Allow-Origin", f"http://{options.host}:{options.node_port}")
        # self.set_header("Access-Control-Allow-Headers", "x-requested-with")
        # self.set_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")


class LayoutHandler(APIHandlerBase):
    def get(self):
        # Access-Control-Allow-Origin: http://siteA.com
        addition_layout_json = json.dumps(addition_layout)
        self.write(addition_layout_json)
        self.finish()


class CacheHandler(APIHandlerBase):
    def get(self):
        addition_cache_json = json.dumps(addition_cache)
        self.write(addition_cache_json)
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
            addition_cache[ckey] = msg_dict["new_value"]
            op1 = addition_cache["op1"]
            op2 = addition_cache["op2"]
            op1_plus_op2 = op1 + op2
            msg_dict["cache_key"] = "op1_plus_op2"
            msg_dict["old_value"] = addition_cache["op1_plus_op2"]
            msg_dict["new_value"] = op1_plus_op2
            addition_cache["op1_plus_op2"] = op1_plus_op2
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
