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
"""Parse flags and arguments for the application and expose them similar to absl.flags."""
import argparse


def init() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bot that posts Warhorn game listings to Discord channels.")
    parser.add_argument(
            '--debug', default=False, type=bool, action=argparse.BooleanOptionalAction,
            help='Enable dev debugging.')
    parser.add_argument(
            '--dry_run', default=True, type=bool, action=argparse.BooleanOptionalAction,
            help='Make no DB changes or Discord posts.')
    parser.add_argument('--db', default='warbot.db', help='WarBot state data.')
    parser.add_argument('--config', default='warbot.conf', help='WarBot configuration file path.')
    return parser.parse_args()

