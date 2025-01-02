# std pkgs
import json
import logging
# tornado
import tornado
import tornado.websocket
from tornado.options import define, options

# command line option definitions: same for all tornado procs
# individual server impls will set "port"
define("debug", default=True, help="run in debug mode")
define( "host", default="localhost")
define( "node_port", default=8080)

GOOD_HTTP_ORIGINS = ['https://shell.duckdb.org', 'https://sql-workbench.com']

class APIHandlerBase(tornado.web.RequestHandler):
    def set_default_headers(self, *args, **kwargs):
        self.set_header("Access-Control-Allow-Origin", f"http://{options.host}:{options.node_port}")
        # self.set_header("Access-Control-Allow-Headers", "x-requested-with")
        # self.set_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")


class JSONHandler(APIHandlerBase):
    def get(self, slug):
        response_json = self.application.on_api_request(slug)
        self.write(response_json)
        self.finish()


class WebSockHandler(tornado.websocket.WebSocketHandler):
    clients = set()     # NB class member

    def check_origin(self, origin):
        return True

    def open(self):
        self.__class__.clients.add(self)

    def on_close(self):
        self.__class__.clients.remove(self)

    def on_message(self, msg):
        logging.info(f'on_message: IN {msg}')
        msg_dict = json.loads(msg)
        self.application.on_ws_message(self, msg_dict)


ND_HANDLERS = [
    (r'/api/websock', WebSockHandler),
    (r'/api/(.*)', JSONHandler),
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
        )

    def on_api_request(self, json_key):
        return json.dumps(self.cache.get(json_key))

    def ws_no_op(self, msg_dict):
        err = f'ws_no_op: {msg_dict['nd_type']}'
        logging.error(err)
        raise Exception(err)

    def on_data_change(self, msg_dict):
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
        changes.append(dict(new_value=new_val, old_value=old_val, cache_key=data_cache_target, nd_type='DataChange'))
        return changes

    def on_ws_message(self, websock, mdict):
        msg_dict = mdict if isinstance(mdict, dict) else dict()
        ws_func = self.ws_handlers.get(msg_dict.get('nd_type'), self.ws_no_op)
        change_list = ws_func(msg_dict)
        if change_list:
            for change in change_list:
                websock.write_message(change)
        return change_list