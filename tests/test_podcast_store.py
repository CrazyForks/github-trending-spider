# -*- coding: utf-8 -*-
"""
每日 AI 播客存储测试。
"""

import json
import sys
import tempfile
import unittest
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, ".")

from podcast_store import (  # noqa: E402
    acquire_podcast_lock,
    get_podcast_audio_file,
    has_successful_podcast,
    is_valid_podcast_date,
    list_podcast_history,
    load_latest_podcast_metadata,
    release_podcast_lock,
    write_podcast_metadata,
)


class TestPodcastStore(unittest.TestCase):
    def _metadata(self, date_text, status="success"):
        return {
            "date": date_text,
            "title": "{} AI 音频日报".format(date_text),
            "audio_url": "/api/podcasts/{}/podcast.mp3".format(date_text),
            "duration_seconds": 397,
            "generated_at": "{}T02:34:12".format(date_text),
            "source_count": 7,
            "item_count": 48,
            "status": status,
            "error": "",
            "chapters": [],
        }

    def test_validates_podcast_date(self):
        self.assertTrue(is_valid_podcast_date("2026-07-19"))
        self.assertFalse(is_valid_podcast_date("2026-99-99"))
        self.assertFalse(is_valid_podcast_date("../../etc/passwd"))

    def test_success_metadata_updates_latest_and_history(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            write_podcast_metadata(self._metadata("2026-07-19"), output_dir=temp_dir)

            latest = load_latest_podcast_metadata(output_dir=temp_dir)
            history = list_podcast_history(
                days=7,
                output_dir=temp_dir,
                today=date(2026, 7, 20),
            )

            self.assertEqual(latest["date"], "2026-07-19")
            self.assertEqual(len(history), 1)
            self.assertTrue(has_successful_podcast("2026-07-19", output_dir=temp_dir))

    def test_history_returns_at_most_requested_days(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            for day in range(10, 17):
                write_podcast_metadata(self._metadata("2026-07-{:02d}".format(day)), output_dir=temp_dir)

            history = list_podcast_history(
                days=3,
                output_dir=temp_dir,
                today=date(2026, 7, 16),
            )

            self.assertEqual([item["date"] for item in history], [
                "2026-07-16",
                "2026-07-15",
                "2026-07-14",
            ])

    def test_failed_metadata_does_not_update_latest(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            write_podcast_metadata(self._metadata("2026-07-19", status="failed"), output_dir=temp_dir)

            self.assertIsNone(load_latest_podcast_metadata(output_dir=temp_dir))
            self.assertFalse(has_successful_podcast("2026-07-19", output_dir=temp_dir))

    def test_lock_prevents_duplicate_generation(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            now = datetime(2026, 7, 20, 2, 30, 0)

            self.assertTrue(acquire_podcast_lock("2026-07-19", output_dir=temp_dir, now=now))
            self.assertFalse(acquire_podcast_lock("2026-07-19", output_dir=temp_dir, now=now))

            release_podcast_lock("2026-07-19", output_dir=temp_dir)
            self.assertTrue(acquire_podcast_lock("2026-07-19", output_dir=temp_dir, now=now))

    def test_get_podcast_audio_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            audio_path = Path(temp_dir) / "podcasts" / "2026-07-19" / "podcast.mp3"
            audio_path.parent.mkdir(parents=True)
            audio_path.write_bytes(b"mp3")

            self.assertEqual(get_podcast_audio_file("2026-07-19", output_dir=temp_dir), audio_path)
            self.assertIsNone(get_podcast_audio_file("bad-date", output_dir=temp_dir))


if __name__ == "__main__":
    unittest.main()
