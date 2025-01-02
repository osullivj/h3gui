# std pkgs
import asyncio
import functools
import json
import logging
# tornado
import tornado.websocket
from tornado.options import options, parse_command_line, define
# nodom
import nd_web
import nd_utils
import nd_consts

EXF_LAYOUT = [
    dict(
        rname='Home',
        cspec=dict(
            title='Eurex Futures',
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

class DepthApp(nd_web.NDAPIApp):
    def __init__(self):
        super().__init__()
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
        data_changes = [c for c in change_list if c.get('nd_type')=='DataChange']
        for dc in data_changes:
            if dc['cache_key'] == 'depth_pq_scan':
                depth_urls = [f'https://localhost/api/parquet/{pqfile}' for pqfile in dc['new_value']]
                sql = f"CREATE TABLE depth as select * from parquet_scan({depth_urls})"
                websock.write_message(dict(nd_type='ParquetScan', sql=sql))


define("port", default=8090, help="run on the given port", type=int)

async def main():
    parse_command_line()
    app = DepthApp()
    app.listen(options.port)
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
