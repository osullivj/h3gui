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
    start_date = (2008,9,21),       # 3 tuple YMD
    end_date = (2008,9,22),
    parquet_scan = [],              # computed from date tups
    dated_file_name_format = 'depth%Y%m%d.parquet',
)

parquet_scan_func = functools.partial(nd_utils.file_list, nd_consts.PQ_DIR, '*.parquet')
# list of functions or cache refs to eval
# element 0 is the data cache destination
# element 1 is real func and 2...N the params
date_change_action = [
    'parquet_scan',
    nd_utils.date_ranged_matches,   # provides val for parquet_scan
    parquet_scan_func,
    'start_date',
    'end_date',
    'dated_file_name_format',
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

    def on_api_request(self, json_key):
        return json.dumps(self.cache.get(json_key))

    def on_ws_message(self, websock, msg_dict):
        if msg_dict["nd_type"] == "DataChange":
            response_dict = self.on_data_change(msg_dict)
            logging.info(f'on_message: OUT {response_dict}')
            websock.write_message(json.dumps(response_dict))


    def on_data_change(self, msg_dict):
        # post the new value into data cache
        ckey = msg_dict["cache_key"]
        data_cache = self.cache['data']
        data_cache[ckey] = msg_dict["new_value"]
        # fire update actions
        action_list = self.cache['action'][ckey].copy()
        data_cache_target = action_list.pop(0)
        old_val = self.cache['data'][data_cache_target]
        primary_func = action_list.pop(0)
        params = []
        for action in action_list:
            if isinstance(action, str):
                params.append(self.cache['data'][action])
            else:
                params.append(action())
        new_val = primary_func(*params)
        self.cache['data'][data_cache_target] = new_val
        return dict(new_value=new_val, old_value=old_val, cache_key=data_cache_target, nd_type='DataChange')

define("port", default=8090, help="run on the given port", type=int)

async def main():
    parse_command_line()
    app = DepthApp()
    app.listen(options.port)
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
