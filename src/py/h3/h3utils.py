# std pkgs
from datetime import datetime
import json
import logging
import os.path
# pandas
import pandas as pd

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

