# imgui application as imported by http3_server.py


import datetime
import logging
import os
from urllib.parse import urlencode

from starlette.applications import Starlette
from starlette.responses import PlainTextResponse, Response
from starlette.routing import Mount, Route, WebSocketRoute
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates
from starlette.types import Receive, Scope, Send
from starlette.websockets import WebSocketDisconnect

# override standard single dir plus py pkg behaviour of StaticFiles
# https://github.com/encode/starlette/issues/625

class H3StaticFiles(StaticFiles):
    def __init__(self, *, directories: list[os.PathLike] | None = None,
            html: bool = False, check_dir: bool = True, follow_symlink: bool = False):
        # base class ctor will call our overriden get_directories(), so
        # define self.dir_list first
        self.dir_list = directories
        super().__init__(directory=directories[0], packages=None, html=html,
                            check_dir=check_dir, follow_symlink=follow_symlink)

    def get_directories(self,
        directory: os.PathLike | None = None,
        packages: list[str | tuple[str, str]] | None = None,
    ) -> list[os.PathLike]:
        return self.dir_list

    def lookup_path(self, path: str) -> tuple[str, os.stat_result | None]:
        # same as base class impl, but we discard the os.path.commonpath
        # check, and replace with a file existence check since we're
        # searching all of self.dir_list for hits...
        for directory in self.all_directories:
            joined_path = os.path.join(directory, path)
            if self.follow_symlink:
                full_path = os.path.abspath(joined_path)
            else:
                full_path = os.path.realpath(joined_path)
            if not os.path.exists(full_path):
                # not in this directory; skip to next iteration
                logging.debug(f'lookup_path:{path} NOT {full_path}')
                continue
            try:
                logging.debug(f'lookup_path:{path} IS {full_path}')
                return full_path, os.stat(full_path)
            except (FileNotFoundError, NotADirectoryError):
                continue
        return "", None


class Imgui(object):
    def __init__(self, static_dir):
        # imgui-jswt/example is the only dir with .html
        template_dir = os.path.join(static_dir, 'example')
        self.templates = Jinja2Templates(directory=template_dir)
        # when imgui-jswt requests URLs they may be relative to
        # to imgui-jswt or imgui-jswt/build; must be something I
        # don't understand about npm's http-server as the paths
        # requested change when npm servers...
        dir_list = [static_dir, template_dir]
        self.starlette = Starlette(routes=[
            Route("/", self.homepage, methods=['GET', 'CONNECT']),
            Mount("/", H3StaticFiles(directories=dir_list, html=True)),
        ])

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "webtransport":
            await self.wt(scope, receive, send)
        else:
            await self.starlette(scope, receive, send)

    async def homepage(self, request):
        # server push style sheet (aioquic/examples/htdocs/style.css)
        # to speed page load
        # await request.send_push_promise("/style.css")
        return self.templates.TemplateResponse("index.html", {"request": request})

    async def wt(self, scope: Scope, receive: Receive, send: Send) -> None:
        # accept connection
        message = await receive()
        assert message["type"] == "webtransport.connect"
        await send({"type": "webtransport.accept"})

        # echo back received data
        while True:
            message = await receive()
            if message["type"] == "webtransport.datagram.receive":
                await send(
                    {
                        "data": message["data"],
                        "type": "webtransport.datagram.send",
                    }
                )
            elif message["type"] == "webtransport.stream.receive":
                await send(
                    {
                        "data": message["data"],
                        "stream": message["stream"],
                        "type": "webtransport.stream.send",
                    }
                )
