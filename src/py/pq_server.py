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

CHUNK_SIZE = 2**16  # 64K chunks
BUFFER = bytearray(CHUNK_SIZE)
parquet_path = lambda pq_name: os.path.join(nd_consts.ND_ROOT_DIR, 'dat', pq_name)

logr = nd_utils.init_logging(__name__, True)

# Tornado implements HTTP ranges in StaticFileHandler
# However, DuckDB-Wasm can only invoke HTTPS from inside
# wasm code because of sandboxing. We also have to supply
# CORS headers that allow the Parquet server to have a
# diff URL from the GUI server. Hence a subclass...
class ParquetHandler(tornado.web.StaticFileHandler):
    def set_default_headers(self, *args, **kwargs):
        # https://www.marginalia.nu/log/a_105_duckdb_parquet/
        # https://developer.mozilla.org/en-US/docs/Web/HTTP/Range_requests
        # https://github.com/mozilla/pdf.js/issues/8566
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "Range, Origin, X-Requested-With, Content-Type, Accept, Authorization")
        self.set_header("Access-Control-Expose-Headers","Content-Length, Content-Encoding, Accept-Ranges, Content-Range")
        self.set_header('Access-Control-Allow-Methods', ' GET, HEAD, OPTIONS')
        # TODO: note cacheEpoch in DuckDBs browser_runtime.ts
        # Does is come from this header? We'll need to think about cache
        # eviction strategies...
        self.set_header('Access-Control-Max-Age', '86400')
        # accept Ranged requests for chunks
        self.set_header("Accept-Ranges", "bytes")
        self.set_header("Connection", "keep-alive")

EXTRA_HANDLERS = [
    (r'/api/parquet/(.*)', ParquetHandler, dict(path=os.path.join(nd_consts.ND_ROOT_DIR, 'dat')))
]

class PQApp(nd_web.NDAPIApp):
    def __init__(self):
        super().__init__(extra_handlers=EXTRA_HANDLERS)


define("port", default=443, help="run on the given port", type=int)


async def main():
    parse_command_line()
    # nd_utils.init_logging(os.path.split(__file__)[1], options.debug)
    # logging.getLogger('tornado.access').disabled = True
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
