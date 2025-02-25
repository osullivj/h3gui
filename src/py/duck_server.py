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

# duck_server is used as a child process by breadboard as
# a standin for duckdb-wasm in browser
NDAPP='duck_server'

logr = nd_utils.init_logging(NDAPP)

define("port", default=8892, help="run on the given port", type=int)

class DuckService(nd_utils.Service):
    def __init__(self):
        super().__init__(NDAPP, {}, {})
        # overwrite the default msg_handlers set in base
        # as we don't need DataChange and DuckOp here; those
        # handlers are for a "real" backend serving a nodom
        # duck browser process
        self.msg_handlers = dict(
            ParquetScan=self.on_scan,
            Query=self.on_query,
        )

    def on_scan(self, sql):
        pass

    def on_query(self, sql):
        pass


service = DuckService()

async def main():
    parse_command_line()
    app = nd_web.NDApp(service)
    app.listen(options.port)
    logr.info(f'{NDAPP} port:{options.port}')
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
