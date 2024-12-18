# builtin
import fnmatch
import logging
import os
import os.path
# 3rd pty
import pandas as pd
import pyarrow as pa
import pyarrow.csv as pa_csv
import pyarrow.parquet as pq
# h3gui
import nd_consts
import nd_utils

# TODO
# argparse
# batch translate all depth

# one set per field: see how many distinct vals...
# invariant: data, sym, MessageType, Instance, Region, MarketName, DisplayName,
# variant: time
# https://stackoverflow.com/questions/48899051/how-to-drop-a-specific-column-of-csv-file-while-reading-it-using-pandas

IGNORE=['data', 'MessageType', 'Instance', 'Region', 'MarketName', 'DisplayName', 'SubMarketName'
           'InstrumentId', 'InstrumentMarketType', 'PriceType', 'WorkupPrice', 'WorkupSize',
           'BestBidOrders', 'BestAskOrders', 'BidLockPrice', 'AskLockPrice', 'FeedId']

# Source data has hh:mm:ss.fff
TIME_FIELDS = ['time', 'FeedCaptureTS']

strip_hms = lambda ts: pd.Timestamp(year=ts.year, month=ts.month, day=ts.day)


def clean_csv(source_dir, target_dir, csv_file):
    csv_in_path = os.path.join(source_dir, csv_file)
    csv_base, csv_ext = os.path.splitext(csv_file)
    csv_out_name = f'{csv_base}_pd{csv_ext}'
    csv_out_path = os.path.join(target_dir, csv_out_name)
    df = pd.read_csv(csv_in_path, usecols=nd_consts.COLUMNS,
                     parse_dates=list(nd_consts.RAW_DATE_FORMATS.keys()),
                     date_format=nd_consts.RAW_DATE_FORMATS)
    logging.info('== df.dtypes 1')
    logging.info(df.dtypes)
    logging.info(df.shape)

    # Add date to LastTradeTime and time: get a base date from
    # LastTradeTime col for correct date on time cols when they
    # become datetime. NB SOD LastTradeTime will have H:M:S as
    # 00:00:00 but time will not, so we justextract the days and
    # ignore HH:MM:SS
    last_trade_ts = df.iloc[-1]['LastTradeTime']
    last_ts = df.iloc[-1]['time']
    base_delta = strip_hms(last_trade_ts) - strip_hms(last_ts)
    df['time'] += base_delta
    df['FeedCaptureTS'] += base_delta
    df['sym'] = df['sym'].str[2:9]
    df['sym'] = df['sym'].astype(int) - 2240000
    # put them in feed sequence so we can see where eg last trade price changes
    df = df.sort_values(by=['FeedSequenceId'])

    logging.info('== df.dtypes 2')
    logging.info(df.dtypes)
    logging.info(df.shape)
    # group by symbol, and filter out any symbols where
    # LastTradePrice is always 0.0: no trades on those
    dfg = df.groupby('sym')
    # apply filter to DataFrameGroupBy obj, which gives us another DataFrame
    # this will remove instruments that never have a non 0 last trade price
    # ie rm insts that do not trade
    df = dfg.filter(lambda x: x['LastTradePrice'].ne(0).any())
    df.to_csv(csv_out_path, columns=nd_consts.COLUMNS, index=False)
    # recreate the DataFrameGroupBy which will have only syms that have
    # LastTradePrice changes
    dfg = df.groupby('sym')
    # groupby approach
    for sym in dfg.groups:
        dfgsym = dfg.get_group(sym)
        dfgltp = dfgsym[dfgsym['LastTradePrice'] != 0.0]['LastTradePrice']
        ltp_diff = dfgltp.diff()
        logging.info(f'sym:{sym} count:{len(dfgltp)} min:{dfgltp.min()} max:{dfgltp.max()}')
    # yields 8 syms: NB Sep08 is a roll month, so the Dec08 contracts are in play too
    # https://www.econstats.com/fut/xeur_em2.htm
    return csv_base, csv_out_path

def write_parquet(csv_base, csv_in_path, target_dir):
    table = pa_csv.read_csv(csv_in_path)
    pq_out_path = os.path.join(target_dir, f'{csv_base}.parquet')
    pq.write_table(table, pq_out_path)
    return pq_out_path


list_source_data_files = lambda source_dir:[fname for fname in os.listdir(source_dir)
                                                    if fnmatch.fnmatch(fname, 'depth200809??.csv')]

if __name__ == '__main__':
    nd_utils.init_logging('pq_writer')
    source_files = list_source_data_files(nd_consts.DATA_SRC_DIR)
    logging.info(f'Source CSVs found in {nd_consts.DATA_SRC_DIR}')
    logging.info(f'{source_files}')
    target_dir = os.path.join(nd_consts.ND_ROOT_DIR, 'dat')
    logging.info(f'Clean CSVs and parquet will be in {target_dir}')
    for sf in source_files:
        csv_base, csv_out_path = clean_csv(nd_consts.DATA_SRC_DIR, target_dir, sf)
        logging.info(f'{csv_out_path} written')
        pq_out_path = write_parquet(csv_base, csv_out_path, target_dir)
        logging.info(f'{pq_out_path} written')
