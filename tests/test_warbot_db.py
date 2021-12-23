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
import os
import unittest

import testfixtures  # type: ignore

import warbot_db


test_dir = os.path.dirname(os.path.realpath(__file__))


class WarBotDB_Test(unittest.TestCase):
    def test_anti_stomping(self):
        test_db_file = os.path.join(test_dir, 'db_anti_stomp_test.db')
        test_tmp_db_file = test_db_file + '.saving'
        with open(test_tmp_db_file, 'w'):
            pass
        with testfixtures.LogCapture() as lc:
            with self.assertRaises(RuntimeError):
                warbot_db.WarBotDB(test_db_file)
            self.assertEqual(
                'root CRITICAL\n'
                '  Temp DB file "/home/olson/src/warbot/tests/db_anti_stomp_test.db.saving" '
                'already exists. Manually recover or delete.', str(lc))
        os.remove(test_tmp_db_file)

    def test_load(self):
        test_db_file = os.path.join(test_dir, 'db_load_test.db')
        db = warbot_db.WarBotDB(test_db_file)
        self.assertEqual(0, len(db))
        asyncio.run(db.load())
        self.assertEqual(1, len(db))
        self.assertFalse(db.add_notification('test-event', 12345, 67890, 'foo-bar-str', 'A very fun game.'))

    def test_save(self):
        test_db_file = os.path.join(test_dir, 'db_save_test.db')
        db = warbot_db.WarBotDB(test_db_file, dry_run=False)
        self.assertEqual(0, len(db))
        self.assertTrue(db.add_notification('test-event', 12345, 67890, 'foo-bar-str', 'A very fun game.'))
        self.assertEqual(1, len(db))
        asyncio.run(db.save())
        self.assertTrue(os.path.exists(test_db_file))
        os.remove(test_db_file)
        # Save does nothing unless there are changes.
        asyncio.run(db.save())
        self.assertFalse(os.path.exists(test_db_file))

    def test_add_notification(self):
        test_db_file = os.path.join(test_dir, 'db_load_test.db')
        db = warbot_db.WarBotDB(test_db_file, dry_run=True)
        self.assertEqual(0, len(db))
        self.assertTrue(db.add_notification('test-event', 12345, 67890, 'foo-bar-str', 'A very fun game.'))
        self.assertEqual(1, len(db))
        self.assertFalse(db.add_notification('test-event', 12345, 67890, 'foo-bar-str', 'A very fun game.'))
        self.assertEqual(1, len(db))


if __name__ == '__main__':
    unittest.main()
