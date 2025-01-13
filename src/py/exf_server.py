# std pkgs
import asyncio
import functools
import json
import logging
import os.path
# tornado
import tornado.websocket
from tornado.options import options, parse_command_line, define
# nodom
import nd_web
import nd_utils
import nd_consts

logr = nd_utils.init_logging(__name__)

EXF_LAYOUT = [
    dict(
        rname='Home',
        cspec=dict(
            title='Eurex Futures',
            # only applicable here in the Home widget
            gui_canvas_style_width="200px",
            gui_canvas_style_height="100px",
            shell_canvas_style_left="100px",
            shell_canvas_style_top = "0px"
        ),
        children=[
            # see src/imgui.ts for enum defns
            # TableFlags.ReadOnly == 1 << 14 == 16384
            dict(
                rname='DatePicker',
                cspec=dict(
                    cname='start_date',
                    table_flags=0,
                    table_size=(280, -1),
                ),
            ),
            dict(
                rname='DatePicker',
                cspec=dict(
                    cname='end_date',
                ),
            ),
            dict(rname='Separator', cspec=dict()),
            dict(rname='Footer', cspec=dict()),
        ],
    ),
]

EXF_DATA = dict(
    home_title = 'FGB',
    start_date = (2008,9,1),       # 3 tuple YMD
    end_date = (2008,9,1),
    depth_pq_scan = [],             # computed from date tups
    depth_pq_fmt = 'depth%Y%m%d.parquet',
)

# data_change_actions should be pure cache data manipulation
# no sending of WS msgs
parquet_list_func = functools.partial(nd_utils.file_list, nd_consts.PQ_DIR, '*.parquet')
# list of functions or cache refs to eval
# element 0 is the data cache destination
# element 1 is real func and 2...N the params
date_change_action = [
    'depth_pq_scan',
    nd_utils.date_ranged_matches,   # provides val for parquet_scan
    parquet_list_func,
    'start_date',
    'end_date',
    'depth_pq_fmt',
]
# methods to fire on cache changes
EXF_ACTIONS = dict(
    start_date=date_change_action,
    end_date=date_change_action,
)


PQ_SCAN_SQL = 'BEGIN; DROP TABLE IF EXISTS %(table)s; CREATE TABLE %(table)s as select * from parquet_scan(%(urls)s); COMMIT;'

EXTRA_HANDLERS = [
    (r'/api/parquet/(.*)', nd_web.ParquetHandler, dict(path=os.path.join(nd_consts.ND_ROOT_DIR, 'dat')))
]

class DepthApp(nd_web.NDAPIApp):
    def __init__(self):
        super().__init__(EXTRA_HANDLERS)
        self.is_duck_app = True
        self.cache = dict(
            layout=EXF_LAYOUT,
            data=EXF_DATA,
            action=EXF_ACTIONS,
        )

    def on_ws_message(self, websock, mdict):
        change_list = super().on_ws_message(websock, mdict)
        # any data changes on this side we should know about?
        # eg filter out DataChangedConfirmed, as those are acks to
        # changes from the other side
        if change_list:
            data_changes = [c for c in change_list if c.get('nd_type')=='DataChange']
            for dc in data_changes:
                if dc['cache_key'] == 'depth_pq_scan':
                    depth_urls = [f'https://localhost/api/parquet/{pqfile}' for pqfile in dc['new_value']]
                    table = 'depth'
                    sql = PQ_SCAN_SQL % dict(table=table, urls=depth_urls)
                    websock.write_message(dict(nd_type='ParquetScan', sql=sql, table=f"{table}"))


define("port", default=443, help="run on the given port", type=int)

async def main():
    parse_command_line()
    cert_path = os.path.normpath(os.path.join(nd_consts.ND_ROOT_DIR, 'cfg', 'h3'))
    app = DepthApp()
    https_server = tornado.httpserver.HTTPServer(app, ssl_options={
        "certfile": os.path.join(cert_path, "ssl_cert.pem"),
        "keyfile": os.path.join(cert_path, "ssl_key.pem"),
    })
    https_server.listen(options.port)
    logr.info(f'{__file__} port:{options.port} cert_path:{cert_path}')

    await asyncio.Event().wait()
    parse_command_line()
    app = DepthApp()
    app.listen(options.port)
    logging.info(f'{__file__} port:{options.port}')
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
