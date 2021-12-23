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
"""Load warbot configuration files."""

from typing import Set

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedSeq


class ChannelConfig:  # pylint: disable=too-few-public-methods
    """Discord channel configuration data."""

    __slots__ = 'guild_id', 'channel_id'

    def __init__(self, guild_id: str, channel_id: str):
        self.guild_id: int = int(guild_id)
        """Discord Guild ID."""
        self.channel_id: int = int(channel_id)
        """Discord Channel ID."""


class VenueConfig:  # pylint: disable=too-few-public-methods
    """Game venue configuration data."""

    __slots__ = 'name', 'slug', 'venue_embed', 'channel'

    def __init__(self, name: str, slug: str, venue_embed: str, channel: CommentedSeq):
        self.name: str = name
        """Venue name, not really used by WarBot."""
        self.slug: str = slug
        """Warhorn slug, last part of the event page path. e.g. https://warhorn.net/events/SLUG"""
        self.venue_embed: str = venue_embed
        """Markdown string to for announcement, usually includes link to the store and maps."""
        self.channel: Set[ChannelConfig] = {ChannelConfig(**c) for c in channel}  # type: ignore
        """Set of channels to post events to."""

    def __repr__(self) -> str:
        return f'config.VenueConfig(name="{self.name}", slug="{self.slug}", venue_embed="{self.venue_embed}", channel={self.channel})'


class Config:  # pylint: disable=too-few-public-methods
    """Top level WarBot config."""

    __slots__ = 'token', 'poll_interval', 'venue'

    def __init__(self, token: str, poll_interval: float, venue: CommentedSeq) -> None:
        self.token: str = token
        """Discord API Token, see https://discord.com/developers/applications/."""
        self.poll_interval: float = poll_interval
        """Warhorn polling interval."""
        self.venue: Set[VenueConfig] = {VenueConfig(**v) for v in venue}  # type: ignore
        """Game Venue information."""


def load(config_file: str) -> Config:
    """Load a WarBot config file and return a Config object for it."""
    try:
        yaml = YAML()
        with open(config_file, encoding='utf-8') as f:
            return Config(**yaml.load(f))  # type: ignore
    except Exception as e:
        raise RuntimeError(
            f'Could not load configuration from "{config_file}".') from e
