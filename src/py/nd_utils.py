# std pkgs
from datetime import datetime, date, timedelta
import fnmatch
import logging
import os.path
# pandas
import pandas as pd

one_day = timedelta(1)
file_list = lambda source_dir, pattern:[fname for fname in os.listdir(source_dir)
                                        if fnmatch.fnmatch(fname, pattern)]

def date_ranged_matches(file_list, start_date_tup, end_date_tup, fmt, max_delta=12):
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


def init_logging(log_name, debug=False):
    # tornado logs to stdout by default - we want it in a file in the %TEMP% dir
    log_file_name = f'{log_name}_{os.getpid()}.log'
    log_file_path = os.path.join(os.environ.get('TEMP'), log_file_name)
    logging.basicConfig(
        filename=log_file_name,
        format="%(asctime)s %(levelname)s %(thread)s %(name)s %(message)s",
        level=logging.DEBUG if debug else logging.INFO,
    )
    logging.getLogger().addHandler(logging.StreamHandler())


def h3_json_encoder(obj):
    # json.dumps( ) can't handle some types, so we provide an impl here
    if isinstance( obj, datetime):
        return obj.isoformat( )
    elif isinstance(obj, pd.Timestamp):
        return str(obj)



