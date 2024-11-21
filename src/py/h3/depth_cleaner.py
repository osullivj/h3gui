# builtin
import csv
from datetime import time, datetime
import logging
import os.path
# 3rd pty
import pandas as pd
# h3gui
import h3consts
import h3utils

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



def load_depth_pd(csv_file):
    csv_path = os.path.join(h3consts.H3ROOT_DIR, 'dat', csv_file)
    csv_base, csv_ext = os.path.splitext(csv_file)
    csv_out_path = os.path.join(h3consts.H3ROOT_DIR, 'dat', f'{csv_base}_pd{csv_ext}')
    df = pd.read_csv(csv_path, usecols=h3consts.COLUMNS,
                     parse_dates=list(h3consts.RAW_DATE_FORMATS.keys()),
                     date_format=h3consts.RAW_DATE_FORMATS)
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
    df.to_csv(csv_out_path, columns=h3consts.COLUMNS, index=False)
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


if __name__ == '__main__':
    h3utils.init_logging('depth_cleaner')
    load_depth_pd('depth20080901.csv')
