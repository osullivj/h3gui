# std pkgs
from datetime import datetime
import json
import logging
import os.path

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
