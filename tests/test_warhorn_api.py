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
import asyncio
from datetime import datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler
import os
import shutil
import unittest

from unittest_utils import TestWebServer
import warhorn_api


test_dir = os.path.dirname(os.path.realpath(__file__))


class MockWarhorn(BaseHTTPRequestHandler):
    """Mock Warhorn GraphQL handler for use with ut_utils.TestWebServer."""
    def do_POST(self):
        req_text = self.rfile.read(60)
        filename = 'schema.json' if b'__schema' in req_text else 'event_data.json'
        with open(os.path.join(test_dir, filename), 'rb') as f:
            fs = os.fstat(f.fileno())
            self.send_response(HTTPStatus.OK)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.send_header('Content-length', str(fs[6]))
            self.end_headers()
            shutil.copyfileobj(f, self.wfile)


class WarhornAPI_Test(unittest.TestCase):
    @staticmethod
    async def _async_query_games():
        with TestWebServer(MockWarhorn) as srv:
            client = warhorn_api.WarhornAPI(url=f'http://localhost:{srv.port}')
            games = [g async for g in client.get_games(
                'test-event',
                starts_after=datetime.fromisoformat('1997-08-29T02:14:00'))]
            return games

    def test_get_games(self):
        games = asyncio.run(self._async_query_games())
        self.assertEqual(1, len(games))  # This is checking that it filtered out the DRAFT and CANCELED games.
        game = games[0]
        # Test session data extraction
        self.assertEqual(game.uuid, '06df3e16-72fc-4752-8dce-3f04144c1247')
        self.assertEqual(game.name, 'DDAL05-01 Treasure of the Broken Hoard')
        self.assertEqual(game.time, '2:00PM - 8:00PM PST Dec 24, 2021')
        self.assertEqual(game.status, 'PUBLISHED')
        self.assertEqual(game.url, 'https://warhorn.net/events/test-event/schedule/sessions/06df3e16-72fc-4752-8dce-3f04144c1247')


if __name__ == '__main__':
    unittest.main()
