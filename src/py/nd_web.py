# std pkgs
from datetime import datetime
import json
import os.path
import uuid
# tornado
import tornado
import tornado.websocket
from tornado.options import define, options
from tornado.web import StaticFileHandler
# nodom
import nd_utils
import nd_consts

# command line option definitions: same for all tornado procs
# individual server impls will set "port"
define("debug", default=True, help="run in debug mode")
define( "host", default="localhost")
define( "node_port", default=8080)
# tornado logs to stderr by default; however we have nd_utils.init_logging,
# which is unaware of the tornado log setup. We cannot set here as Tornado's
# log.py defines, so we set on the cmd line --log-to-stderr

logr = nd_utils.init_logging(__name__)

GOOD_HTTP_ORIGINS = ['https://shell.duckdb.org', 'https://sql-workbench.com']

class APIHandlerBase(tornado.web.RequestHandler):
    def set_default_headers(self, *args, **kwargs):
        self.set_header("Access-Control-Allow-Origin", f"http://{options.host}:{options.node_port}")

class DuckJournalHandler(tornado.web.RequestHandler):
    def get(self, slug):
        self.set_header("Content-Type", "text/plain")
        response_text = self.application.on_duck_journal_request(slug)
        self.write(response_text)
        self.finish()

class JSONHandler(APIHandlerBase):
    def get(self, slug):
        response_json = self.application.on_api_request(slug)
        self.write(response_json)
        self.finish()


class WebSockHandler(tornado.websocket.WebSocketHandler):
    def check_origin(self, origin):
        return True

    def open(self):
        self._uuid = str(uuid.uuid4())
        logr.info(f'WebSockHandler.open: {self._uuid}')

    def on_close(self):
        logr.info(f'WebSockHandler.on_close: {self._uuid}')

    def on_message(self, msg):
        logr.info(f'on_message: {self._uuid} IN {msg}')
        msg_dict = json.loads(msg)
        self.application.on_ws_message(self, msg_dict)


ND_HANDLERS = [
    (r'/api/websock', WebSockHandler),
    (r'/api/(.*)', JSONHandler),
    (r'/ui/duckjournal/(.*)', DuckJournalHandler),
    (r'/imgui/misc/fonts/(.*)', StaticFileHandler, dict(path=os.path.join(nd_consts.IMGUI_DIR, 'imgui', 'misc', 'fonts'))),
    (r'/node_modules/@flyover/system/build/(.*)', StaticFileHandler, dict(path=os.path.join(nd_consts.IMGUI_DIR, 'node_modules', '@flyover', 'system', 'build'))),
    (r'/example/build/(.*)', StaticFileHandler, dict(path=os.path.join(nd_consts.IMGUI_DIR, 'example', 'build'))),
    (r'/build/(.*)', StaticFileHandler, dict(path=os.path.join(nd_consts.IMGUI_DIR, 'build'))),
    (r'/example/(.*)', StaticFileHandler, dict(path=os.path.join(nd_consts.IMGUI_DIR, 'example'))),
    (r'/(.*)', StaticFileHandler, dict(path=nd_consts.ND_ROOT_DIR)),
]

class NDAPIApp( tornado.web.Application):
    def __init__( self, extra_handlers = [], settings_dict = {}):
        # extra_handlers first so they get first crack at the match
        self.cache = dict()
        handlers = extra_handlers + ND_HANDLERS
        settings = settings_dict
        tornado.web.Application.__init__( self, handlers, **settings)
        self.ws_handlers = dict(
            DataChange=self.on_data_change,
            DuckOp=self.on_duck_op,
        )
        # keyed on websock handler object itself
        self.duck_op_dict = dict()

    def on_api_request(self, json_key):
        return json.dumps(self.cache.get(json_key))

    def on_duck_journal_request(self, slug):
        logr.info(f'on_duck_journal_request: duck_op_dict:{self.duck_op_dict}')
        journal_entries = self.duck_op_dict.get(slug, [])
        journal_text = '\n'.join( [ j['sql'] for j in journal_entries ] )
        logr.info(f'on_duck_journal_request: {slug} {journal_text}')
        return journal_text

    def ws_no_op(self, ws, msg_dict):
        err = f'ws_no_op: {msg_dict['nd_type']}'
        logr.error(err)
        raise Exception(err)

    def on_data_change(self, ws, msg_dict):
        changes = []
        # post the new value into data cache
        ckey = msg_dict["cache_key"]
        data_cache = self.cache['data']
        data_cache[ckey] = msg_dict["new_value"]
        conf_dict = msg_dict.copy()
        conf_dict['nd_type'] = 'DataChangeConfirmed'
        changes.append(conf_dict)
        # check for update actions
        action_cache = self.cache.get('action')
        if not action_cache:
            return changes
        # copy so we don't drain the orig cache copy
        action_list = action_cache.get(ckey, []).copy()
        if not action_list:
            return changes
        # fire update actions
        data_cache_target = action_list.pop(0)
        old_val = data_cache.get(data_cache_target)
        primary_func = action_list.pop(0)
        params = []
        for action in action_list:
            if isinstance(action, str): # not a func, a cache ref
                params.append(data_cache.get(action))
            else:
                params.append(action())
        new_val = primary_func(*params)
        data_cache[data_cache_target] = new_val
        # send server side data changes back to client
        changes.append(dict(new_value=new_val, old_value=old_val, cache_key=data_cache_target, nd_type='DataChange'))
        return changes

    def on_duck_op(self, ws, msg_dict):
        logr.info(f'on_duck_op: {ws._uuid} {msg_dict}')
        msg_dict['ts'] = datetime.now().isoformat()
        op_list = self.duck_op_dict.setdefault(ws._uuid, [])
        op_list.append(msg_dict)
        logr.info(f'on_duck_op: duck_op_dict:{self.duck_op_dict}')
        # let the client know about the uuid for this websock
        # so it can compose /ui/... URLs to see the duck log
        # for diagnostics
        return [dict(nd_type='DuckOpUUID', uuid=ws._uuid)]

    def on_ws_message(self, websock, mdict):
        msg_dict = mdict if isinstance(mdict, dict) else dict()
        ws_func = self.ws_handlers.get(msg_dict.get('nd_type'), self.ws_no_op)
        change_list = ws_func(websock, msg_dict)
        # no mutations or actions on changed cache entries, just send em
        # back up to the client...
        if change_list:
            for change in change_list:
                websock.write_message(change)
        return change_list