import os.path

# Env config
CHROME_EXE = r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe'
# B64_RSA_KEY was extracted from aioquic/tests/ssl_cert.pem
B64_RSA_KEY = 'BSQJ0jkQ7wwhR7KvPZ+DSNk2XTZ/MS6xCbo9qu++VdQ='

# Notes on Chrome launch flags...
# https://www.chromium.org/quic/playing-with-quic/
# https://github.com/GoogleChrome/samples/blob/gh-pages/webtransport/webtransport_server.py
CHROME_LAUNCH_FMT = (
    '%(exe)s --user-data-dir=%(user_data_dir)s --no-proxy-server '
    # logging into user_data_dir: comment out to restore logging in devtools
    # '--enable-logging --v=1 '
    '--auto-open-devtools-for-tabs '
    '--enable-quic --origin-to-force-quic-on=localhost:4433 '
    '--ignore-cerificate-errors '
    '--ignore-certificate-errors-spki-list=%(b64_rsa_key)s '
    'https://localhost:4433'
)

CHROME_LAUNCH_DICT = dict(exe=CHROME_EXE, user_data_dir='', b64_rsa_key=B64_RSA_KEY)

H3ROOT_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
EXT_DATA_SRC_DIR = 'c:\\osullivj\\dat\\depth'

# Data config
INSTRUMENTS = {
    7907: 'FGBMU8', # count:16559 min:103.14 max:103.34
    7935: 'FGBMZ8', # count:6489 min:103.46 max:103.665
    7988: 'FGBXZ8', # count:10917 min:113.5 max:114.29
    7993: 'FGBSU8', # count:532 min:91.2 max:91.52
    8001: 'FGBSZ8', # count:1823 min:90.6 max:91.72
    8009: 'FGBXU8', # count:21792 min:114.11 max:114.63
    8010: 'FGBLU8', # count:19557 min:108.13 max:108.595
    8028: 'FGBLZ8', # count:9423 min:108.355 max:108.81
}
RINSTRUMENTS=dict((v,k) for k,v in INSTRUMENTS.items())

# cols for csvs aggregated across instruments
AGG_COLUMNS=['sym', 'SeqNo', 'FeedSequenceId', 'time', 'FeedCaptureTS',
             'StatusCode', 'StatusText', 'Explicit',
             'TradingStatus', 'InstrumentStatus', 'LastTradeTime',
             'LastTradePrice', 'LastTradeSize', 'HighPrice',
             'LowPrice', 'OpenPrice', 'ClosePrice', 'Volume',
             'LastTradeSequence', 'State', 'TranDateTime',
             'AskQty0', 'AskPrice0',
             'AskQty1', 'AskPrice1',
             'AskQty2', 'AskPrice2',
             'AskQty3', 'AskPrice3',
             'AskQty4', 'AskPrice4',
             'AskQty5', 'AskPrice5',
             'BidQty0', 'BidPrice0',
             'BidQty1', 'BidPrice1',
             'BidQty2', 'BidPrice2',
             'BidQty3', 'BidPrice3',
             'BidQty4', 'BidPrice4',
             'BidQty5', 'BidPrice5',
]

COLUMNS=['date', 'time', 'sym', 'SeqNo', 'FeedSequenceId', 'FeedCaptureTS',
             'LastTradeTime',
             'LastTradePrice', 'LastTradeSize', 'HighPrice',
             'LowPrice', 'Volume',
             'LastTradeSequence', 'TranDateTime',
             'AskQty1', 'AskPrice1',
             'AskQty2', 'AskPrice2',
             'AskQty3', 'AskPrice3',
             'AskQty4', 'AskPrice4',
             'AskQty5', 'AskPrice5',
             'BidQty1', 'BidPrice1',
             'BidQty2', 'BidPrice2',
             'BidQty3', 'BidPrice3',
             'BidQty4', 'BidPrice4',
             'BidQty5', 'BidPrice5',
]

DATE_FIELDS = {'TS': ['date', 'time'], 'CaptureTS': ['date', 'FeedCaptureTS']},
# mydatetime will contain my_date and my_time separated by a single space
DATE_FORMAT = {'TS': '%Y-%m-%d %H:%M:%S.%f'}

TIME_FMT='%H:%M:%S.%f'
DATETIME_FMT='%Y-%m-%d %H:%M:%S.%f'
RAW_DATE_FORMATS = dict(time=TIME_FMT, FeedCaptureTS=TIME_FMT, LastTradeTime=DATETIME_FMT, TranDateTime=DATETIME_FMT)
CLEAN_DATE_FORMATS = dict(time=DATETIME_FMT, FeedCaptureTS=DATETIME_FMT, LastTradeTime=DATETIME_FMT, TranDateTime=DATETIME_FMT)