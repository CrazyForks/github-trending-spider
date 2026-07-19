# -*- coding: utf-8 -*-
"""
历史归档 API 层测试。
"""

import sys
import unittest
from unittest.mock import patch

from fastapi import HTTPException

sys.path.insert(0, ".")

from api import get_history_source, get_latest_source, get_rss_feed  # noqa: E402


class TestHistoryApi(unittest.TestCase):
    def test_unknown_source_returns_404(self):
        with self.assertRaises(HTTPException) as ctx:
            get_history_source("unknown-source", "2026-06-06")

        self.assertEqual(ctx.exception.status_code, 404)

    def test_disabled_linux_do_latest_returns_404(self):
        with self.assertRaises(HTTPException) as ctx:
            get_latest_source("linux-do")

        self.assertEqual(ctx.exception.status_code, 404)

    def test_disabled_linux_do_history_returns_404(self):
        with self.assertRaises(HTTPException) as ctx:
            get_history_source("linux-do", "2026-06-06")

        self.assertEqual(ctx.exception.status_code, 404)

    def test_rss_does_not_load_disabled_linux_do_source(self):
        with patch("api.load_latest_snapshot", return_value=(None, "empty")) as loader:
            response = get_rss_feed()

        loaded_source_ids = [call.args[0] for call in loader.call_args_list]
        self.assertNotIn("linux-do", loaded_source_ids)
        self.assertNotIn("Linux.do", response.body.decode("utf-8"))

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
