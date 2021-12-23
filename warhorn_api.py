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
"""Warhorn GraphQL client."""

import collections.abc
import datetime
import logging
from typing import AsyncGenerator, Dict, Optional, Sequence, Tuple, Union

import pytz
from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport
from gql.transport.aiohttp import log as gql_logger


_QUERY = '''\
{{
  eventSessions(
      events: ["{slug}"],
      startsAfter: "{startsAfter}") {{
    nodes {{
      status
      scenario {{
        name
      }}
      scenarioOffering {{
        customName
      }}
      signupUrl
      uuid
      slot {{
        timezone
        startsAt
        endsAt
      }}
    }}
  }}
}}'''
_GQLNode = Optional[Union[str, Dict[str, '_GQLNode'], Sequence['_GQLNode']]]


class GraphNode:
    """Wrapper for GraphQL nodes that don't make the type system (or me) cry."""

    __slots__ = ('_node', )

    def __init__(self, node: _GQLNode) -> None:
        """Init a GraphNode.

        Args:
            node: GraphQL result node.
        """
        self._node: _GQLNode = node

    def path(self, *path: str) -> 'GraphNode':  # pylint: disable=used-before-assignment
        """Resolve a path under this node.

        Args:
            path: Sequence of key values to lookup.

        Returns:
            Node navigated to, or a None node if no such node existed.
        """
        node = self._node
        for p in path:
            if not isinstance(node, dict):
                return GraphNode(None)
            node = node.get(p)
        return GraphNode(node)

    @property
    def str(self) -> str:
        """Return the node as a string if it is one, else ''."""
        if isinstance(self._node, str):
            return self._node
        return ''

    @property
    def tuple(self) -> Tuple['GraphNode', ...]:
        """Return the node as a Tuple of GraphNodes if it's a sequence, else an empty tuple."""
        if isinstance(self._node, collections.abc.Sequence):
            return tuple(GraphNode(e) for e in self._node)
        return tuple()


def _strings_exists(*strings: str) -> bool:
    """Check that all of the strings exist and none of them are just the str 'None'."""
    for s in strings:
        if s in ('', 'None'):
            return False
    return True


class Game:
    """Game holds the key information about a Warhorn D&D session."""

    __slots__ = 'uuid', 'name', 'url', 'status', 'starts', 'ends'

    def __init__(self, session: GraphNode) -> None:
        """Init new Game.

        Args:
            session: Warhorn GraphQL session node to extract game data from.

        Throws:
            ValueError: in the event of key missing values, like a start time.
        """
        self.uuid: str = session.path('uuid').str
        """Warhorn session UUID."""
        self.name: str = (
            session.path('scenarioOffering', 'customName').str
            or session.path('scenario', 'name').str)
        """Game scenario name."""
        self.url = session.path('signupUrl').str
        """Warhorn session signup URL."""
        self.status: str = session.path('status').str
        """Warhorn session status. (e.g. PUBLISHED, DRAFT, CANCELED)"""

        starts = session.path('slot', 'startsAt').str
        ends = session.path('slot', 'endsAt').str
        tz_str = session.path('slot', 'timezone').str or 'US/Pacific'

        if not _strings_exists(self.uuid, self.name, self.status, self.url, starts, ends, tz_str):
            raise ValueError(f'Missing key values for game session: {session}')

        tz = pytz.timezone(tz_str)
        self.starts: datetime.datetime = datetime.datetime.fromisoformat(starts).astimezone(tz)
        """Game start time."""
        self.ends: datetime.datetime = datetime.datetime.fromisoformat(ends).astimezone(tz)
        """Game end time."""

    @property
    def time(self) -> str:
        """String describing game start/end time."""
        return f'{self.starts:%-I:%M%p} - {self.ends:%-I:%M%p %Z %b %d, %Y}'

    def __repr__(self) -> str:
        return f'Game("{self.name}", {self.time}, {self.status}, uuid: {self.uuid})'


class WarhornAPI:  # pylint: disable=too-few-public-methods
    """Warhorn client API."""

    def __init__(self, url: str='https://warhorn.net/graphql') -> None:
        """Init Warhorn client.

        Args:
            url: Warhorn GraphQL endpoint.
        """
        self._transport = AIOHTTPTransport(url=url)
        self._client = Client(transport=self._transport, fetch_schema_from_transport=False)
        gql_logger.setLevel(logging.WARNING)  # type: ignore

    async def get_games(
            self, slug: str, starts_after: Optional[datetime.datetime]=None
            ) -> AsyncGenerator[Game, None]:
        """Query Warhorn for games.

        Args:
            slug: identifying string for the warhorn event.
            starts_after: Only return Games beginning after this time.
        Returns:
            Generator of games.
        """
        starts_after = starts_after if starts_after else datetime.datetime.now()
        q = _QUERY.format(slug=slug, startsAfter=starts_after.isoformat())
        query = gql(q)
        result = GraphNode(await self._client.execute_async(query))  # type: ignore
        for session in result.path('eventSessions', 'nodes').tuple:
            status = session.path('status').str
            if status not in ('PUBLISHED', 'DRAFT', 'CANCELED'):
                logging.warn('Unexpected sessions status: %s', session)
            if status != 'PUBLISHED':
                continue
            yield Game(session)
