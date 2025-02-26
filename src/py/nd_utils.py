# std pkgs
from datetime import datetime, date, timedelta
import fnmatch
import json
import logging
import os.path
# pandas
import pandas as pd

one_day = timedelta(1)
file_list = lambda source_dir, pattern:[fname for fname in os.listdir(source_dir)
                                        if fnmatch.fnmatch(fname, pattern)]

is_data_change = lambda c: c.get('nd_type')=='DataChangeConfirmed'

def date_ranged_file_name_matches(file_list, start_date_tup, end_date_tup, fmt, max_delta=12):
    matches = []
    # YMD tuples are in the right order for a *args list unpack
    sdate = datetime(*start_date_tup)
    edate = datetime(*end_date_tup)
    range_delta = edate - sdate
    # ensure end_date > start_date
    if range_delta.days < 0:
        sdate, edate = edate, sdate
    while sdate <= edate:
        dated_file_name = sdate.strftime(fmt)
        if dated_file_name in file_list:
            matches.append(dated_file_name)
        sdate = sdate + one_day
    return matches


def init_logging(log_name, debug=False, console=False):
    # tornado logs to stdout by default - we want it in a file in the %TEMP% dir
    log_file_name = f'{log_name}_{os.getpid()}.log'
    log_file_path = os.path.join(os.environ.get('TEMP'), log_file_name)
    # create our logger object
    # NB others create their own eg "tornado.access"
    log_level = logging.DEBUG if debug else logging.INFO
    logger = logging.getLogger(log_name)
    logger.setLevel(log_level)
    # create console and file handlers
    file_handler = logging.FileHandler(log_file_path)
    file_handler.setLevel(log_level)
    if console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    return logger


def h3_json_encoder(obj):
    # json.dumps( ) can't handle some types, so we provide an impl here
    if isinstance( obj, datetime):
        return obj.isoformat( )
    elif isinstance(obj, pd.Timestamp):
        return str(obj)

# for Service diagnostic logging
logr = init_logging(__name__)

class Service(object):
    def __init__(self, app_name, layout, data, is_duck=False):
        self.app_name = app_name
        self.cache = dict(layout=layout, data=data)
        # duck_op_dict is keyed on uuid from nd_web.WebSockHandler.open()
        self.duck_op_dict = dict()
        self.is_duck_app = is_duck

    def on_ws_open(self, ws):
        pass

    def on_ws_close(self, ws):
        pass

    def on_api_request(self, json_key):
        return json.dumps(self.cache.get(json_key))

    def on_duck_journal_request(self, client_uuid):
        logr.info(f'on_duck_journal_request: duck_op_dict:{self.duck_op_dict}')
        journal_entries = self.duck_op_dict.get(client_uuid, [])
        journal_text = '\n'.join( [ j['sql'] for j in journal_entries ] )
        logr.info(f'on_duck_#journal_request: {client_uuid} {journal_text}')
        return journal_text

    def on_no_op(self, client_uuid, msg_dict):
        err = f'ws_no_op: client:{client_uuid} msg:{msg_dict}'
        logr.error(err)
        raise Exception(err)

    def on_data_change(self, client_uuid, client_change):
        # GUI has changed client cached data, so
        # apply the change on the server side,
        # and give app logic a chance to append
        # further changes...
        # First, post the new value into data cache
        logr.info(f'on_data_change: client_change:{client_change}')
        ckey = client_change["cache_key"]
        data_cache = self.cache['data']
        data_cache[ckey] = client_change["new_value"]
        logr.info(f'on_data_change: data_cache:{data_cache}')
        conf_dict = client_change.copy()
        conf_dict['nd_type'] = 'DataChangeConfirmed'
        server_changes = self.on_client_data_change(client_uuid, client_change)
        return [conf_dict] + server_changes

    def on_duck_op(self, client_uuid, msg_dict):
        logr.info(f'on_duck_op: client:{client_uuid} {msg_dict}')
        msg_dict['ts'] = datetime.now().isoformat()
        op_list = self.duck_op_dict.setdefault(client_uuid, [])
        op_list.append(msg_dict)
        logr.info(f'on_duck_op: duck_op_dict:{self.duck_op_dict}')
        # let the client know about the uuid for this websock
        # so it can compose /ui/... URLs to see the duck log
        # for diagnostics
        return [dict(nd_type='DuckOpUUID', uuid=client_uuid)]

    def on_client_data_change(self, client_uuid, client_change):
        # override this method to make server side cache
        # changes in response to client changes, and have
        # the whole change set relayed to client...
        return []