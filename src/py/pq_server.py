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

NDAPP='pq_server'

logr = nd_utils.init_logging(NDAPP)

EXTRA_HANDLERS = [
    (r'/api/parquet/(.*)', nd_web.ParquetHandler, dict(path=os.path.join(nd_consts.ND_ROOT_DIR, 'dat')))
]

define("port", default=8891, help="run on the given port", type=int)

service = nd_utils.Service(NDAPP, {}, {}, False)

async def main():
    parse_command_line()
    app = nd_web.NDApp(service, EXTRA_HANDLERS)
    app.listen(options.port)
    logr.info(f'{NDAPP} port:{options.port}')
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
