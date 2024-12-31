# std pkgs
import asyncio
import io
import logging
import os.path
# tornado
import tornado
import tornado.websocket
from tornado.options import define, options, parse_command_line
# nodom
import nd_consts
import nd_web

CHUNK_SIZE = 2**16  # 64K chunks
BUFFER = bytearray(CHUNK_SIZE)
parquet_path = lambda pq_name: os.path.join(nd_consts.ND_ROOT_DIR, 'dat', pq_name)

class ParquetHandler(tornado.web.RequestHandler):
    def set_default_headers(self, *args, **kwargs):
        # https://www.marginalia.nu/log/a_105_duckdb_parquet/
        # https://developer.mozilla.org/en-US/docs/Web/HTTP/Range_requests
        # self.set_header("Access-Control-Allow-Origin", f"http://{options.host}:{options.node_port}")
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "x-requested-with")
        self.set_header('Access-Control-Allow-Methods', ' GET, HEAD, OPTIONS')
        self.set_header('Access-Control-Max-Age', '86400')
        # accept Ranged requests for chunks
        self.set_header("Accept-Ranges", "bytes")
        self.set_header("Connection", "keep-alive")

    def get(self, pq_name):
        pq_path = parquet_path(pq_name)
        if not os.path.exists(pq_path):
            logging.error(f'ParquetHandler.get: {pq_path} not found')
            self.set_status(404)
            return
        self.set_header('Content-Type', 'application/octet-stream')
        # is this a Ranged request?
        # https://developer.mozilla.org/en-US/docs/Web/HTTP/Range_requests
        range_header_val = self.request.headers.get('Range')
        logging.info(f'ParquetHandler.get: {pq_name} Range:{range_header_val}')
        start_byte = 0
        end_byte = 0
        if not range_header_val:
            logging.info(f'ParquetHandler.get: no Range header in GET {pq_name}')
        else:
            # fullest form: "bytes=start-end/size"
            # we may also get bytes=start, bytes=start-end
            # so first we discard the bytes= preamble
            start_index = range_header_val.find('=')
            if start_index != -1:
                range_header_val = range_header_val[start_index+1:]
            end_index = range_header_val.find('/')
            if end_index != -1:
                range_header_val = range_header_val[:end_index]
            range_fields = range_header_val.split('-')
            if len(range_fields) > 0:
                start_byte = int(range_fields[0])
            if len(range_fields) > 1:
                end_byte = int(range_fields[1])
        # return 206 partial if end_byte!=0 after the Range shredding above
        # else a plain ole 200 if we serve the whole file
        http_status = 206
        if end_byte == 0:
            http_status = 200
            end_byte = os.path.getsize(pq_path)
        logging.info(f'ParquetHandler.get: {pq_name} serving Range:{start_byte}-{end_byte}')
        with open(pq_path, 'rb') as pq_file:
            current_byte = start_byte
            while (current_byte < end_byte):
                pq_file.seek(current_byte)
                bytes_read = pq_file.read(CHUNK_SIZE)
                self.write(bytes_read)
                current_byte += CHUNK_SIZE
        self.set_status(http_status)
        self.finish()

    def options(self, *args):
        # HTTP OPTIONS to check access to a resource if we run SQL that
        # points at private or localhost from eg shell.duckdb.org
        origin = self.request.headers.get('Origin')
        # https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/405
        # 405: method known but not allowed for unknown origin
        http_status = 405
        # set 204 to indicate OK and no content
        if origin in nd_web.GOOD_HTTP_ORIGINS:
            http_status = 204
        logging.info(f'ParquetHandler.options: Origin:{origin} {http_status}')
        self.set_status(http_status)
        self.finish()

    def head(self, pq_name):
        # HTTP HEAD: we get this after OPTIONS (if a CORS check needed)
        # DuckDB wants the Content-Length header to figure the PQ size
        # No response body: just headers
        pq_path = parquet_path(pq_name)
        if not os.path.exists(pq_path):
            logging.error(f'ParquetHandler.head: {pq_path} not found')
            self.set_status(404)
            return
        pq_size = os.path.getsize(pq_path)
        self.set_header("Content-Length", f"{pq_size}")
        logging.info(f'ParquetHandler.head: {pq_path} sz:{pq_size}')
        self.set_status(200)


EXTRA_HANDLERS = [
    (r'/api/parquet/(.*)', ParquetHandler),
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
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
