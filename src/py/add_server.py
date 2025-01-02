# std pkg
import asyncio
import json
import logging
# 3rd pty
from tornado.options import options, parse_command_line, define
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


ADDITION_DATA = dict(
    home_title = 'WebAddition',
    op1=2,
    op2=3,
    op1_plus_op2=5,
)

addition_func = lambda x, y: x+y

# list of functions or cache refs to eval
# element 0 is the real func and 1...N the params
op_change_action = ['op1_plus_op2', addition_func, 'op1', 'op2']
# methods to fire on cache changes
ADDITION_ACTIONS = dict(
    op1=op_change_action,
    op2=op_change_action,
)
class AdditionApp(nd_web.NDAPIApp):
    def __init__(self):
        super().__init__()
        self.cache = dict(
            layout=ADDITION_LAYOUT,
            data=ADDITION_DATA,
            config=dict(),
            action=ADDITION_ACTIONS,
        )

define("port", default=8090, help="run on the given port", type=int)

async def main():
    parse_command_line()
    app = AdditionApp()
    app.listen(options.port)
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
