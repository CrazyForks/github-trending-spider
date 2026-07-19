# -*- coding: utf-8 -*-
"""
每日 AI 播客 API 测试。
"""

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import HTTPException
from fastapi.responses import FileResponse

sys.path.insert(0, ".")

from api import get_latest_podcast, get_podcast_audio, get_podcast_history  # noqa: E402


class TestPodcastApi(unittest.TestCase):
    def test_latest_empty(self):
        with patch("api.load_latest_podcast_metadata", return_value=None):
            result = get_latest_podcast()

        self.assertEqual(result["status"], "empty")
        self.assertIsNone(result["podcast"])

    def test_latest_success(self):
        metadata = {"date": "2026-07-19", "status": "success"}
        with patch("api.load_latest_podcast_metadata", return_value=metadata):
            result = get_latest_podcast()

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["podcast"], metadata)

    def test_history(self):
        podcasts = [{"date": "2026-07-19", "status": "success"}]
        with patch("api.list_podcast_history", return_value=podcasts):
            result = get_podcast_history()

        self.assertEqual(result["count"], 1)
        self.assertEqual(result["podcasts"], podcasts)

    def test_audio_invalid_date_returns_400(self):
        with self.assertRaises(HTTPException) as ctx:
            get_podcast_audio("../../etc/passwd")

        self.assertEqual(ctx.exception.status_code, 400)

    def test_audio_missing_returns_404(self):
        with patch("api.get_podcast_audio_file", return_value=None):
            with self.assertRaises(HTTPException) as ctx:
                get_podcast_audio("2026-07-19")

        self.assertEqual(ctx.exception.status_code, 404)

    def test_audio_returns_file_response(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            audio_path = Path(temp_dir) / "podcast.mp3"
            audio_path.write_bytes(b"mp3")
            with patch("api.get_podcast_audio_file", return_value=audio_path):
                response = get_podcast_audio("2026-07-19")

        self.assertIsInstance(response, FileResponse)
        self.assertEqual(response.media_type, "audio/mpeg")


if __name__ == "__main__":
    unittest.main()
