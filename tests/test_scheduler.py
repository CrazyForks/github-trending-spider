# -*- coding: utf-8 -*-
"""
内置调度器测试。
"""

import sys
import unittest

sys.path.insert(0, ".")

from scheduler import parse_schedule_times  # noqa: E402


class TestScheduler(unittest.TestCase):
    def test_parse_podcast_schedule_time(self):
        self.assertEqual(parse_schedule_times("02:30"), [(2, 30)])

    def test_parse_multiple_schedule_times(self):
        self.assertEqual(
            parse_schedule_times("23:50,07:50,15:50"),
            [(7, 50), (15, 50), (23, 50)],
        )

    def test_invalid_schedule_time(self):
        with self.assertRaises(ValueError):
            parse_schedule_times("25:00")


if __name__ == "__main__":
    unittest.main()
