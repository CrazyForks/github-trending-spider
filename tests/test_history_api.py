# -*- coding: utf-8 -*-
"""
历史归档 API 层测试。
"""

import sys
import unittest

from fastapi import HTTPException

sys.path.insert(0, ".")

from api import get_history_source  # noqa: E402


class TestHistoryApi(unittest.TestCase):
    def test_unknown_source_returns_404(self):
        with self.assertRaises(HTTPException) as ctx:
            get_history_source("unknown-source", "2026-06-06")

        self.assertEqual(ctx.exception.status_code, 404)

    def test_invalid_date_returns_400(self):
        with self.assertRaises(HTTPException) as ctx:
            get_history_source("github-daily", "../../etc/passwd")

        self.assertEqual(ctx.exception.status_code, 400)

    def test_empty_archive_returns_empty_items(self):
        result = get_history_source("github-daily", "1900-01-01")

        self.assertEqual(result["served_from"], "empty")
        self.assertEqual(result["batch_file"], "")
        self.assertEqual(result["item_count"], 0)
        self.assertEqual(result["items"], [])


if __name__ == "__main__":
    unittest.main()
