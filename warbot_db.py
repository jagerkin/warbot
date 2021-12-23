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
"""WarBot database storage."""

import ast
import logging
import os
import pathlib
import shutil
from typing import Dict, Tuple

from aiofile import async_open  # type: ignore
from prettyprinter import pformat  # type: ignore


class WarBotDB:
    """WarBot Database, stores posted games as a text dictionary literal..

    This is slow as dirt compared to a real DB of nearly any kind, but it also
    seems sufficient for my purposes and is very light on the memory, which is
    good because I run this on an rpi cluster.

    Args:
        db_file: path to database file
    
    Raises:
        RuntimeError: When there's danger of overwritting previous run data.
    """

    __slots__ = '_db_file', '_tmp_db_file', '_db', '_changed', '_dry_run'

    def __init__(self, db_file: str, dry_run:bool=True) -> None:
        self._db_file: str = db_file
        self._tmp_db_file: str = self._db_file + '.saving'
        self._db: Dict[Tuple[str, Tuple[int, int]], Dict[str, str]] = {}
        self._changed: bool = False
        self._dry_run: bool = dry_run
        if os.path.exists(self._tmp_db_file):
            # Do we really care this much? A couple repeat posts, let this stomp
            # it, and we get on with our lives...
            msg = f'Temp DB file "{self._tmp_db_file}" already exists. Manually recover or delete.'
            logging.fatal(msg)
            raise RuntimeError(msg)

    def __len__(self) -> int:
        return len(self._db)

    def add_notification(  # pylint: disable=too-many-arguments
            self, slug: str, guild_id: int, channel_id: int, uuid: str, name: str) -> bool:
        """Add a notification to the database.

        Args:
            slug: Warhorn event slug.
            guild_id: Discord guild ID being posted to.
            channel_id: Discord channel ID being posted to.
            uuid: Warhorn unique ID for the session.
            name: Warhorn session name, mainly for debugging the DB by hand later.

        Returns:
            True if this request is not already in the DB, otherwise false.
        """
        feed = (slug, (guild_id, channel_id))
        if feed not in self._db:
            self._db[feed] = {}
            self._changed = True
        if uuid not in self._db[feed]:
            self._db[feed][uuid] = name
            self._changed = True
            logging.info('New entry: %s (%s) -> %s', name, uuid, channel_id)
            return True
        return False

    async def load(self) -> None:
        """Load the database from file."""
        if os.path.exists(self._db_file):
            async with async_open(self._db_file, 'r') as f:
                self._db.update(ast.literal_eval(await f.read()))
        else:
            logging.warn('DB file %s does not exist.', self._db_file)
        self._changed = False

    async def save(self) -> None:
        """Save the database to file if there are changes.

        Writes to a temp file then renames it once the write is complete to
        prevent corruption if interrupted mid write."""
        if self._changed:
            if self._dry_run:
                logging.info(
                        'Dry-Run, faking saving changes to DB to %s', self._db_file)
                self._changed = False
                return
            logging.debug('Saving DB to %s', self._db_file)
            tmp_save = pathlib.Path(str(self._db_file) + '.saving')
            async with async_open(tmp_save, 'w') as f:
                await f.write(pformat(self._db, indent=2, width=200, ribbon_width=200) + '\n')
            shutil.move(tmp_save, self._db_file)
            self._changed = False
