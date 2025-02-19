# builtin
import fnmatch
import json
import logging
import os.path
# 3rd pty
import pandas as pd
# h3gui
import h3consts
import h3utils


class DepthData(object):
    def __init__(self, source_dir, target_dir):
        self.source_dir = source_dir
        self.target_dir = target_dir

    def load_data(self):
        # various sanity testing checksums
        column_counts = set()
        column_names = set()
        column_types = set()
        logging.info(f'load_data: searching {self.source_dir}')
        for fname in os.listdir(self.source_dir):
            df = None
            if fnmatch.fnmatch(fname, 'depth200809[01]?_???????.csv'):
                csv_path = os.path.join(self.source_dir, fname)
                logging.info(f'load_data: processing {csv_path}')
                # 1st pass parse lets pandas guess the data types
                try:
                    df = pd.read_csv(csv_path, usecols=h3consts.COLUMNS, dtype=h3consts.DTYPES)
                            # parse_dates=h3consts.DATE_FIELDS, # list(h3consts.CLEAN_DATE_FORMATS.keys()),
                              #                  date_format=h3consts.DATE_FORMAT) # h3consts.CLEAN_DATE_FORMATS)

                except Exception as ex:
                    logging.error(f'load_data: skipping {fname} {ex}')
                    continue
                # now fix the dates after the fact: much faster than pandas trying
                # many possible conversions. First the simple conversions where a full
                # ISO8601 like timestamp has been provided...
                df['LastTradeTime'] = pd.to_datetime(df['LastTradeTime'])
                df['TranDateTime'] = pd.to_datetime(df['TranDateTime'])
                df['TS'] = pd.to_datetime(df['date'] + ' ' + df['time'])
                df['CaptureTS'] = pd.to_datetime(df['date'] + ' ' + df['FeedCaptureTS'])
                start_ts = df['FeedCaptureTS'].min()
                end_ts = df['FeedCaptureTS'].max()
                start_seq_id = df['FeedSequenceId'].min()
                end_seq_id = df['FeedSequenceId'].max()
                # do not need sym as it's the only varchar, and implicit in the file name
                df = df.drop(columns=['date', 'time', 'FeedCaptureTS'])
                df = df.sort_values(by=['FeedSequenceId'])
                # logging.info(f'load_data: {fname} df.types\n{df.dtypes}')
                logging.info(f'load_data: ts_range {fname} start:{start_ts}, end:{end_ts}')
                logging.info(f'load_data: seq_id_range {fname} start:{start_seq_id}, end:{end_seq_id}')
                # throw away the .csv (with [0]), the depth prefix (with [5:]) and split to (date, instcode)
                fdate, inst_code7s = os.path.splitext(fname)[0][5:].split('_')
                # consts use last 4 digits...
                inst_code4s = inst_code7s[3:]
                inst_name = h3consts.INSTRUMENTS.get(int(inst_code4s))
                if inst_name:
                    ofname = f'{inst_name}_{fdate}.csv'
                    opath = os.path.join(self.target_dir, ofname)
                    col_list = list(df.columns)
                    col_types = [str(df[col].dtype) for col in col_list]
                    logging.info(f'load_data: writing {opath} with {len(col_list)} columns')
                    column_counts.add(len(col_list))
                    column_names.add(str(col_list))
                    column_types.add(str(col_types))
                    # throw away all the dtype:object auxiliary stuff...
                    logging.info(f'{dict(zip(col_list, col_types))}')
                    # do not create an index field, use SeqNo
                    df.to_csv(opath, index=False, index_label='SeqNo')
                else:
                    logging.info(f'load_data: skipping {inst_code4s} {fname}')
        logging.info(f'load_data: {len(column_counts)} column counts')
        logging.info(f'load_data: {len(column_names)} name lists')
        logging.info(f'load_data: {len(column_names)} type lists')


if __name__ == '__main__':
    h3utils.init_logging(__file__)
    dd = DepthData(h3consts.EXT_DATA_SRC_DIR, os.path.join(h3consts.H3ROOT_DIR, 'dat'))
    dd.load_data()
