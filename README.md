# h3gui
Quic based browser GUI, based on aioquic

## Integrating aioquic/examples/http3_server.py with Chrome
This [Chrome sample](https://googlechrome.github.io/samples/webtransport/client.html) fails
the handshake with http3_server.py. Fixes needed to make them work together...

### Extract RSA key from aioquic/tests/ssl_cert.pem
Chrome will not recognise a self signed cert from the server, so we have
to use the cert supplied by aioquic. See sh/extract_finger.bat for details.
We use the base64 encoded key as a command line param when launching chrome.

### Chrome launcher
src/py/chrome_launcher.py starts Chrome like so...
`   chrome --user-data-dir=/tmp/chrome-profile --no-proxy-server --enable-quic
        --ignore-cerificate-errors
        --origin-to-force-quic-on=localhost:4433 
        --ignore-certificate-errors-spki-list=<b64key>
        https://googlechrome.github.io/samples/webtransport/client.html`

Note that chrome_launcher.py creates a new user-data-dir for each launch.

### CONNECT
Chrome sends CONNECT as the http method, and aioquic/examples/http3_client.py
send GET. So in aioquic/examples/demo.py, we specify CONNECT in the Starlette
Route...
`        Route("/", homepage, methods=['GET', 'CONNECT']),`

### starlette/routing.py
Line 759 in Router.app() asserts scope['type'] must be one of 
("http", "websocket", "lifespan"), but Chrome sends "webtransport",
so we comment out the assertion.

### app method
In aioquic/examples/demo.py:app() we remove the check on the scope['path']
