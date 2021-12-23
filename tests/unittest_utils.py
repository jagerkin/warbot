# Copyright 2021 Michael Olson
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     https://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Unittest utilities like quick web servers, unified diff asserts, special TestCase classes, ..."""
from http.server import BaseHTTPRequestHandler, HTTPServer
import contextlib
from threading import Thread
from typing import Type


class TestWebServer(contextlib.AbstractContextManager):
    """Fire up a quick and dirty web server in another thread."""
    def __init__(self, handler: Type[BaseHTTPRequestHandler]) -> None:
        self._server = HTTPServer(('localhost', 0), handler)
        self.port: int = self._server.server_port
        self._server_thread = Thread(target=self._server.serve_forever)
        self._server_thread.daemon = True
        self._server_thread.start()

    def __enter__(self) -> 'TestWebServer':
        return self
    
    def __exit__(self, *args, **kwargs):  # type: ignore
        self.shutdown()
        return super().__exit__(*args, **kwargs)  # type: ignore

    def shutdown(self) -> None:
        self._server.shutdown()
        self._server.socket.close()
