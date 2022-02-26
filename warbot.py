# Copyright 2020-2021 Michael Olson
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
"""WarBot hikari bot."""

import asyncio
import logging
from typing import Optional

import hikari
from hikari.events import StartedEvent
from gql.transport.exceptions import TransportServerError

from config import Config, ChannelConfig, VenueConfig
from warhorn_api import WarhornAPI, Game
from warbot_db import WarBotDB


class WarBot:  # pylint: disable=too-few-public-methods
    """WarBot initializes hikari, handles events, and runs the main bot loop.

    Args:
        config: Bot configuration.
        db: Database to store posted games.
        warhorn: Warhorn client to query for games.
    """

    __slots__ = '_bot', '_config', '_db', '_warhorn', '_dry_run', '_debug'

    def __init__(
        self,
        config: Config,
        db: WarBotDB,
        warhorn: WarhornAPI,
        dry_run:bool=True,
        debug:bool=True) -> None:
        self._bot: Optional[hikari.GatewayBot] = None
        self._config: Config = config
        self._db: WarBotDB = db
        self._dry_run: bool = dry_run
        self._debug: bool = debug
        self._warhorn: WarhornAPI = warhorn
        logging.debug('Warhorn Token: %s', self._config.warhorn_token)
        logging.debug('Discord Token: %s', self._config.discord_token)

    async def _post_game(self, ch: ChannelConfig, venue: VenueConfig, game: Game) -> None:
        """Construct the Discord announcement embed and post it."""
        logging.info(
            f'Sending notice to {ch.guild_id}/{ch.channel_id} for "{game.name}".')
        embed = hikari.Embed(
            title=game.name,
            description=venue.venue_embed,
            color=hikari.Color(0x71368a),  # Purple
        )
        embed.add_field(name='Game Time', value=game.time, inline=False)
        embed.add_field(name='Sign up', value=game.url, inline=False)
        if self._dry_run:
            logging.info('Dry-Run, notification: %s', embed)
            return
        await self._bot.cache.get_guild_channel(ch.channel_id).send(embed)  # type: ignore

    async def polling_loop(self, run_once:bool=False) -> None:
        """Periodically query Warhorn for new games."""
        await self._db.load()
        logging.info('Staring Warhorn polling.')
        run_loop = True
        while run_loop:
            logging.info('Polling for new games.')
            run_loop = not run_once
            try:
                for venue in self._config.venue:
                    logging.info('Polling venue: %s', venue.slug)
                    async for game in self._warhorn.get_games(venue.slug):
                        for ch in venue.channel:
                            if self._db.add_notification(
                                    venue.slug, ch.guild_id, ch.channel_id, game.uuid, game.name):
                                await self._post_game(ch, venue, game)
            except TransportServerError:
                logging.exception("Error getting games, try again later.")
            await self._db.save()
            await asyncio.sleep(self._config.poll_interval)

    async def _on_started(self, _: StartedEvent) -> None:
        """Launch background tasks (the polling loop) and the connection to discord is up."""
        logging.info("StartedEvent, we should be connected.")
        asyncio.get_running_loop().create_task(self.polling_loop())

    def run(self) -> None:
        """Execute the main bot, does not return until terminated."""
        self._bot = hikari.GatewayBot(self._config.discord_token)
        self._bot.event_manager.subscribe(StartedEvent, self._on_started)
        self._bot.run(asyncio_debug=self._debug)
