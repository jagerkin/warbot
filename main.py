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
"""WarBot monitors the Warhorn API and posts new games to Discord.

WarBot polls Warhorn on a configurable interval, it can load data from multiple
events and output each event to a set of channels.  Currently WarBot takes no
commands via Discord and is manually invited, offering WarBot as a service is
an option if it gets enough users, but for now, if you want to ride on the
authors service, file an issue against this project requesting it.
"""

import logging
import sys

from argparse import Namespace

import args
import config
import logs
from warbot import WarBot
from warhorn_api import WarhornAPI
from warbot_db import WarBotDB


def main(flags: Namespace) -> None:
    """Initialize and start WarBot."""
    logging.info(f'Dry Run: {flags.dry_run}.')
    try:
        # Purely an asyncio speedup. Load and forget.
        import uvloop  # pylint: disable=import-outside-toplevel
        uvloop.install()
        logging.info("uvloop initalized.")
    except ModuleNotFoundError:
        logging.info("uvloop not available.")

    conf = config.load(flags.config)
    bot = WarBot(
        conf,
        WarBotDB(flags.db, dry_run=flags.dry_run),
        WarhornAPI(token=conf.warhorn_token),
        dry_run=flags.dry_run,
        debug=flags.debug)
    bot.run()


if __name__ == '__main__':
    flags = args.init()
    logs.init(logging.DEBUG if flags.debug else logging.INFO)
    logging.info(f'WarBot starting.')
    for i, arg in enumerate(sys.argv):
        logging.info(f'arg[{i}]={arg}')
    main(flags)
