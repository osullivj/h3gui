import os.path

CHROME_EXE = r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe'
B64_RSA_KEY = 'BSQJ0jkQ7wwhR7KvPZ+DSNk2XTZ/MS6xCbo9qu++VdQ='
CHROME_LAUNCH_FMT = (
    '%(exe)s --user-data-dir=%(user_data_dir)s --no-proxy-server '
    '--enable-quic --origin-to-force-quic-on=localhost:4433 '
    '--ignore-certificate-errors-spki-list=%(b64_rsa_key)s '
    'https://googlechrome.github.io/samples/webtransport/client.html'
)

CHROME_LAUNCH_DICT = dict(exe=CHROME_EXE, user_data_dir='', b64_rsa_key=B64_RSA_KEY)

H3ROOT_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..'))
