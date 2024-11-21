import asyncio
import json
import logging
import tornado
import tornado.websocket
import os.path
import uuid

from tornado.options import define, options, parse_command_line

define("port", default=8090, help="run on the given port", type=int)
define("debug", default=True, help="run in debug mode")

SRC_ROOT_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

addition_layout = dict(
    home=dict(
        title='add_server',
        children=dict(
            operand1=dict(
                widget='InputInt',
                # The cache location provided below is for clarity,
                # we could have let it default to the widget name
                cache='operand1',
            ),
            operand2=dict(
                widget='InputInt',
            ),
            addition_result=dict(
                widget='Label',

            ),
        )
    )
)

addition_cache = dict(
    operand1=2,
    operand2=3,
    addition_result=None,
)

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("<p>HomePage</p>")
        self.finish()
        # self.render("index.html", messages=dict())


class LayoutHandler(tornado.web.RequestHandler):
    def get(self):
        self.write(json.dumps(addition_layout))
        self.finish()


class CacheHandler(tornado.web.RequestHandler):
    def get(self):
        self.write(json.dumps(addition_cache))
        self.finish()


class WebSockHandler(tornado.websocket.WebSocketHandler):
    clients = set()     # NB class member

    def open(self):
        self.__cls__.clients.add(self)

    def on_close(self):
        self.__cls__.clients.remove(self)

    def on_message(self, msg):
        logging.info(f'on_message:{msg}')


async def main():
    parse_command_line()
    app = tornado.web.Application(
        [
            (r"/layout", LayoutHandler),
            (r"/cache", CacheHandler),
            (r'/websock', WebSockHandler),
        ],
        cookie_secret="__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__",
        template_path=os.path.join(SRC_ROOT_DIR, "h3gui", "html"),
        static_path=os.path.join(SRC_ROOT_DIR, "imgui-jswt", "example"),  # common base dir
        static_url_prefix="/",  # not '/static/' !!
        xsrf_cookies=True,
        debug=options.debug,
    )
    app.listen(options.port)
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
