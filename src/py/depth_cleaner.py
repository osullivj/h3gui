# builtin
import csv
from datetime import time, datetime
import os.path
# 3rd pty
import pandas as pd
# h3gui
import h3consts

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
COLUMNS=dict(sym=str, SeqNo=int, FeedSequenceId=int, time=time, FeedCaptureTS=time,
             StatusCode=str, StatusText=str, Explicit=str,
             TradingStatus=int, InstrumentStatus=int, LastTradeTime=datetime,
             LastTradePrice=float, LastTradeSize=int, HighPrice=float,
             LowPrice=float, OpenPrice=float, ClosePrice=float, Volume=int,
             LastTradeSequence=int, State=int, TranDateTime=datetime,
             AskQty0=int, AskPrice0=float,
             AskQty1=int, AskPrice1=float,
             AskQty2=int, AskPrice2=float,
             AskQty3=int, AskPrice3=float,
             AskQty4=int, AskPrice4=float,
             AskQty5=int, AskPrice5=float,
             BidQty0=int, BidPrice0=float,
             BidQty1=int, BidPrice1=float,
             BidQty2=int, BidPrice2=float,
             BidQty3=int, BidPrice3=float,
             BidQty4=int, BidPrice4=float,
             BidQty5=int, BidPrice5=float,
             )

TIME_FMT='%H:%M:%S.%f'
DATETIME_FMT='%Y-%m-%d %H:%M:%S.%f'
DATE_FORMATS = dict(time=TIME_FMT, FeedCaptureTS=TIME_FMT, LastTradeTime=DATETIME_FMT, TranDateTime=DATETIME_FMT)
TIME_FIELDS = ['time', 'FeedCaptureTS']

strip_hms = lambda ts: pd.Timestamp(year=ts.year, month=ts.month, day=ts.day)

INSTRUMENTS = {
    2247907: 'FGBMU8', # count:16559 min:103.14 max:103.34
    2247935: 'FGBMZ8', # count:6489 min:103.46 max:103.665
    2247988: 'FGBXZ8', # count:10917 min:113.5 max:114.29
    2247993: 'FGBSU8', # count:532 min:91.2 max:91.52
    2248001: 'FGBSZ8', # count:1823 min:90.6 max:91.72
    2248009: 'FGBXU8', # count:21792 min:114.11 max:114.63
    2248010: 'FGBLU8', # count:19557 min:108.13 max:108.595
    2248028: 'FGBLZ8', # count:9423 min:108.355 max:108.81
}

def load_depth_pd(csv_file):
    csv_path = os.path.join(h3consts.H3ROOT_DIR, 'dat', csv_file)
    csv_base, csv_ext = os.path.splitext(csv_file)
    csv_out_path = os.path.join(h3consts.H3ROOT_DIR, 'dat', f'{csv_base}_pd{csv_ext}')
    cols = list(COLUMNS.keys())
    df = pd.read_csv(csv_path,
                     usecols=cols, parse_dates=list(DATE_FORMATS.keys()), date_format=DATE_FORMATS)
    # get a base date from LastTradeTime col for correct date on
    # time cols when they become datetime. NB SOD LastTradeTime
    # will have H:M:S as 00:00:00 but time will not, so we just
    # extract the days and ignore HH:MM:SS
    last_trade_ts = df.iloc[-1]['LastTradeTime']
    last_ts = df.iloc[-1]['time']
    base_delta = strip_hms(last_trade_ts) - strip_hms(last_ts)
    df['time'] += base_delta
    df['FeedCaptureTS'] += base_delta
    df['sym'] = df['sym'].str[2:9]
    df['sym'] = df['sym'].astype(int)
    # put them in feed sequence so we can see where eg last trade price changes
    df = df.sort_values(by=['FeedSequenceId'])

    print('== df.dtypes')
    print(df.dtypes)
    print(df.shape)
    # group by symbol, and filter out any symbols where
    # LastTradePrice is always 0.0: no trades on those
    dfg = df.groupby('sym')
    # apply filter to DataFrameGroupBy obj, which gives us another DataFrame
    # this will remove instruments that never have a non 0 last trade price
    # ie rm insts that do not trade
    df = dfg.filter(lambda x: x['LastTradePrice'].ne(0).any())
    df.to_csv(csv_out_path, columns=cols, index=False)
    # recreate the DataFrameGroupBy which will have only syms that have
    # LastTradePrice changes
    dfg = df.groupby('sym')
    # groupby approach
    for sym in dfg.groups:
        dfgsym = dfg.get_group(sym)
        dfgltp = dfgsym[dfgsym['LastTradePrice'] != 0.0]['LastTradePrice']
        ltp_diff = dfgltp.diff()
        print(f'sym:{sym} count:{len(dfgltp)} min:{dfgltp.min()} max:{dfgltp.max()}')

    # yields 8 syms: NB Sep08 is a roll month, so the Dec08 contracts are in play too
    # https://www.econstats.com/fut/xeur_em2.htm


if __name__ == '__main__':
    load_depth_pd('depth20080901.csv')
