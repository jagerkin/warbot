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
import unittest
from unittest import mock

import config
import hikari
from warbot import WarBot
from warhorn_api import GraphNode, Game, WarhornAPI
from warbot_db import WarBotDB


class WarBotTest(unittest.TestCase):
    def test_polling_loop(self):
        chan = config.ChannelConfig(guild_id='8675', channel_id='309')
        venue = config.VenueConfig(
            name='Test Venue',
            slug='test-event',
            venue_embed='Brought to you by a unit test',
            channel=tuple())  # type: ignore
        venue.channel = {chan}
        conf = config.Config(
            token='',
            poll_interval=0.0,
            venue=tuple())  # type: ignore
        conf.venue = {venue}

        db = mock.create_autospec(WarBotDB)
        db.add_notification.return_value = True

        game = Game(GraphNode({
            'uuid': 'xxxx-yyy-zzzzzz',
            'scenarioOffering': {
                'customName': 'The Custom Game',
            },
            'scenario': {
                'name': 'The Base Game',
            },
            'signupUrl': 'https://wh/xxxx-yyy-zzzzz/signup',
            'status': 'PUBLISHED',
            'slot': {
                'startsAt': '2021-12-25T12:00:00.000000',
                'endsAt': '2021-12-25T16:00:00.000000',
                'timezone': 'US/Pacific',
            },
        }))
        warhorn_api = mock.create_autospec(WarhornAPI)
        warhorn_api.get_games.return_value.__aiter__.return_value = [game]
        
        bot = WarBot(conf, db, warhorn_api, dry_run=False, debug=False)
        hikari_bot = mock.create_autospec(hikari.GatewayBot)
        send = mock.AsyncMock()
        hikari_bot.cache.get_guild_channel.return_value.send = send
        bot._bot = hikari_bot  # pyright: reportPrivateUsage=false

        asyncio.run(bot.polling_loop(run_once=True))

        send.assert_called_once()
        self.assertEqual(1, len(send.call_args[0]))
        embed = send.call_args[0][0]
        self.assertEqual('The Custom Game', embed.title)
        self.assertEqual('Brought to you by a unit test', embed.description)


if __name__ == '__main__':
    unittest.main()
