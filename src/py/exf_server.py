# std pkgs
import asyncio
import json
import logging
# tornado
import tornado.websocket
from tornado.options import options, parse_command_line
# nodom
import nd_web


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

EXF_CACHE = dict(
    home_title = 'FGB',
    start_date = (2008,9,21),     # 3 tuple YMD
    end_date = (2008,9,22),
)


class DepthApp(nd_web.NDAPIApp):
    def __init__(self):
        super().__init__()
        self.api_response = dict(
            layout=EXF_LAYOUT,
            cache=EXF_CACHE,
        )

    def on_api_request(self, json_key):
        return json.dumps(self.api_response.get(json_key))

    def on_ws_message(self, websock, msg_dict):
        if msg_dict["nd_type"] == "DataChange":
            ckey = msg_dict["cache_key"]
            exf_cache = self.api_response['cache']
            exf_cache[ckey] = msg_dict["new_value"]
            logging.info(f'on_message: OUT {msg_dict}')
            websock.write_message(json.dumps(msg_dict))


async def main():
    parse_command_line()
    app = DepthApp()
    app.listen(options.port)
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
