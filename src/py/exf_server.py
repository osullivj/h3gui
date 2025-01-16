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
            dict(
                rname='Combo',
                cspec=dict(
                    cname='instruments',
                    index='selected_instrument',
                    label='Instrument',
                ),
            ),
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
            dict(rname='SameLine'),
            dict(rname='Text',
                cspec=dict(
                    text='Start date',
                ),
            ),
            dict(
                rname='DatePicker',
                cspec=dict(
                    cname='end_date',
                ),
            ),
            dict(rname='SameLine'),
            dict(rname='Text',
                cspec=dict(
                    text='End date',
                ),
            ),
            dict(rname='Separator', cspec=dict()),
            dict(
                rname='Button',
                cspec=dict(
                    text="Scan",
                    # next three fields align with {nd_type:"ParquetScan, sql:"...", query_id:".."}
                    action='ParquetScan',
                    sql='scan_sql',
                    query_id='scan_query_id',
                ),
            ),
            dict(rname='SameLine'),
            dict(
                rname='Button',
                cspec=dict(
                    text="Summary",
                    action="depth_summary_modal",
                ),
            ),
            dict(rname='Footer', cspec=dict()),
        ],
    ),
    # not a Home child? Must have an ID to be pushable
    dict(
        widget_id='depth_summary_modal',
        rname='DuckTableSummaryModal',
        cspec=dict(
            title='Depth table',
            cname='db_summary_depth',
        ),
    ),
]

PQ_SCAN_SQL = 'BEGIN; DROP TABLE IF EXISTS %(scan_query_id)s; CREATE TABLE %(scan_query_id)s as select * from parquet_scan(%(scan_urls)s); COMMIT;'

EXF_DATA = dict(
    home_title = 'FGB',
    start_date = (2008,9,1),       # 3 tuple YMD
    end_date = (2008,9,1),
    # NB tuple gives us Array in TS, and list gives us Object
    instruments = ('FGBMU8', 'FGBMZ8', 'FGBXZ8', 'FGBSU8', 'FGBSZ8', 'FGBXU8', 'FGBLU8', 'FGBLZ8'),
    selected_instrument = 0,
    scan_sql = PQ_SCAN_SQL % dict(scan_query_id='depth', scan_urls=[]),
    scan_query_id = 'depth',
    scan_urls = [],
    # empty placeholder: see main.ts:on_duck_event for hardwiring of db_summary_ prefix
    db_summary_depth = dict(),
)

# nd_utils.file_list needs one more arg after this partial bind for the pattern we're matching
parquet_list_func = functools.partial(nd_utils.file_list, nd_consts.PQ_DIR, '*.parquet')


EXTRA_HANDLERS = [
    (r'/api/parquet/(.*)', nd_web.ParquetHandler, dict(path=os.path.join(nd_consts.ND_ROOT_DIR, 'dat')))
]

is_scan_change = lambda c: c.get('cache_key') in ['start_date', 'end_date', 'selected_instrument']

class DepthApp(nd_web.NDAPIApp):
    def __init__(self):
        super().__init__(EXTRA_HANDLERS)
        self.is_duck_app = True
        self.cache = dict(
            layout=EXF_LAYOUT,
            data=EXF_DATA,
        )

    def on_client_data_changes(self, change_list):
        # Have selected_instrument, start_date or end_date changed?
        # If so wewe need to send a fresh parquet_scan up to the client
        scan_data_changes = [c for c in change_list if is_scan_change(c)]
        if scan_data_changes:
            data_cache = self.cache['data']
            # first we need the selected instrument to compose a fmt string for
            # file name date matching
            instrument_index = data_cache['selected_instrument']
            instrument_name = data_cache['instruments'][instrument_index]
            # get a list of all files for this instrument: NB the * in the
            # match string, which is not a regex, it's a unix fnmatch
            instrument_specific_files = nd_utils.file_list(nd_consts.PQ_DIR, f'{instrument_name}_*.parquet')
            # reduce the list to only files in the date range
            # here the format string is a strftime format
            ranged_matches = nd_utils.date_ranged_file_name_matches(instrument_specific_files,
                            data_cache['start_date'], data_cache['end_date'], f'{instrument_name}_%Y%m%d.parquet')
            # convert filenames to PQ URLs
            data_cache['scan_urls'] = [f'https://localhost/api/parquet/{pqfile}' for pqfile in ranged_matches]
            old_val = data_cache['scan_sql']
            new_val = PQ_SCAN_SQL % data_cache
            data_cache['scan_sql'] = new_val
            # finally, return the extra changes to be processed by the client
            return [dict(nd_type='DataChange', cache_key='scan_sql', old_value=old_val, new_value=new_val)]


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


if __name__ == "__main__":
    asyncio.run(main())
