# std pkg
import asyncio
import json
import logging
# 3rd pty
from tornado.options import options, parse_command_line, define
# nodom
import nd_web
import nd_utils

NDAPP='add_server'

logr = nd_utils.init_logging(__name__)

ADDITION_LAYOUT = [
    dict(
        rname='Home',
        cspec=dict(
            title='Server side addition',
        ),
        children=[
            dict(rname='InputInt', cspec=dict(cname='op1', step=1)),
            dict(rname='InputInt', cspec=dict(cname='op2', step=2)),
            # see src/imgui.ts for enum defns
            # InputTextFlags.ReadOnly == 1 << 14 == 16384
            dict(rname='InputInt', cspec=dict(cname='op1_plus_op2', flags=16384)),
            dict(rname='Separator', cspec=dict()),
            dict(rname='Footer', cspec=dict()),
        ],
    ),
]


ADDITION_DATA = dict(
    home_title = 'WebAddition',
    op1=2,
    op2=3,
    op1_plus_op2=5,
)

is_addition_change = lambda c: c.get('cache_key') in ['op1', 'op2']


class AdditionApp(nd_web.NDAPIApp):
    def __init__(self):
        super().__init__(NDAPP)
        self.cache = dict(
            layout=ADDITION_LAYOUT,
            data=ADDITION_DATA,
        )

    def on_client_data_changes(self, change_list):
        # Have selected_instrument, start_date or end_date changed?
        # If so wewe need to send a fresh parquet_scan up to the client
        add_data_changes = [c for c in change_list if is_addition_change(c)]
        if add_data_changes:
            ckey = 'op1_plus_op2'
            data_cache = self.cache['data']
            new_val = data_cache['op1'] + data_cache['op2']
            change = dict(nd_type='DataChange', old_value=data_cache[ckey], new_value=new_val, cache_key=ckey)
            data_cache[ckey] = new_val
            return [change]

define("port", default=8090, help="run on the given port", type=int)

async def main():
    parse_command_line()
    app = AdditionApp()
    app.listen(options.port)
    logr.info(f'{__file__} port:{options.port}')
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
