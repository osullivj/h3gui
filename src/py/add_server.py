# std pkg
import asyncio
import json
import logging
# 3rd pty
from tornado.options import options, parse_command_line
# nodom
import nd_web

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


ADDITION_CACHE = dict(
    home_title = 'WebAddition',
    op1=2,
    op2=3,
    op1_plus_op2=5,
)

class AdditionApp(nd_web.NDAPIApp):
    def __init__(self):
        super().__init__()
        self.api_response = dict(
            layout=ADDITION_LAYOUT,
            cache=ADDITION_CACHE,
            config=dict()
        )

    def on_api_request(self, json_key):
        return json.dumps(self.api_response.get(json_key))

    def on_ws_message(self, websock, msg_dict):
        if msg_dict["nd_type"] == "DataChange":
            ckey = msg_dict["cache_key"]
            addition_cache = self.api_response['cache']
            addition_cache[ckey] = msg_dict["new_value"]
            op1 = addition_cache["op1"]
            op2 = addition_cache["op2"]
            op1_plus_op2 = op1 + op2
            msg_dict["cache_key"] = "op1_plus_op2"
            msg_dict["old_value"] = addition_cache["op1_plus_op2"]
            msg_dict["new_value"] = op1_plus_op2
            addition_cache["op1_plus_op2"] = op1_plus_op2
            logging.info(f'on_message: OUT {msg_dict}')
            websock.write_message(json.dumps(msg_dict))


async def main():
    parse_command_line()
    app = AdditionApp()
    app.listen(options.port)
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
