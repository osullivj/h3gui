# builtin
import csv
from datetime import time, datetime
import json
import logging
import os.path
# 3rd pty
import pandas as pd
# h3gui
import h3consts
import h3utils


class DepthData(object):
    def __init__(self, data_dir):
        self.dframe = self.load_data(data_dir)

    def load_data(self, data_dir):
        # TODO: replace with eg duckDB
        data_frames = []
        for fname in os.listdir(data_dir):
            if fname.endswith('_pd.csv'):
                csv_path = os.path.join(data_dir, fname)
                data_frames.append(pd.read_csv(csv_path, usecols=h3consts.COLUMNS,
                            parse_dates=list(h3consts.CLEAN_DATE_FORMATS.keys()),
                                               date_format=h3consts.CLEAN_DATE_FORMATS))
        df = pd.concat(data_frames)
        logging.info(f'load_data: df.types\n{df.dtypes}')
        self.start_ts = df['FeedCaptureTS'].min()
        self.end_ts = df['FeedCaptureTS'].max()
        logging.info(f'load_data: start:{self.start_ts}/{type(self.start_ts)}, end:{self.end_ts}')
        return df

    def json_range(self):
        msg_dict = dict(h3type='ts_range', start_ts=self.start_ts, end_ts=self.end_ts)
        return json.dumps(msg_dict, default=h3utils.h3_json_encoder)

if __name__ == '__main__':
    h3utils.init_logging('depth_data')
    data_dir = os.path.join(h3consts.H3ROOT_DIR, 'dat')
    dd = DepthData(data_dir)
    logging.info(f'depth_data: json_range({dd.json_range()})')
