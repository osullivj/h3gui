# std pkgs
import asyncio
import logging
import os.path
# tornado
import tornado
import tornado.websocket
from tornado.options import define, options, parse_command_line
from tornado.web import StaticFileHandler
# nodom
import nd_consts
import nd_web
import nd_utils

logr = nd_utils.init_logging(__name__)

EXTRA_HANDLERS = [
    (r'/api/parquet/(.*)', nd_web.ParquetHandler, dict(path=os.path.join(nd_consts.ND_ROOT_DIR, 'dat')))
]

class PQApp(nd_web.NDAPIApp):
    def __init__(self):
        super().__init__(extra_handlers=EXTRA_HANDLERS)


define("port", default=443, help="run on the given port", type=int)


async def main():
    parse_command_line()
    cert_path = os.path.normpath(os.path.join(nd_consts.ND_ROOT_DIR, 'cfg', 'h3'))
    app = PQApp()
    https_server = tornado.httpserver.HTTPServer(app, ssl_options={
        "certfile": os.path.join(cert_path, "ssl_cert.pem"),
        "keyfile": os.path.join(cert_path, "ssl_key.pem"),
    })
    https_server.listen(options.port)
    logr.info(f'{__file__} port:{options.port} cert_path:{cert_path}')
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
