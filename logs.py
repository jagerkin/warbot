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
"""Standard logging setup."""
from datetime import datetime
import logging
import sys


class LogFormatter(logging.Formatter):
    """A logging formater that supports the datetime strftime options."""
    def formatTime(self, record, datefmt=None):  # type: ignore
        return datetime.fromtimestamp(record.created).astimezone().strftime(  # type: ignore
            datefmt or '%Y-%m-%d %H:%M:%S')  # type: ignore


def init(level:int=logging.INFO):
    """Setup root logger."""
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(
        LogFormatter(
            fmt='%(levelname)s %(asctime)s %(filename)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S.%f %Z(%z)'))
    logging.basicConfig(
        level=level,
        handlers=[handler])
